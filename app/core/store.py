"""
RTOGuard In-Memory Data Store.

This is the canonical home for customer history and pincode lookup logic.
It is intentionally placed in app/core/ (not app/db.py) so that git pulls
that overwrite app/db.py do not affect this code.

app/db.py re-exports everything from here for backward compatibility.
"""

import csv as _csv
from datetime import datetime as _datetime
from pathlib import Path as _Path
from typing import Any, Dict, List


# ─────────────────────────────────────────────────────────────────────────────
# CUSTOMER STORE
# Built by aggregating data/orders.csv per customer_id (SHA-256 hash).
# customers.csv only has customer_id/signup_date/pincode — history fields
# like past_orders_count, past_rto_rate, avg_order_value are DERIVED here
# from the customer's actual order history, not stored directly.
# Replace with a real DB query when the database is ready.
# ─────────────────────────────────────────────────────────────────────────────

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


def _load_customer_profiles() -> Dict[str, Dict[str, Any]]:
    """Aggregate orders.csv into per-customer behavioral profiles."""
    base_dir = _Path(__file__).resolve().parent.parent / "data"
    customers_path = base_dir / "customers.csv"
    orders_path = base_dir / "orders.csv"

    signup_dates: Dict[str, str] = {}
    if customers_path.exists():
        with open(customers_path, newline="", encoding="utf-8") as f:
            for row in _csv.DictReader(f):
                signup_dates[row["customer_id"]] = row["signup_date"]

    agg: Dict[str, Dict[str, Any]] = {}
    if orders_path.exists():
        with open(orders_path, newline="", encoding="utf-8") as f:
            for row in _csv.DictReader(f):
                cid = row["customer_id"]
                if cid not in agg:
                    agg[cid] = {
                        "order_count": 0,
                        "rto_count": 0,
                        "cod_count": 0,
                        "cod_success_count": 0,
                        "total_value": 0.0,
                    }
                a = agg[cid]
                a["order_count"] += 1
                is_rto = row["outcome"].strip().lower() == "rto"
                is_cod = row["payment_mode"].strip().upper() == "COD"
                if is_rto:
                    a["rto_count"] += 1
                if is_cod:
                    a["cod_count"] += 1
                    if not is_rto:
                        a["cod_success_count"] += 1
                a["total_value"] += float(row["value"])

    result: Dict[str, Dict[str, Any]] = {}
    today = _datetime.now()
    for cid, a in agg.items():
        n = a["order_count"]
        signup = signup_dates.get(cid)
        tenure_months = 0
        if signup:
            try:
                signup_dt = _datetime.strptime(signup, "%Y-%m-%d")
                tenure_months = max(
                    0, (today.year - signup_dt.year) * 12 + (today.month - signup_dt.month)
                )
            except ValueError:
                pass

        result[cid] = {
            "past_orders_count": n,
            "past_rto_orders": a["rto_count"],
            "past_rto_rate": round(a["rto_count"] / n, 4) if n else 0.0,
            "address_stability_score": 0.75,  # not present in source data; reasonable default
            "distinct_addresses_used": 1,
            "tenure_months": tenure_months,
            "orders_per_month": round(n / max(tenure_months, 1), 2),
            "orders_last_90d": 0,  # requires order_ts filtering; not computed yet
            "prev_cod_orders": a["cod_count"],
            "prev_cod_success_rate": (
                round(a["cod_success_count"] / a["cod_count"], 4) if a["cod_count"] else 0.0
            ),
            "cod_share_history": round(a["cod_count"] / n, 4) if n else 0.0,
            "avg_order_value": round(a["total_value"] / n, 2) if n else 0.0,
        }

    return result


MOCK_CUSTOMERS: Dict[str, Dict[str, Any]] = _load_customer_profiles()


def get_customer_info(customer_id: str) -> Dict[str, Any]:
    """Retrieve customer behavioral profile by SHA-256 hash. Cold-start default if unknown."""
    return MOCK_CUSTOMERS.get(str(customer_id), dict(_NEW_CUSTOMER_DEFAULT))


# ─────────────────────────────────────────────────────────────────────────────
# PINCODE STORE
# Loaded from app/data/pincode_stats.csv at startup (real pincodes with
# Bayesian-smoothed RTO rates).
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