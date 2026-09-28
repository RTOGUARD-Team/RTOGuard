from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api")

class DashboardSummary(BaseModel):
    overall_rto_rate: float
    total_at_risk_value: float
    festive_breakdown: dict

@router.get("/dashboard/summary", response_model=DashboardSummary)
def get_dashboard_summary():
    # Return mock data representing current live metrics for dashboard
    return DashboardSummary(
        overall_rto_rate=0.26,
        total_at_risk_value=125000.0,
        festive_breakdown={
            "pre_festive_rto_rate": 0.22,
            "festive_rto_rate": 0.31
        }
    )
