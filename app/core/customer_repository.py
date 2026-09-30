"""
Customer Repository — MongoDB-backed with in-memory fallback.

Priority:
  1. MongoDB customers_collection  (production)
  2. MOCK_CUSTOMERS in store.py    (local dev / no DB)

Usage:
    from app.core.customer_repository import get_customer_profile
    profile = get_customer_profile(customer_id)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Union

logger = logging.getLogger(__name__)

# ── In-memory fallback ──────────────────────────────────────────────────────
from app.core.store import get_customer_info as _mock_get, _NEW_CUSTOMER_DEFAULT

# ── MongoDB connection check ─────────────────────────────────────────────────
# We test connectivity ONCE at import time with a short timeout.
# If MongoDB is unreachable we set _USE_MONGO = False and skip all DB calls.

_USE_MONGO: bool = False
_customers_col = None


def _init_mongo() -> None:
    """Try connecting to MongoDB with a 500ms timeout. Safe to call at startup."""
    global _USE_MONGO, _customers_col
    try:
        from pymongo import MongoClient
        from app.config import settings
        client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=500)
        client.admin.command("ping")                    # raises if unreachable
        from app.db import customers_collection
        _customers_col = customers_collection
        _USE_MONGO = True
        logger.info("MongoDB connected — using live customer data.")
    except Exception as e:
        _USE_MONGO = False
        _customers_col = None
        logger.info("MongoDB not reachable (%s) — using in-memory store.", e)


_init_mongo()


# ── Field mapping ────────────────────────────────────────────────────────────
# MongoDB document fields  →  scoring engine field names
_FIELD_MAP = {
    # MongoDB field          : scoring field
    "past_orders_count"      : "past_orders_count",
    "past_rto_orders"        : "past_rto_orders",
    "past_rto_rate"          : "past_rto_rate",
    "address_stability_score": "address_stability_score",
    "distinct_addresses_used": "distinct_addresses_used",
    "tenure_months"          : "tenure_months",
    "orders_per_month"       : "orders_per_month",
    "orders_last_90d"        : "orders_last_90d",
    "prev_cod_orders"        : "prev_cod_orders",
    "prev_cod_success_rate"  : "prev_cod_success_rate",
    "cod_share_history"      : "cod_share_history",
    "avg_order_value"        : "avg_order_value",
    # Older seeds may use different names — handle both
    "total_orders"           : "past_orders_count",
    "total_rto"              : "past_rto_orders",
    "rto_rate"               : "past_rto_rate",
}


def _normalize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map a raw MongoDB customer document → the flat profile dict
    that score_order() expects.  Missing fields get safe defaults.
    """
    profile: Dict[str, Any] = dict(_NEW_CUSTOMER_DEFAULT)  # start from defaults

    for mongo_key, score_key in _FIELD_MAP.items():
        if mongo_key in doc:
            profile[score_key] = doc[mongo_key]

    # Derive rto_rate if not stored directly
    if profile.get("past_rto_rate", 0.0) == 0.0:
        orders = profile.get("past_orders_count", 0)
        rto    = profile.get("past_rto_orders", 0)
        if orders > 0:
            profile["past_rto_rate"] = round(rto / orders, 4)

    return profile


def _coerce_id(customer_id: Union[int, str]) -> list:
    """
    Return a list of candidate ID values to try in MongoDB query.
    Handles int / str / "CUS-1001"-style prefixes.
    """
    candidates = [customer_id]
    # Try int conversion
    try:
        candidates.append(int(customer_id))
    except (ValueError, TypeError):
        pass
    # Try str conversion
    candidates.append(str(customer_id))
    # Try numeric suffix ("CUS-1001" → 1001)
    s = str(customer_id)
    if "-" in s:
        suffix = s.split("-")[-1]
        try:
            candidates.append(int(suffix))
            candidates.append(suffix)
        except ValueError:
            pass
    return list(dict.fromkeys(candidates))  # deduplicate, preserve order


# ── Public API ───────────────────────────────────────────────────────────────

def get_customer_profile(customer_id: Union[int, str]) -> Dict[str, Any]:
    """
    Fetch the customer behavioural profile used by the scoring engine.

    Flow:
      1. Try MongoDB (production path) — only if MongoDB is reachable.
      2. Fall back to MOCK_CUSTOMERS (local dev / offline).
      3. If still not found → return cold-start defaults (new customer).

    Returns:
        dict with keys matching score_order() expectations.
    """
    if _USE_MONGO and _customers_col is not None:
        # Try each candidate ID format in MongoDB
        for cid in _coerce_id(customer_id):
            try:
                doc = _customers_col.find_one({"customer_id": cid})
                if doc:
                    logger.debug("MongoDB hit for customer_id=%s (queried as %s)", customer_id, cid)
                    return _normalize_doc(doc)
            except Exception as e:
                logger.warning("MongoDB query failed for customer_id=%s: %s", cid, e)
                break  # don't retry on connection error

        logger.info("Customer %s not found in MongoDB → falling back to in-memory.", customer_id)

    # Fallback: in-memory MOCK_CUSTOMERS (handles type coercion too)
    return _mock_get(customer_id)




def is_new_customer(profile: Dict[str, Any]) -> bool:
    """Convenience helper: True if the profile has no prior order history."""
    return profile.get("past_orders_count", 0) == 0
