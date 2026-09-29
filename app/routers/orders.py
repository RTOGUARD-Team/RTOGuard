from fastapi import APIRouter, Query
from app.schemas import OrderRequest, HighRiskOrder
from app.core.scoring import score_order
from app.core.actions import recommend_action

router = APIRouter(prefix="/api")

# Demo data until orders come from db
MOCK_ORDERS = [
    {"order_id": 101, "customer_id": 2, "order_value": 5000, "payment_mode": "cod",
     "pincode": "800001", "category": "electronics", "is_festive_window": True},
    {"order_id": 102, "customer_id": 1, "order_value": 1200, "payment_mode": "cod",
     "pincode": "110001", "category": "apparel", "is_festive_window": False},
]


@router.get("/orders/high-risk", response_model=list[HighRiskOrder])
def high_risk(threshold: float = Query(0.6, ge=0.0, le=1.0)):
    results = []
    for o in MOCK_ORDERS:
        req = OrderRequest(**{k: v for k, v in o.items() if k != "order_id"})
        score_result = score_order(req)
        risk = score_result["risk_score"]
        if risk >= threshold:
            action, reason = recommend_action(risk)
            results.append(HighRiskOrder(
                order_id=o["order_id"], risk_score=risk, action=action, reason=reason
            ))
    return results