from pydantic import BaseModel


class OrderRequest(BaseModel):
    customer_id: str      # ← SHA-256 hash, 64 hex characters
    order_value: float
    payment_mode: str
    pincode: str
    category: str
    is_festive_window: bool


class ScoreResponse(BaseModel):
    risk_score: float
    action: str
    reason: str


class HighRiskOrder(BaseModel):
    order_id: int
    risk_score: float
    action: str
    reason: str


class SimulationResponse(BaseModel):
    before_total: float
    after_total: float
    improvement_pct: float
    savings_per_1000: float


class FestiveBreakdown(BaseModel):
    pre_festive_rto_rate: float
    festive_rto_rate: float


class DashboardSummary(BaseModel):
    overall_rto_rate: float
    total_at_risk_value: float
    festive_breakdown: FestiveBreakdown