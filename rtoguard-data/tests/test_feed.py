"""
Unit tests for data feed FastAPI service endpoints.
"""

from datetime import date, datetime
from fastapi.testclient import TestClient

from src.feed import app

client = TestClient(app)

VALID_HASHED_ID = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "RTOGuard Data Feed Service"


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_ingest_customer_endpoint():
    payload = {
        "customer_id": VALID_HASHED_ID,
        "signup_date": "2025-04-01",
        "pincode": "110001"
    }
    response = client.post("/feed/customer", json=payload)
    assert response.status_code == 201
    assert response.json()["status"] == "success"


def test_ingest_order_endpoint():
    payload = {
        "order_id": "ord_feed_101",
        "customer_id": VALID_HASHED_ID,
        "order_ts": "2025-07-01T12:00:00",
        "value": 1999.0,
        "payment_mode": "COD",
        "category": "Apparel",
        "discount_pct": 20.0,
        "hour_of_day": 12,
        "address_completeness": 0.90,
        "cart_pattern": 0,
        "is_festive": 0,
        "outcome": "delivered"
    }
    response = client.post("/feed/order", json=payload)
    assert response.status_code == 201
    assert response.json()["status"] == "success"


def test_pincode_stats_endpoint():
    p_payload = {
        "pincode": "560001",
        "tier": 1,
        "smoothed_rto_rate": 0.115,
        "order_count": 850
    }
    resp = client.post("/feed/pincode", json=p_payload)
    assert resp.status_code == 201

    get_resp = client.get("/stats/pincode/560001")
    assert get_resp.status_code == 200
    assert get_resp.json()["tier"] == 1
