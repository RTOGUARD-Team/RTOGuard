from fastapi import APIRouter

from app.schemas import DashboardSummary, FestiveBreakdown

router = APIRouter(prefix="/api")


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary():
    # Hardcoded demo numbers for now
    return DashboardSummary(
        overall_rto_rate=0.26,
        total_at_risk_value=125000.0,
        festive_breakdown=FestiveBreakdown(
            pre_festive_rto_rate=0.22,
            festive_rto_rate=0.31,
        ),
    )