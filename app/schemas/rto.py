from pydantic import BaseModel, Field


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