"""
Unit tests for Pydantic data models & PII validation rules.
"""

from datetime import date, datetime
import pytest
from pydantic import ValidationError

from src.models import Customer, Order, OutcomeMode, PaymentMode, PincodeStats

VALID_HASHED_ID = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_customer_valid():
    cust = Customer(
        customer_id=VALID_HASHED_ID,
        signup_date=date(2025, 5, 10),
        pincode="110001"
    )
    assert cust.customer_id == VALID_HASHED_ID
    assert cust.pincode == "110001"


def test_customer_invalid_hash():
    with pytest.raises(ValidationError) as excinfo:
        Customer(
            customer_id="cust_raw_1234",  # Not 64 hex chars
            signup_date=date(2025, 5, 10),
            pincode="110001"
        )
    assert "customer_id must be a 64-character SHA-256 hex string" in str(excinfo.value)


def test_customer_invalid_pincode():
    with pytest.raises(ValidationError) as excinfo:
        Customer(
            customer_id=VALID_HASHED_ID,
            signup_date=date(2025, 5, 10),
            pincode="010001"  # Starts with 0
        )
    assert "pincode must be a valid 6-digit Indian postal PIN code" in str(excinfo.value)


def test_customer_pii_rejection():
    with pytest.raises(ValidationError) as excinfo:
        Customer.model_validate({
            "customer_id": VALID_HASHED_ID,
            "signup_date": "2025-05-10",
            "pincode": "110001",
            "phone": "+919876543210"  # Forbidden PII
        })
    assert "PII Field violation" in str(excinfo.value)


def test_order_valid():
    ord_obj = Order(
        order_id="ord_1001",
        customer_id=VALID_HASHED_ID,
        order_ts=datetime(2025, 6, 15, 14, 30),
        value=1499.50,
        payment_mode=PaymentMode.COD,
        category="Apparel",
        discount_pct=15.0,
        hour_of_day=14,
        address_completeness=0.85,
        cart_pattern=1,
        is_festive=0,
        outcome=OutcomeMode.DELIVERED
    )
    assert ord_obj.value == 1499.50
    assert ord_obj.payment_mode == PaymentMode.COD


def test_order_invalid_value_and_ranges():
    with pytest.raises(ValidationError):
        Order(
            order_id="ord_1002",
            customer_id=VALID_HASHED_ID,
            order_ts=datetime(2025, 6, 15, 14, 30),
            value=-50.0,  # Invalid <= 0
            payment_mode=PaymentMode.COD,
            category="Electronics",
            discount_pct=120.0,  # Invalid > 100
            hour_of_day=25,  # Invalid > 23
            address_completeness=1.5,  # Invalid > 1.0
            cart_pattern=0,
            is_festive=0,
            outcome=OutcomeMode.DELIVERED
        )


def test_pincode_stats_valid():
    stat = PincodeStats(
        pincode="560001",
        tier=1,
        smoothed_rto_rate=0.1250,
        order_count=1200
    )
    assert stat.tier == 1
    assert stat.smoothed_rto_rate == 0.1250


def test_pincode_stats_invalid_tier():
    with pytest.raises(ValidationError):
        PincodeStats(
            pincode="560001",
            tier=4,  # Tier must be 1, 2, or 3
            smoothed_rto_rate=0.12,
            order_count=100
        )
