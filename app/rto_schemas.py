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
        description="SHA-256 hashed customer identifier (64 hex characters)."
    )

    order_value: float = Field(
        ...,
        gt=0
    )

    payment_mode: str = "COD"

    pincode: str = "110001"

    category: str = "general"

    is_festive_window: bool = False

    @field_validator("customer_id")
    @classmethod
    def validate_customer_id(cls, v: str) -> str:
        v_clean = v.strip().lower()
        if not re.match(r"^[a-f0-9]{64}$", v_clean):
            raise ValueError("customer_id must be a 64-character SHA-256 hex string.")
        return v_clean


# =====================================================
# RAW SIMULATION REQUEST
# =====================================================

class RawSimulationRequest(BaseModel):

    orders: list[RawOrder]