"""
Notification & Operational Action Dispatcher Module for RTOGuard.

Evaluates checkout risk scores (0.0 to 1.0) and generates 3-Tier operational notifications:
- 0.0 - 0.3 Low Risk: Ship as normal COD (Zero friction)
- 0.3 - 0.6 Medium Risk: Require Partial Prepaid Deposit
- 0.6 - 1.0 High Risk: Route to Confirmation Call / Prepaid Only
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Callable, List, Optional
from pydantic import BaseModel, Field, field_validator


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class OperationalAction(str, Enum):
    SHIP_COD = "SHIP_COD"
    PARTIAL_PREPAID = "PARTIAL_PREPAID"
    CONFIRMATION_CALL = "CONFIRMATION_CALL"


class OrderNotificationPayload(BaseModel):
    """
    Notification payload dispatched when an order risk score is evaluated.
    """
    order_id: str
    customer_id: str
    risk_score: float = Field(..., ge=0.0, le=1.0)
    risk_level: RiskLevel
    recommended_action: OperationalAction
    reasons: List[str]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("customer_id")
    @classmethod
    def validate_customer_id(cls, v: str) -> str:
        if len(v) != 64:
            raise ValueError("customer_id in notification must be a 64-character SHA-256 string.")
        return v.lower()


class NotifierService:
    """
    Notification Service to route high risk alerts to operational channels.
    """

    def __init__(self, high_risk_threshold: float = 0.60, medium_risk_threshold: float = 0.30):
        self.high_risk_threshold = high_risk_threshold
        self.medium_risk_threshold = medium_risk_threshold
        self.handlers: List[Callable[[OrderNotificationPayload], None]] = [self._default_log_handler]

    def register_handler(self, handler: Callable[[OrderNotificationPayload], None]) -> None:
        """Register custom notification alert handler (e.g. Webhook, Slack, Email)."""
        self.handlers.append(handler)

    def evaluate_and_notify(
        self,
        order_id: str,
        customer_id: str,
        risk_score: float,
        reasons: Optional[List[str]] = None
    ) -> OrderNotificationPayload:
        """
        Evaluates risk score, classifies 3-tier operational action, builds notification payload,
        and triggers all registered handlers.
        """
        reasons_list = reasons or []

        if risk_score >= self.high_risk_threshold:
            risk_lvl = RiskLevel.HIGH
            action = OperationalAction.CONFIRMATION_CALL
        elif risk_score >= self.medium_risk_threshold:
            risk_lvl = RiskLevel.MEDIUM
            action = OperationalAction.PARTIAL_PREPAID
        else:
            risk_lvl = RiskLevel.LOW
            action = OperationalAction.SHIP_COD

        payload = OrderNotificationPayload(
            order_id=order_id,
            customer_id=customer_id,
            risk_score=round(risk_score, 4),
            risk_level=risk_lvl,
            recommended_action=action,
            reasons=reasons_list,
            timestamp=datetime.now(timezone.utc)
        )

        # Trigger notification handlers
        for h in self.handlers:
            try:
                h(payload)
            except Exception as e:
                print(f"Error executing notification handler: {e}")

        return payload

    def _default_log_handler(self, payload: OrderNotificationPayload) -> None:
        """Default logging handler for risk notifications."""
        print(f"🚨 [RTOGuard Alert] Order: {payload.order_id} | Risk: {payload.risk_score} ({payload.risk_level.value}) | Action: {payload.recommended_action.value} | Reasons: {', '.join(payload.reasons)}")
