from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List
from app.core.ml import is_model_loaded, predict_rto_probability

router = APIRouter(prefix="/api")


class OrderRequest(BaseModel):
    customer_id: int
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


# Mock databases for the hackathon demo
mock_customers = {
    1: {"past_orders_count": 5, "past_rto_count": 1, "past_cod_orders": 4, "avg_order_value": 1500.0},
    2: {"past_orders_count": 0, "past_rto_count": 0, "past_cod_orders": 0, "avg_order_value": 0.0},
}

mock_pincodes = {
    "110001": {"historical_rto_rate": 0.15, "tier": "metro"},
    "800001": {"historical_rto_rate": 0.35, "tier": "tier2"},
}


def get_pincode_info(pincode: str):
    return mock_pincodes.get(pincode, {"historical_rto_rate": 0.20, "tier": "tier3"})


def get_customer_info(customer_id: int):
    return mock_customers.get(
        customer_id,
        {"past_orders_count": 0, "past_rto_count": 0, "past_cod_orders": 0, "avg_order_value": 1000.0},
    )


def compute_risk_score(customer_info, order_req: OrderRequest, pincode_info):
    if order_req.payment_mode.lower() == "prepaid":
        return 0.02  # Prepaid is structurally near-zero risk

    past_cod_orders = max(customer_info["past_cod_orders"], 1)
    history_score = customer_info["past_rto_count"] / past_cod_orders
    new_cust_weight = 0.25 if customer_info["past_orders_count"] == 0 else 0.0
    pincode_weight = pincode_info["historical_rto_rate"]

    avg_ov = customer_info["avg_order_value"] if customer_info["avg_order_value"] > 0 else order_req.order_value
    value_ratio = min(order_req.order_value / avg_ov, 3.0) / 3.0
    festive_weight = 0.08 if order_req.is_festive_window else 0.0

    if is_model_loaded():
        # Use the trained ML model (logic lives in app/core/ml.py)
        return predict_rto_probability([
            history_score,
            new_cust_weight,
            pincode_weight,
            value_ratio,
            festive_weight,
        ])
    else:
        # Fallback to MVP heuristic if model isn't trained yet
        raw = (0.35 * history_score +
               0.20 * new_cust_weight +
               0.25 * pincode_weight +
               0.12 * value_ratio +
               0.08 * festive_weight)
        return max(0.0, min(raw, 1.0))


def recommend_action(risk_score: float):
    if risk_score < 0.3:
        return "ship", "Low predicted return risk"
    elif risk_score < 0.6:
        return "partial_deposit", "Moderate risk — reduce exposure"
    else:
        return "confirm_call", "High risk — verify before shipping"


@router.post("/score-order", response_model=ScoreResponse)
def score_order(req: OrderRequest):
    cust_info = get_customer_info(req.customer_id)
    pin_info = get_pincode_info(req.pincode)

    score = compute_risk_score(cust_info, req, pin_info)
    action, reason = recommend_action(score)

    return ScoreResponse(risk_score=score, action=action, reason=reason)


@router.get("/orders/high-risk", response_model=List[HighRiskOrder])
def get_high_risk_orders(threshold: float = Query(0.6)):
    # Mocking some high risk orders for the GET endpoint
    orders = [
        {"order_id": 101, "customer_id": 2, "order_value": 5000, "payment_mode": "cod", "pincode": "800001", "category": "electronics", "is_festive_window": True},
        {"order_id": 102, "customer_id": 1, "order_value": 1200, "payment_mode": "cod", "pincode": "110001", "category": "apparel", "is_festive_window": False},
    ]

    results = []
    for o in orders:
        req = OrderRequest(
            customer_id=o["customer_id"],
            order_value=o["order_value"],
            payment_mode=o["payment_mode"],
            pincode=o["pincode"],
            category=o["category"],
            is_festive_window=o["is_festive_window"],
        )
        cust_info = get_customer_info(req.customer_id)
        pin_info = get_pincode_info(req.pincode)
        score = compute_risk_score(cust_info, req, pin_info)

        if score >= threshold:
            action, reason = recommend_action(score)
            results.append(HighRiskOrder(
                order_id=o["order_id"],
                risk_score=score,
                action=action,
                reason=reason,
            ))

    return results