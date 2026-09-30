
"""
Risk Scoring Engine Adapter (Riya's ML Models).

Wraps Riya's dual trained Logistic Regression pipelines:
- rtoguard_old_model.joblib (18 features for returning customers)
- rtoguard_new_model.joblib (13 features for first-time buyers)

Produces the exact contract:
{
    "risk_score": float,       # 0.0 to 1.0 (used by Shubham's Cost & Action engines)
    "top_factors": list[str]   # Human-readable reasons (used by Khyati's UI)
}
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Union
import joblib
import pandas as pd

from app.core.customer_repository import get_customer_profile as get_customer_info
from app.core.store import get_pincode_info


MODEL_DIR = Path(__file__).resolve().parent / "models"
OLD_MODEL_PATH = MODEL_DIR / "rtoguard_old_model.joblib"
NEW_MODEL_PATH = MODEL_DIR / "rtoguard_new_model.joblib"

OLD_FEATURES: List[str] = [
    "historical_orders",
    "historical_rto_orders",
    "historical_rto_rate",
    "address_stability_score",
    "distinct_addresses_used",
    "tenure_months",
    "orders_per_month",
    "orders_last_90d",
    "prev_cod_orders",
    "prev_cod_success_rate",
    "cod_share_history",
    "usual_order_value",
    "current_order_value",
    "order_value_ratio",
    "pincode_valid",
    "pincode_rto_rate",
    "festive_window",
    "product_category",
]

NEW_FEATURES: List[str] = [
    "address_quality_score",
    "house_number_present",
    "landmark_present",
    "address_word_count",
    "pincode_city_match",
    "pincode_valid",
    "pincode_rto_rate",
    "checkout_hour",
    "night_order",
    "checkout_duration_sec",
    "product_category",
    "current_order_value",
    "festive_window",
]

# Lazy-loaded models cache
_MODELS: Dict[str, Any] = {}


def _get_model(customer_type: str):
    """Loads and caches the trained ML pipeline."""
    if customer_type in _MODELS:
        return _MODELS[customer_type]

    path = OLD_MODEL_PATH if customer_type == "OLD" else NEW_MODEL_PATH
    if path.exists():
        try:
            model = joblib.load(path)
            _MODELS[customer_type] = model
            return model
        except Exception as e:
            print(f"Warning: Failed to load {customer_type} model from {path}: {e}")
    return None


def _extract_order_dict(order: Any) -> Dict[str, Any]:
    """Helper to convert Pydantic model or dict into standard dict."""
    if hasattr(order, "model_dump"):
        return order.model_dump()
    if hasattr(order, "dict"):
        return order.dict()
    return dict(order)


def score_order(order: Union[Dict[str, Any], Any]) -> Dict[str, Any]:
    """
    Adapter function that:
    1. Determines customer type (OLD vs NEW).
    2. Builds the exact pandas feature DataFrame expected by Riya's pipeline.
    3. Calls model.predict_proba() to get probability.
    4. Generates explainable top_factors.
    5. Returns {"risk_score": float, "top_factors": list[str]}.
    """
    od = _extract_order_dict(order)

    # 1. Structural near-zero risk for prepaid orders
    payment_mode = str(od.get("payment_mode", "COD")).upper()
    if payment_mode == "PREPAID":
        return {
            "risk_score": 0.02,
            "top_factors": ["Order is prepaid (near-zero RTO default exposure)"],
        }

    pincode_str = str(od.get("pincode", "110001"))
    pincode_info = get_pincode_info(pincode_str)

    order_value = float(od.get("order_value", 1000.0))
    is_festive = int(bool(od.get("is_festive_window", False)))
    category = str(od.get("category", od.get("product_category", "clothing"))).lower()

    # 2. Determine customer profile: prioritize inline history fields if supplied,
    # otherwise fall back to database / customer_repository lookup.
    has_inline_history = any(k in od for k in ("past_orders_count", "past_orders", "historical_orders"))

    if has_inline_history:
        past_orders = int(od.get("past_orders_count", od.get("past_orders", od.get("historical_orders", 0))))
        past_rtos = int(od.get("past_rto_orders", od.get("past_rtos", od.get("historical_rto_orders", 0))))
        rto_rate = float(od.get("past_rto_rate", od.get("historical_rto_rate", (past_rtos / max(past_orders, 1)) if past_orders else 0.0)))

        raw_cust_type = str(od.get("customer_type", "")).upper()
        if past_orders > 0 or past_rtos > 0:
            is_old_customer = True
        elif raw_cust_type in ("OLD", "RETURNING"):
            is_old_customer = True
        elif raw_cust_type == "NEW":
            is_old_customer = False
        else:
            is_old_customer = False

        customer_info = {
            "past_orders_count": past_orders,
            "past_rto_orders": past_rtos,
            "past_rto_rate": rto_rate,
            "address_stability_score": float(od.get("address_stability_score", 0.85 if is_old_customer else 0.50)),
            "distinct_addresses_used": int(od.get("distinct_addresses_used", 1)),
            "tenure_months": int(od.get("tenure_months", max(1, past_orders // 2) if is_old_customer else 0)),
            "orders_per_month": float(od.get("orders_per_month", 0.8 if is_old_customer else 0.0)),
            "orders_last_90d": int(od.get("orders_last_90d", min(past_orders, 2) if is_old_customer else 0)),
            "prev_cod_orders": int(od.get("prev_cod_orders", max(past_orders - 1, 0) if is_old_customer else 0)),
            "prev_cod_success_rate": float(od.get("prev_cod_success_rate", max(0.0, 1.0 - rto_rate) if is_old_customer else 0.0)),
            "cod_share_history": float(od.get("cod_share_history", 0.70 if is_old_customer else 0.0)),
            "avg_order_value": float(od.get("avg_order_value", od.get("usual_order_value", order_value))),
        }
    else:
        customer_id = od.get("customer_id", 0)
        customer_info = get_customer_info(customer_id)
        is_old_customer = customer_info.get("past_orders_count", 0) > 0

    customer_type = "OLD" if is_old_customer else "NEW"

    # 3. Build DataFrame matching Riya's exact columns
    model = _get_model(customer_type)
    factors: List[str] = []

    if customer_type == "OLD":
        hist_orders = customer_info.get("past_orders_count", 1)
        hist_rto = customer_info.get("past_rto_orders", 0)
        hist_rto_rate = hist_rto / max(hist_orders, 1)
        usual_ov = customer_info.get("avg_order_value", order_value)
        if usual_ov <= 0:
            usual_ov = order_value
        ov_ratio = order_value / usual_ov

        old_row = {
            "historical_orders": hist_orders,
            "historical_rto_orders": hist_rto,
            "historical_rto_rate": round(hist_rto_rate, 4),
            "address_stability_score": customer_info.get("address_stability_score", 0.85),
            "distinct_addresses_used": customer_info.get("distinct_addresses_used", 1),
            "tenure_months": customer_info.get("tenure_months", 6),
            "orders_per_month": customer_info.get("orders_per_month", 0.8),
            "orders_last_90d": customer_info.get("orders_last_90d", 2),
            "prev_cod_orders": customer_info.get("prev_cod_orders", max(hist_orders - 2, 1)),
            "prev_cod_success_rate": customer_info.get("prev_cod_success_rate", 0.80),
            "cod_share_history": customer_info.get("cod_share_history", 0.70),
            "usual_order_value": usual_ov,
            "current_order_value": order_value,
            "order_value_ratio": round(ov_ratio, 2),
            "pincode_valid": pincode_info.get("pincode_valid", 1),
            "pincode_rto_rate": pincode_info.get("historical_rto_rate", 0.18),
            "festive_window": is_festive,
            "product_category": category,
        }
        df_input = pd.DataFrame([old_row], columns=OLD_FEATURES)

        # Factor generation for returning customer
        if hist_rto_rate > 0.25:
            factors.append(f"High historical return rate ({round(hist_rto_rate*100)}%)")
        if ov_ratio > 1.5:
            factors.append(f"Order value {round(ov_ratio, 1)}x higher than customer average")
        if customer_info.get("distinct_addresses_used", 1) >= 3:
            factors.append("Multiple delivery addresses used recently")

    else:
        # NEW customer features
        checkout_hour = int(od.get("checkout_hour", 14))
        is_night = int(checkout_hour in [0, 1, 2, 3, 4, 5])

        new_row = {
            "address_quality_score": float(od.get("address_quality_score", 0.80)),
            "house_number_present": int(bool(od.get("house_number_present", True))),
            "landmark_present": int(bool(od.get("landmark_present", True))),
            "address_word_count": int(od.get("address_word_count", 10)),
            "pincode_city_match": int(bool(od.get("pincode_city_match", True))),
            "pincode_valid": pincode_info.get("pincode_valid", 1),
            "pincode_rto_rate": pincode_info.get("historical_rto_rate", 0.22),
            "checkout_hour": checkout_hour,
            "night_order": is_night,
            "checkout_duration_sec": float(od.get("checkout_duration_sec", 90.0)),
            "product_category": category,
            "current_order_value": order_value,
            "festive_window": is_festive,
        }
        df_input = pd.DataFrame([new_row], columns=NEW_FEATURES)

        factors.append("First-time customer (zero prior order history)")
        if is_night:
            factors.append("Late night order placement (00:00 - 05:00)")
        if new_row["address_quality_score"] < 0.65:
            factors.append("Incomplete or missing street/house address details")

    # Common contextual factors
    if order_value > 2500:
        factors.append(f"High order value COD (Rs. {int(order_value):,})")
    if is_festive:
        factors.append("Active festive surge window (higher return propensity)")
    if pincode_info.get("historical_rto_rate", 0) >= 0.28:
        factors.append(f"High-risk delivery pincode {pincode_str} (tier-3 zone)")

    # 4. Predict probability using Riya's model
    if model is not None:
        try:
            prob = float(model.predict_proba(df_input)[0, 1])
        except Exception as e:
            print(f"Error during ML inference: {e}")
            prob = 0.35
    else:
        # Fallback heuristic if joblib loading fails
        prob = 0.35 + (0.15 if is_festive else 0) + (0.20 if not is_old_customer else 0)

    prob = float(max(0.01, min(round(prob, 4), 0.99)))

    # Ensure at least one factor is always present
    if not factors:
        if prob < 0.30:
            factors.append("Consistent customer history with reliable delivery pincode")
        else:
            factors.append("COD checkout risk signals detected")

    return {
        "risk_score": prob,
        "top_factors": factors,
    }
