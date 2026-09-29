"""
Notifier Service — ported from rtoguard-data/src/notify/notifier.py

Evaluates risk scores and dispatches 3-tier operational alerts:
- LOW  (0.0–0.30): Ship as normal COD — zero friction
- MEDIUM (0.30–0.60): Require partial prepaid deposit
- HIGH  (0.60–1.0): Route to confirmation call / full prepaid

Used in Step 10 of the pipeline — WhatsApp/webhook alert for MEDIUM and HIGH orders.
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
    Sent to WhatsApp / webhook / email for MEDIUM and HIGH risk orders.
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
    Risk-based notification dispatcher.
    Classifies risk tier, builds alert payload, and triggers all registered handlers.
    Register custom handlers (WhatsApp, webhook, Slack, email) via register_handler().
    """

    def __init__(self, high_risk_threshold: float = 0.60, medium_risk_threshold: float = 0.30):
        self.high_risk_threshold = high_risk_threshold
        self.medium_risk_threshold = medium_risk_threshold
        self.handlers: List[Callable[[OrderNotificationPayload], None]] = [self._default_log_handler]

    def register_handler(self, handler: Callable[[OrderNotificationPayload], None]) -> None:
        """Register a custom notification alert handler (e.g. WhatsApp webhook, Slack, Email)."""
        self.handlers.append(handler)

    def evaluate_and_notify(
        self,
        order_id: str,
        customer_id: str,
        risk_score: float,
        reasons: Optional[List[str]] = None
    ) -> OrderNotificationPayload:
        """
        Classifies risk tier, builds the alert payload, and fires all handlers.
        Returns the full OrderNotificationPayload.
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

        for handler in self.handlers:
            try:
                handler(payload)
            except Exception as e:
                print(f"Error executing notification handler: {e}")

        return payload

    def _default_log_handler(self, payload: OrderNotificationPayload) -> None:
        """Default console logger — replace with WhatsApp webhook in production."""
        alert = (
            f"[RTOGuard Alert] "
            f"Order: {payload.order_id} | "
            f"Risk: {payload.risk_score} ({payload.risk_level.value}) | "
            f"Action: {payload.recommended_action.value} | "
            f"Reasons: {', '.join(payload.reasons)}"
        )
        print(alert)
