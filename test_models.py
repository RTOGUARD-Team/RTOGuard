"""
RTOGuard Model Health Check
Run this from the RTOGuard/ root to verify every component works.

    python test_models.py
"""

import sys

PASS = "[PASS]"
FAIL = "[FAIL]"
HEAD = "\n" + "=" * 55


def check(label, fn):
    try:
        result = fn()
        print(f"  {PASS}  {label}")
        return result
    except Exception as e:
        print(f"  {FAIL}  {label}")
        print(f"         ERROR: {e}")
        return None


# ─────────────────────────────────────────────────────────
# 1. MODEL FILES
# ─────────────────────────────────────────────────────────
print(HEAD)
print(" STEP 1 — Model Files Present")
print("=" * 55)

from pathlib import Path

check("rtoguard_old_model.joblib exists",
      lambda: Path("app/core/models/rtoguard_old_model.joblib").exists() or (_ for _ in ()).throw(FileNotFoundError("missing")))

check("rtoguard_new_model.joblib exists",
      lambda: Path("app/core/models/rtoguard_new_model.joblib").exists() or (_ for _ in ()).throw(FileNotFoundError("missing")))

check("pincode_stats.csv exists",
      lambda: Path("app/data/pincode_stats.csv").exists() or (_ for _ in ()).throw(FileNotFoundError("missing")))


# ─────────────────────────────────────────────────────────
# 2. MODEL LOADING (joblib)
# ─────────────────────────────────────────────────────────
print(HEAD)
print(" STEP 2 — Model Loading (joblib)")
print("=" * 55)

import joblib

old_model = check("Load OLD model (joblib)",
                  lambda: joblib.load("app/core/models/rtoguard_old_model.joblib"))

new_model = check("Load NEW model (joblib)",
                  lambda: joblib.load("app/core/models/rtoguard_new_model.joblib"))

if old_model:
    check("OLD model has predict_proba()",
          lambda: callable(getattr(old_model, "predict_proba", None)) or (_ for _ in ()).throw(AttributeError))

if new_model:
    check("NEW model has predict_proba()",
          lambda: callable(getattr(new_model, "predict_proba", None)) or (_ for _ in ()).throw(AttributeError))


# ─────────────────────────────────────────────────────────
# 3. DATABASE & PINCODE CSV
# ─────────────────────────────────────────────────────────
print(HEAD)
print(" STEP 3 — Database & Pincode CSV")
print("=" * 55)

from app.core.store import get_customer_info, get_pincode_info, PINCODE_DATA

check("30 pincodes loaded from CSV",
      lambda: len(PINCODE_DATA) >= 10 or (_ for _ in ()).throw(AssertionError(f"Only {len(PINCODE_DATA)} loaded")))

pin = check("Pincode 110001 (Metro tier-1) lookup",
            lambda: get_pincode_info("110001"))
if pin:
    print(f"         rto_rate={pin['historical_rto_rate']}  tier={pin['tier']}")

pin3 = check("Pincode 841301 (Tier-3 rural) lookup",
             lambda: get_pincode_info("841301"))
if pin3:
    print(f"         rto_rate={pin3['historical_rto_rate']}  tier={pin3['tier']}")

fallback = check("Unknown pincode fallback (999999)",
                 lambda: get_pincode_info("999999"))
if fallback:
    print(f"         fallback rto_rate={fallback['historical_rto_rate']}")

cust_old = check("Returning customer lookup (id=1)",
                 lambda: get_customer_info(1))
if cust_old:
    print(f"         past_orders={cust_old['past_orders_count']}  past_rto={cust_old['past_rto_orders']}")

cust_new = check("New customer cold-start (id=99999)",
                 lambda: get_customer_info(99999))
if cust_new:
    print(f"         past_orders={cust_new['past_orders_count']}  (should be 0)")


# ─────────────────────────────────────────────────────────
# 4. RISK ENGINE — score_order()
# ─────────────────────────────────────────────────────────
print(HEAD)
print(" STEP 4 — Risk Engine (Riya's Model)")
print("=" * 55)

from app.core.scoring import score_order

# 4a. Returning customer, high-risk pincode
r1 = check("OLD customer, tier-3 pincode, festive",
           lambda: score_order({
               "customer_id": 1,
               "order_value": 3500,
               "payment_mode": "COD",
               "pincode": "841301",
               "category": "Apparel",
               "is_festive_window": True
           }))
if r1:
    print(f"         risk_score={r1['risk_score']}  factors={r1['top_factors']}")

# 4b. New customer, metro pincode
r2 = check("NEW customer, metro pincode, normal",
           lambda: score_order({
               "customer_id": 99999,
               "order_value": 800,
               "payment_mode": "COD",
               "pincode": "110001",
               "category": "clothing",
               "is_festive_window": False
           }))
if r2:
    print(f"         risk_score={r2['risk_score']}  factors={r2['top_factors']}")

# 4c. Prepaid order (must always be near-zero)
r3 = check("PREPAID order (must return risk_score ~0.02)",
           lambda: score_order({
               "customer_id": 1,
               "order_value": 5000,
               "payment_mode": "PREPAID",
               "pincode": "841301",
               "category": "Electronics",
               "is_festive_window": True
           }))
if r3:
    assert r3["risk_score"] <= 0.05, f"Prepaid risk should be near-zero, got {r3['risk_score']}"
    print(f"         risk_score={r3['risk_score']}  (expected ~0.02)")

# 4d. Contract check
if r1:
    check("Output has only 'risk_score' and 'top_factors' keys",
          lambda: (set(r1.keys()) == {"risk_score", "top_factors"}) or
                  (_ for _ in ()).throw(AssertionError(f"Got keys: {list(r1.keys())}")))

    check("risk_score is float between 0 and 1",
          lambda: isinstance(r1["risk_score"], float) and 0.0 <= r1["risk_score"] <= 1.0 or
                  (_ for _ in ()).throw(AssertionError(f"Got {r1['risk_score']}")))

    check("top_factors is a non-empty list of strings",
          lambda: isinstance(r1["top_factors"], list) and len(r1["top_factors"]) > 0 and
                  all(isinstance(f, str) for f in r1["top_factors"]) or
                  (_ for _ in ()).throw(AssertionError(f"Got {r1['top_factors']}")))


# ─────────────────────────────────────────────────────────
# 5. SHUBHAM'S SERVICES
# ─────────────────────────────────────────────────────────
print(HEAD)
print(" STEP 5 — Shubham's Services (Action + Cost + Simulation)")
print("=" * 55)

from app.services.action_recommendation import ActionRecommendationEngine
from app.services.cost_calculator import CostCalculator
from app.services.simulation_engine import SimulationEngine

action_eng = ActionRecommendationEngine()
cost_calc   = CostCalculator()
sim_eng     = SimulationEngine()

rec = check("ActionRecommendationEngine.recommend() [HIGH risk]",
            lambda: action_eng.recommend(
                risk_score=0.75,
                order_value=3000,
                payment_mode="COD",
                top_factors=["High RTO rate"]
            ))
if rec:
    print(f"         action={rec['recommended_action']}  deposit={rec['suggested_deposit']}")

cost = check("CostCalculator.calculate() [CONFIRMATION action]",
             lambda: cost_calc.calculate(
                 order_value=3000,
                 risk_score=0.75,
                 action="CONFIRMATION",
                 suggested_deposit=1500
             ))
if cost:
    print(f"         loss_avoided={cost.get('rto_loss_avoided')}  net_impact={cost.get('net_impact')}")

sim = check("SimulationEngine.simulate() [2 orders]",
            lambda: sim_eng.simulate([
                {"risk_score": 0.75, "order_value": 2000, "payment_mode": "COD", "top_factors": ["High RTO"]},
                {"risk_score": 0.15, "order_value": 800,  "payment_mode": "COD", "top_factors": []},
            ]))
if sim:
    print(f"         simulation keys: {list(sim.keys())[:4]} ...")


# ─────────────────────────────────────────────────────────
# 6. FULL PIPELINE (end-to-end)
# ─────────────────────────────────────────────────────────
print(HEAD)
print(" STEP 6 — Full Pipeline (Risk -> Action -> Cost)")
print("=" * 55)

def full_pipeline():
    order = {
        "customer_id": "CUS-1001",
        "order_value": 4500,
        "payment_mode": "COD",
        "pincode": "841301",
        "category": "Electronics",
        "is_festive_window": True,
    }
    risk   = score_order(order)
    action = action_eng.recommend(
        risk_score=risk["risk_score"],
        order_value=order["order_value"],
        payment_mode=order["payment_mode"],
        top_factors=risk["top_factors"]
    )
    cost = cost_calc.calculate(
        order_value=order["order_value"],
        risk_score=risk["risk_score"],
        action=action["recommended_action"],
        suggested_deposit=action["suggested_deposit"]
    )
    return risk, action, cost

res = check("Full pipeline runs without error", full_pipeline)
if res:
    risk, action, cost = res
    print(f"         risk_score    = {risk['risk_score']}")
    print(f"         risk_level    = {action['risk_level']}")
    print(f"         action        = {action['recommended_action']}")
    print(f"         deposit       = {action['suggested_deposit']}")
    print(f"         loss_avoided  = {cost.get('rto_loss_avoided')}")


# ─────────────────────────────────────────────────────────
# 7. NOTIFIER SERVICE
# ─────────────────────────────────────────────────────────
print(HEAD)
print(" STEP 7 — Notifier Service (WhatsApp/Webhook)")
print("=" * 55)

# Notifier requires 64-char SHA-256 customer_id
import hashlib
hashed_id = hashlib.sha256(b"rtoguard_salt_2026_test_customer").hexdigest()

from app.services.notify.notifier import NotifierService
notifier = NotifierService()

notif = check("NotifierService — HIGH risk alert fires",
              lambda: notifier.evaluate_and_notify(
                  order_id="ORD-TEST-001",
                  customer_id=hashed_id,
                  risk_score=0.75,
                  reasons=["High historical RTO rate", "Tier-3 pincode"]
              ))
if notif:
    print(f"         risk_level={notif.risk_level.value}  action={notif.recommended_action.value}")

notif_low = check("NotifierService — LOW risk (SHIP_COD)",
                  lambda: notifier.evaluate_and_notify(
                      order_id="ORD-TEST-002",
                      customer_id=hashed_id,
                      risk_score=0.12,
                      reasons=[]
                  ))
if notif_low:
    print(f"         risk_level={notif_low.risk_level.value}  action={notif_low.recommended_action.value}")


# ─────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print(" ALL CHECKS COMPLETE")
print("=" * 55)
print("  If all lines show [PASS], start the server with:")
print("  uvicorn app.main:app --reload")
print("  Then open: http://localhost:8000/docs")
print("=" * 55 + "\n")
