"""
Unit tests for Notifier Service & 3-Tier action classification.
"""

from src.notify import NotifierService, OperationalAction, RiskLevel

VALID_HASHED_ID = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_notifier_high_risk():
    notifier = NotifierService()
    payload = notifier.evaluate_and_notify(
        order_id="ord_high_1",
        customer_id=VALID_HASHED_ID,
        risk_score=0.85,
        reasons=["High risk Tier 3 pincode", "Incomplete address"]
    )
    assert payload.risk_level == RiskLevel.HIGH
    assert payload.recommended_action == OperationalAction.CONFIRMATION_CALL


def test_notifier_medium_risk():
    notifier = NotifierService()
    payload = notifier.evaluate_and_notify(
        order_id="ord_med_1",
        customer_id=VALID_HASHED_ID,
        risk_score=0.45,
        reasons=["Cart size anomaly"]
    )
    assert payload.risk_level == RiskLevel.MEDIUM
    assert payload.recommended_action == OperationalAction.PARTIAL_PREPAID


def test_notifier_low_risk():
    notifier = NotifierService()
    payload = notifier.evaluate_and_notify(
        order_id="ord_low_1",
        customer_id=VALID_HASHED_ID,
        risk_score=0.15
    )
    assert payload.risk_level == RiskLevel.LOW
    assert payload.recommended_action == OperationalAction.SHIP_COD
