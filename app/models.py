"""
MongoDB document helpers for RTOGuard.

These are NOT ORM models — MongoDB is schema-less.
Each helper creates a proper document dict and provides
a from_doc() to convert a Mongo document back to a dict
with a clean `id` field (string) instead of ObjectId.
"""

from datetime import datetime, timezone


# ── Order ────────────────────────────────────────────────

def create_order_doc(
    order_id: int,
    customer_id: int,
    order_value: float,
    payment_mode: str,
    pincode: str,
    category: str,
    is_festive_window: bool,
) -> dict:
    """Build an order document ready for insertion."""
    return {
        "order_id": order_id,
        "customer_id": customer_id,
        "order_value": order_value,
        "payment_mode": payment_mode,
        "pincode": pincode,
        "category": category,
        "is_festive_window": is_festive_window,
        "created_at": datetime.now(timezone.utc),
    }


# ── Customer ─────────────────────────────────────────────

def create_customer_doc(
    customer_id: int,
    total_orders: int = 0,
    total_rto: int = 0,
    avg_order_value: float = 0.0,
) -> dict:
    """Build a customer profile document."""
    return {
        "customer_id": customer_id,
        "total_orders": total_orders,
        "total_rto": total_rto,
        "rto_rate": round(total_rto / total_orders, 4) if total_orders else 0.0,
        "avg_order_value": avg_order_value,
        "created_at": datetime.now(timezone.utc),
    }


# ── Prediction ───────────────────────────────────────────

def create_prediction_doc(
    order_id: int,
    risk_score: float,
    action: str,
    reason: str,
) -> dict:
    """Build a prediction/result document."""
    return {
        "order_id": order_id,
        "risk_score": risk_score,
        "action": action,
        "reason": reason,
        "scored_at": datetime.now(timezone.utc),
    }


# ── Helpers ──────────────────────────────────────────────

def doc_to_dict(doc: dict) -> dict:
    """Convert a MongoDB document to a plain dict with string id."""
    if doc is None:
        return {}
    doc["id"] = str(doc.pop("_id"))
    return doc
