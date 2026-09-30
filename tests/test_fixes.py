"""
Automated Verification Suite for RTOGuard Audit Fixes.
"""
import pytest
import re
from app.db import customers_collection, orders_collection, predictions_collection, strip_forbidden_fields
from app.core.scoring import score_order
from app.rto_schemas import ScoreFeaturesRequest, OperatorDecisionRequest, RawOrder
from pydantic import ValidationError

def test_fix1_no_pii_in_mongodb():
    """Verify that zero documents in MongoDB contain forbidden PII fields."""
    all_custs = list(customers_collection.find())
    assert len(all_custs) > 0, "No customers in MongoDB"
    forbidden = {"name", "phone", "email", "address"}
    for doc in all_custs:
        for k in doc.keys():
            assert k.lower() not in forbidden, f"Found forbidden PII key: {k} in customer {doc.get('customer_id')}"

def test_fix1_strip_forbidden_fields_guard():
    """Verify that strip_forbidden_fields strips top-level and $set PII keys."""
    dirty_doc = {
        "customer_id": "abc",
        "name": "Jane Doe",
        "phone": "+919999999999",
        "email": "test@example.com",
        "past_orders_count": 5
    }
    cleaned = strip_forbidden_fields(dirty_doc)
    assert "name" not in cleaned
    assert "phone" not in cleaned
    assert "email" not in cleaned
    assert cleaned["past_orders_count"] == 5

    dirty_update = {"$set": {"name": "Hacker", "status": "ACTIVE"}}
    cleaned_update = strip_forbidden_fields(dirty_update)
    assert "name" not in cleaned_update["$set"]
    assert cleaned_update["$set"]["status"] == "ACTIVE"

def test_fix2_all_customer_ids_are_sha256():
    """Verify that 100% of customer IDs in MongoDB match 64-hex SHA-256."""
    all_custs = list(customers_collection.find())
    assert len(all_custs) == 300, f"Expected 300 customers from customers.csv, got {len(all_custs)}"
    sha256_pattern = re.compile(r"^[a-f0-9]{64}$")
    for doc in all_custs:
        cid = str(doc.get("customer_id", ""))
        assert sha256_pattern.match(cid), f"Non-SHA-256 customer_id found: {cid}"

def test_fix3_returning_customer_inline_scoring():
    """Verify that supplying inline customer history runs OLD model without DB lookup."""
    test_order = {
        "order_id": "TEST_ORD_001",
        "customer_id": "UNKNOWN_ID_NOT_IN_DB_999",
        "order_value": 3500.0,
        "payment_mode": "COD",
        "pincode": "400001",
        "is_festive_window": False,
        "past_orders_count": 20,
        "past_rto_orders": 14,
        "past_rto_rate": 0.7,
        "customer_type": "RETURNING"
    }
    result = score_order(test_order)
    assert result["risk_score"] > 0.40, f"Expected elevated risk score for 70% RTO history, got {result['risk_score']}"
    assert "First-time customer (zero prior order history)" not in result["top_factors"]
    assert any("High historical return rate" in f for f in result["top_factors"])

def test_fix4_pincode_validation_rejection():
    """Verify that pincodes not matching ^[1-9][0-9]{5}$ raise ValidationError."""
    with pytest.raises(ValidationError):
        ScoreFeaturesRequest(
            customer_type="NEW",
            past_orders=0,
            past_rtos=0,
            order_value=1500,
            payment_mode="COD",
            pincode="123"
        )

    with pytest.raises(ValidationError):
        RawOrder(
            customer_id="abc",
            order_value=1500,
            payment_mode="COD",
            pincode="012345"  # starts with 0
        )

def test_fix4_operator_decision_literal_rejection():
    """Verify that operator_action not in ['ACCEPT', 'OVERRIDE'] raises ValidationError."""
    with pytest.raises(ValidationError):
        OperatorDecisionRequest(operator_action="FAKE")

    # Valid actions should pass
    req_accept = OperatorDecisionRequest(operator_action="ACCEPT")
    req_override = OperatorDecisionRequest(operator_action="OVERRIDE", override_action="SHIP_NORMAL", override_reason="VIP_CUSTOMER")
    assert req_accept.operator_action == "ACCEPT"
    assert req_override.operator_action == "OVERRIDE"


def test_simulation_ground_truth_economics():
    """Verify simulation Pass A and Pass B evaluate against ground truth labels."""
    from app.services.simulation_engine import SimulationEngine

    # Order 1: predicted low risk (0.05), but actual ground truth is RTO
    # Order 2: predicted high risk (0.85), but actual ground truth is DELIVERED
    orders = [
        {
            "order_id": "ORD_TEST_1",
            "order_value": 2000.0,
            "payment_mode": "COD",
            "risk_score": 0.05,
            "top_factors": [],
            "outcome": "RTO"
        },
        {
            "order_id": "ORD_TEST_2",
            "order_value": 3000.0,
            "payment_mode": "COD",
            "risk_score": 0.85,
            "top_factors": [],
            "outcome": "DELIVERED"
        }
    ]

    engine = SimulationEngine()
    result = engine.simulate(orders)

    # Pass A baseline MUST equal 1 RTO order * 750 = 750.0
    # If the old self-scoring bug existed, baseline loss would be (0.05 + 0.85) * 750 = 675.0
    assert result["baseline"]["expected_rto_orders"] == 1.0
    assert result["baseline"]["expected_rto_loss"] == 750.0
    assert result["baseline"]["expected_rto_rate"] == 0.50

    # Pass B:
    # ORD_TEST_1 (risk 0.05 -> SHIP_NORMAL): actual RTO, so unmitigated RTO loss = 750.0
    # ORD_TEST_2 (risk 0.85 -> PARTIAL_DEPOSIT): actual DELIVERED, so conversion friction loss applied!
    assert result["impact"]["conversion_loss_impact"] > 0.0


def test_evaluation_report_and_endpoint():
    """Verify evaluation report exists with real metrics and endpoint serves it."""
    from app.api.rto_routes import get_model_evaluation
    import json
    from pathlib import Path

    report_path = Path("app/data/evaluation_report.json")
    assert report_path.exists(), "evaluation_report.json does not exist"

    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "synthetic_outcomes" in data
    assert "evaluation_dataset" in data
    assert data["evaluation_dataset"]["roc_auc"] > 0.65
    assert data["synthetic_outcomes"]["n"] == 300

    resp = get_model_evaluation()
    assert resp["evaluation_dataset"]["roc_auc"] == data["evaluation_dataset"]["roc_auc"]

