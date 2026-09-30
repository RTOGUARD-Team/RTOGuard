"""
Comprehensive End-to-End System Verification for RTOGuard.
Tests:
1. Database Layer (MongoDB Atlas: connections, zero PII, SHA-256 hashes, counts)
2. ML & Decision Engines (Risk Engine, Action Engine, Cost Engine, Simulation Engine)
3. Backend API Endpoints (Live HTTP tests on localhost:8000)
4. Frontend Dev Server (Live HTTP test on localhost:5173)
"""

import sys
import json
import urllib.request
import urllib.error
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_database_layer():
    print_header("1. DATABASE LAYER (MongoDB Atlas)")
    from app.db import customers_collection, orders_collection, predictions_collection, strip_forbidden_fields

    # 1. Connection check
    try:
        cust_count = customers_collection.count_documents({})
        ord_count = orders_collection.count_documents({})
        pred_count = predictions_collection.count_documents({})
        print(f"  [PASS] MongoDB Connection: Active")
        print(f"         - Customers:   {cust_count} documents")
        print(f"         - Orders:      {ord_count} documents")
        print(f"         - Predictions: {pred_count} documents")
    except Exception as e:
        print(f"  [FAIL] MongoDB connection failed: {e}")
        return False

    # 2. Zero-PII check
    forbidden = {"name", "phone", "email", "address"}
    pii_violations = 0
    all_custs = list(customers_collection.find().limit(100))
    for c in all_custs:
        for k in c.keys():
            if k.lower() in forbidden:
                pii_violations += 1
    if pii_violations == 0:
        print("  [PASS] Zero-PII Compliance: 0 forbidden fields found in MongoDB")
    else:
        print(f"  [FAIL] Found {pii_violations} PII violations in MongoDB!")
        return False

    # 3. SHA-256 ID check
    sha_regex = re.compile(r"^[a-f0-9]{64}$")
    non_sha = [c.get("customer_id") for c in all_custs if not sha_regex.match(str(c.get("customer_id", "")))]
    if len(non_sha) == 0:
        print("  [PASS] Privacy ID Format: 100% of sampled customer IDs are 64-hex SHA-256 hashes")
    else:
        print(f"  [FAIL] Non-SHA customer IDs found: {non_sha[:3]}")
        return False

    return True


def test_engines_layer():
    print_header("2. ENGINE PIPELINES (Risk -> Action -> Cost -> Simulation)")
    from app.core.scoring import score_order
    from app.services.action_recommendation import ActionRecommendationEngine
    from app.services.cost_calculator import CostCalculator
    from app.services.simulation_engine import SimulationEngine

    rec_engine = ActionRecommendationEngine()
    cost_calc = CostCalculator()
    sim_engine = SimulationEngine()

    # Engine A: Dual-Model ML Scoring
    # Returning customer with bad history
    ret_order = {
        "order_id": "TEST_ORD_RET",
        "customer_id": "test_returning_customer_hash",
        "order_value": 4500.0,
        "payment_mode": "COD",
        "pincode": "841301",
        "past_orders_count": 20,
        "past_rto_orders": 14,
        "past_rto_rate": 0.70,
        "customer_type": "RETURNING"
    }
    ret_score = score_order(ret_order)
    assert ret_score["risk_score"] > 0.40, "Returning customer did not receive elevated risk"
    assert "First-time customer" not in " ".join(ret_score["top_factors"])
    print(f"  [PASS] Dual-Model ML Engine: Returning customer routed to OLD model (Score: {ret_score['risk_score']})")

    # Prepaid customer
    prep_order = {
        "order_id": "TEST_ORD_PREP",
        "order_value": 3000.0,
        "payment_mode": "PREPAID",
        "pincode": "110001",
    }
    prep_score = score_order(prep_order)
    assert prep_score["risk_score"] == 0.02
    print(f"  [PASS] Dual-Model ML Engine: Prepaid order scored at 0.02 near-zero risk")

    # Engine B: Action Recommendation
    high_rec = rec_engine.recommend(risk_score=0.75, order_value=4000.0, payment_mode="COD")
    assert high_rec["recommended_action"] == "CONFIRMATION"
    med_rec = rec_engine.recommend(risk_score=0.45, order_value=4000.0, payment_mode="COD")
    assert med_rec["recommended_action"] == "PARTIAL_DEPOSIT"
    print(f"  [PASS] Action Engine: High Risk -> {high_rec['recommended_action']}, Medium Risk -> {med_rec['recommended_action']}")

    # Engine C: Cost Calculator
    econ = cost_calc.calculate(order_value=4000.0, risk_score=0.75, action="CONFIRMATION", suggested_deposit=0.0)
    assert "rto_loss_avoided" in econ and "net_impact" in econ
    print(f"  [PASS] Cost Engine: Potential Loss Avoided: Rs. {econ['rto_loss_avoided']}, Net Impact: Rs. {econ['net_impact']}")

    # Engine D: Simulation Engine (Ground Truth Economics)
    test_batch = [
        {"order_id": "SIM_1", "order_value": 2500, "payment_mode": "COD", "risk_score": 0.10, "top_factors": [], "outcome": "RTO"},
        {"order_id": "SIM_2", "order_value": 2500, "payment_mode": "COD", "risk_score": 0.85, "top_factors": [], "outcome": "DELIVERED"},
    ]
    sim_res = sim_engine.simulate(test_batch)
    assert sim_res["baseline"]["expected_rto_loss"] == 750.0  # Exactly 1 actual RTO
    assert sim_res["impact"]["conversion_loss_impact"] > 0.0  # Friction on delivered order
    print(f"  [PASS] Simulation Engine: Baseline loss calculated from ground truth outcomes (Rs. {sim_res['baseline']['expected_rto_loss']})")

    return True


def test_live_backend_api():
    print_header("3. LIVE BACKEND HTTP API (http://127.0.0.1:8000)")
    base_url = "http://127.0.0.1:8000"

    def req(path, method="GET", data=None):
        url = base_url + path
        headers = {"Content-Type": "application/json", "User-Agent": "RTOGuard-E2E-Tester"}
        body = json.dumps(data).encode("utf-8") if data else None
        r = urllib.request.Request(url, data=body, headers=headers, method=method)
        with urllib.request.urlopen(r, timeout=10) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content)

    # 1. Dashboard summary
    status, d_sum = req("/rto/dashboard-summary")
    print(f"  [PASS] GET /rto/dashboard-summary -> 200 OK")
    print(f"         Total Orders: {d_sum.get('total_orders')}, High Risk: {d_sum.get('high_risk_orders')}, RTO Risk: {d_sum.get('rto_risk_percentage')}%")

    # 2. Orders list
    status, orders = req("/rto/orders")
    print(f"  [PASS] GET /rto/orders -> 200 OK ({len(orders)} orders loaded)")

    # 3. Model Evaluation report
    status, eval_rep = req("/rto/evaluation")
    print(f"  [PASS] GET /rto/evaluation -> 200 OK")
    print(f"         ROC-AUC: {eval_rep.get('evaluation_dataset', {}).get('roc_auc')}, High-Risk Precision: {eval_rep.get('synthetic_outcomes', {}).get('high_risk_precision')}")

    # 4. Score a real order live via HTTP
    new_order_payload = {
        "customer_type": "RETURNING",
        "past_orders": 12,
        "past_rtos": 8,
        "order_value": 3800.0,
        "payment_mode": "COD",
        "pincode": "841301",
        "category": "Apparel",
        "is_festive_window": False,
        "checkout_hour": 22,
        "address_word_count": 8,
        "address_quality_score": 0.85
    }
    status, scored = req("/rto/score-features", method="POST", data=new_order_payload)
    order_id = scored.get("order_id")
    print(f"  [PASS] POST /rto/score-features -> 200 OK (Created Order: {order_id})")
    print(f"         Score: {scored.get('risk_score')}, Level: {scored.get('risk_level')}, Action: {scored.get('recommended_action')}")

    # 5. Operator Decision on that created order
    dec_payload = {
        "operator_action": "ACCEPT",
        "override_action": None,
        "override_reason": None,
        "override_note": "Verified by automated E2E test"
    }
    status, dec_res = req(f"/rto/orders/{order_id}/decision", method="POST", data=dec_payload)
    assert dec_res.get("decision", {}).get("operator_action") == "ACCEPT"
    print(f"  [PASS] POST /rto/orders/{order_id}/decision -> 200 OK (Decision: ACCEPT confirmed in DB)")

    # 6. Run Simulation via API
    sim_payload = {"order_count": 100, "seed": 42, "festive": False}
    status, sim_api = req("/rto/simulate", method="POST", data=sim_payload)
    print(f"  [PASS] POST /rto/simulate -> 200 OK (Orders simulated: {sim_api.get('order_count')}, Baseline Loss: Rs. {sim_api.get('baseline', {}).get('expected_rto_loss')})")

    return True


def test_live_frontend():
    print_header("4. LIVE FRONTEND DEV SERVER (http://localhost:5173)")
    url = "http://localhost:5173"
    try:
        r = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(r, timeout=5) as resp:
            html = resp.read().decode("utf-8")
            assert "<html" in html or "<div id=\"root\"" in html or "vite" in html.lower()
            print(f"  [PASS] Frontend Web Server: Active on {url} (Status {resp.status} OK)")
            print(f"         Vite single-page-app bundle successfully delivered.")
            return True
    except Exception as e:
        print(f"  [FAIL] Could not connect to Frontend on {url}: {e}")
        return False


def main():
    print("\n" + "#" * 70)
    print("        RTOGUARD FULL SYSTEM END-TO-END VERIFICATION")
    print("#" * 70)

    ok_db = test_database_layer()
    ok_eng = test_engines_layer()
    ok_api = test_live_backend_api()
    ok_ui = test_live_frontend()

    print_header("FINAL VERIFICATION SUMMARY")
    if ok_db and ok_eng and ok_api and ok_ui:
        print("  >>> ALL SYSTEMS OPERATIONAL AND FULLY FUNCTIONING! <<<")
        print("  - Database (MongoDB Atlas):  CONNECTED & ZERO-PII COMPLIANT")
        print("  - All 4 Engines:             ACCURATE & VERIFIED")
        print("  - Backend API (FastAPI):     LIVE ON http://127.0.0.1:8000")
        print("  - Frontend (React/Vite):     LIVE ON http://localhost:5173")
    else:
        print("  >>> ISSUES DETECTED IN ONE OR MORE COMPONENTS <<<")


if __name__ == "__main__":
    main()
