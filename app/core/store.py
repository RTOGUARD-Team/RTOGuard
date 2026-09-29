"""      
RTOGuard In-Memory Data Store.

This is the canonical home for customer history and pincode lookup logic.
It is intentionally placed in app/core/ (not app/db.py) so that git pulls
that overwrite app/db.py do not affect this code.

app/db.py re-exports everything from here for backward compatibility.
"""

import csv as _csv
from pathlib import Path as _Path
from typing import Any, Dict, List, Union


# ─────────────────────────────────────────────────────────────────────────────
# CUSTOMER STORE
# In-memory behavioral profiles keyed by customer_id.
# Replace with a real DB query (SQLAlchemy / Supabase) when DB is ready.
# ─────────────────────────────────────────────────────────────────────────────

MOCK_CUSTOMERS: Dict[Union[int, str], Dict[str, Any]] = {
    1: {
        "past_orders_count": 8,
        "past_rto_orders": 1,
        "past_rto_rate": 0.125,
        "address_stability_score": 0.90,
        "distinct_addresses_used": 1,
        "tenure_months": 14,
        "orders_per_month": 0.8,
        "orders_last_90d": 3,
        "prev_cod_orders": 6,
        "prev_cod_success_rate": 0.85,
        "cod_share_history": 0.75,
        "avg_order_value": 1400.0,
    },
    2: {
        "past_orders_count": 0,   # NEW customer — first-time buyer
        "past_rto_orders": 0,
        "past_rto_rate": 0.0,
        "address_stability_score": 0.50,
        "distinct_addresses_used": 1,
        "tenure_months": 0,
        "orders_per_month": 0.0,
        "orders_last_90d": 0,
        "prev_cod_orders": 0,
        "prev_cod_success_rate": 0.0,
        "cod_share_history": 0.0,
        "avg_order_value": 0.0,
    },
    "CUS-1001": {
        "past_orders_count": 12,
        "past_rto_orders": 4,
        "past_rto_rate": 0.33,
        "address_stability_score": 0.65,
        "distinct_addresses_used": 3,
        "tenure_months": 8,
        "orders_per_month": 1.5,
        "orders_last_90d": 4,
        "prev_cod_orders": 10,
        "prev_cod_success_rate": 0.60,
        "cod_share_history": 0.83,
        "avg_order_value": 1800.0,
    },
}

_NEW_CUSTOMER_DEFAULT: Dict[str, Any] = {
    "past_orders_count": 0,
    "past_rto_orders": 0,
    "past_rto_rate": 0.0,
    "address_stability_score": 0.50,
    "distinct_addresses_used": 1,
    "tenure_months": 0,
    "orders_per_month": 0.0,
    "orders_last_90d": 0,
    "prev_cod_orders": 0,
    "prev_cod_success_rate": 0.0,
    "cod_share_history": 0.0,
    "avg_order_value": 0.0,
}


def get_customer_info(customer_id: Union[int, str]) -> Dict[str, Any]:
    """
    Retrieve customer behavioral profile by ID.
    Returns cold-start defaults for unknown / first-time buyers.
    """
    return MOCK_CUSTOMERS.get(customer_id, _NEW_CUSTOMER_DEFAULT)


# ─────────────────────────────────────────────────────────────────────────────
# PINCODE STORE
# Loaded from app/data/pincode_stats.csv at startup (30 real Indian pincodes
# with Bayesian-smoothed RTO rates from Riya's dataset).
# ─────────────────────────────────────────────────────────────────────────────

def _load_pincode_stats() -> Dict[str, Dict[str, Any]]:
    """Load pincode risk data from data/pincode_stats.csv at startup."""
    result: Dict[str, Dict[str, Any]] = {}
    csv_path = _Path(__file__).resolve().parent.parent / "data" / "pincode_stats.csv"
    if csv_path.exists():
        with open(csv_path, newline="", encoding="utf-8") as f:
            for row in _csv.DictReader(f):
                result[row["pincode"]] = {
                    "historical_rto_rate": float(row["smoothed_rto_rate"]),
                    "tier": int(row["tier"]),
                    "pincode_valid": 1,
                    "order_count": int(row["order_count"]),
                }
    return result


PINCODE_DATA: Dict[str, Dict[str, Any]] = _load_pincode_stats()

_PINCODE_DEFAULT: Dict[str, Any] = {
    "historical_rto_rate": 0.22,
    "tier": 2,
    "pincode_valid": 1,
    "order_count": 0,
}


def get_pincode_info(pincode: str) -> Dict[str, Any]:
    """
    Retrieve pincode reliability stats.
    Falls back to tier-2 defaults for unknown pincodes.
    """
    return PINCODE_DATA.get(pincode, _PINCODE_DEFAULT)


# ─────────────────────────────────────────────────────────────────────────────
# ORDER LOG
# In-memory log of evaluated orders for the session.
# ─────────────────────────────────────────────────────────────────────────────

LOGGED_ORDERS: List[Dict[str, Any]] = []


def log_order(order_data: Dict[str, Any]) -> None:
    """Append an evaluated order to the in-memory log."""
    LOGGED_ORDERS.append(order_data)
