import re
from pydantic import BaseModel, Field, field_validator


# =====================================================
# RECOMMENDATION REQUEST
# =====================================================

class RecommendationRequest(BaseModel):

    risk_score: float = Field(
        ...,
        ge=0.0,
        le=1.0
    )

    order_value: float = Field(
        ...,
        gt=0
    )

    payment_mode: str = "COD"

    top_factors: list[str] = Field(
        default_factory=list
    )


# =====================================================
# COST REQUEST
# =====================================================

class CostRequest(BaseModel):

    risk_score: float = Field(
        ...,
        ge=0.0,
        le=1.0
    )

    order_value: float = Field(
        ...,
        gt=0
    )

    payment_mode: str = "COD"

    top_factors: list[str] = Field(
        default_factory=list
    )


# =====================================================
# SIMULATION ORDER
# =====================================================

class SimulationOrder(BaseModel):

    order_id: str

    order_value: float = Field(
        ...,
        gt=0
    )

    payment_mode: str = "COD"

    risk_score: float = Field(
        ...,
        ge=0.0,
        le=1.0
    )

    top_factors: list[str] = Field(
        default_factory=list
    )


# =====================================================
# SIMULATION REQUEST
# =====================================================

class SimulationRequest(BaseModel):

    orders: list[SimulationOrder] | None = None

    order_count: int = Field(
        default=1000,
        ge=1,
        le=100000
    )

    seed: int = 42


# =====================================================
# RAW ORDER (no risk_score — ML will generate it)
# =====================================================

class RawOrder(BaseModel):

    order_id: str = ""

    customer_id: str = Field(
        ...,
        description="Customer identifier — numeric (1, 101) or string ('CUS-1001')."
    )

    order_value: float = Field(
        ...,
        gt=0
    )

    payment_mode: str = "COD"

    pincode: str = "110001"

    category: str = "general"

    is_festive_window: bool = False

    @field_validator("customer_id", mode="before")
    @classmethod
    def coerce_customer_id(cls, v) -> str:
        """Accept int or string customer IDs — convert all to string for storage."""
        return str(v).strip()


# =====================================================
# RAW SIMULATION REQUEST
# =====================================================

class RawSimulationRequest(BaseModel):

    orders: list[RawOrder]


# =====================================================
# ORDER OUTCOME REQUEST (Feedback Loop)
# =====================================================

class OrderOutcomeRequest(BaseModel):
    order_id: str
    status: str = Field(
        ...,
        description="Delivery outcome: 'DELIVERED' or 'RTO' / 'RETURNED'"
    )
    notes: str = ""


# =====================================================
# SCORE FEATURES REQUEST (from ScoreOrder.tsx)
# =====================================================

class ScoreFeaturesRequest(BaseModel):
    customer_type: str = "NEW"
    past_orders: int = 0
    past_rtos: int = 0
    order_value: float = Field(..., gt=0)
    payment_mode: str = "COD"
    pincode: str = "110001"
    festive_window: bool = False


# =====================================================
# OPERATOR DECISION REQUEST (from DecisionPanel.tsx)
# =====================================================

class OperatorDecisionRequest(BaseModel):
    operator_action: str = Field(..., description="'ACCEPT' or 'OVERRIDE'")
    override_action: str | None = None
    override_reason: str | None = None
    override_note: str | None = None
