from fastapi import APIRouter, Query
from pydantic import BaseModel
import random
from .orders import compute_risk_score, recommend_action, OrderRequest

router = APIRouter(prefix="/api")

class SimulationResponse(BaseModel):
    before_total: float
    after_total: float
    improvement_pct: float
    savings_per_1000: float

TOTAL_COST_PER_RTO = 900.0  # LOGISTICS_COST (225) + ACQUISITION_COST (675)

def expected_cost(risk_score: float, action_taken: str):
    base_exposure = risk_score * TOTAL_COST_PER_RTO
    mitigation_factor = {
        "ship": 1.0,
        "partial_deposit": 0.55,
        "confirm_call": 0.30
    }.get(action_taken, 1.0)
    return base_exposure * mitigation_factor

@router.get("/simulate", response_model=SimulationResponse)
def run_simulation(window: str = Query("festive")):
    random.seed(42) # fixed seed for demo reliability
    
    orders = []
    for i in range(1000):
        is_festive = window == "festive"
        # Create a varied synthetic distribution for demo
        new_cust = random.random() < 0.3
        past_rto = random.choice([0, 0, 1, 2]) if not new_cust else 0
        past_cod = random.randint(1, 10) if not new_cust else 0
        payment = "prepaid" if random.random() < 0.2 else "cod"
        
        cust_info = {
            "past_orders_count": 0 if new_cust else past_cod + 2,
            "past_rto_count": past_rto,
            "past_cod_orders": past_cod,
            "avg_order_value": random.uniform(500, 2000)
        }
        
        pin_tier = random.choice(["metro", "tier2", "tier3"])
        pin_info = {
            "historical_rto_rate": {"metro": 0.1, "tier2": 0.2, "tier3": 0.35}[pin_tier],
            "tier": pin_tier
        }
        
        order_req = OrderRequest(
            customer_id=i,
            order_value=random.uniform(300, 3000),
            payment_mode=payment,
            pincode="000000",
            category="apparel",
            is_festive_window=is_festive
        )
        
        orders.append((cust_info, order_req, pin_info))
        
    before_total = 0.0
    after_total = 0.0
    
    for cust_info, order_req, pin_info in orders:
        score = compute_risk_score(cust_info, order_req, pin_info)
        action, _ = recommend_action(score)
        
        before_total += score * TOTAL_COST_PER_RTO
        after_total += expected_cost(score, action)
        
    improvement_pct = ((before_total - after_total) / before_total * 100) if before_total > 0 else 0
    savings_per_1000 = (before_total - after_total) / len(orders) * 1000
    
    return SimulationResponse(
        before_total=before_total,
        after_total=after_total,
        improvement_pct=improvement_pct,
        savings_per_1000=savings_per_1000
    )
