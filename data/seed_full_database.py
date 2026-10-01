"""
seed_full_database.py — Populates MongoDB Atlas with all 1,000 real orders and 300+ customer profiles.
Runs the genuine ML scoring models, action recommendation engine, and cost calculator on every order.
Ensures 100% of data in MongoDB is real, evaluated, and ready for production dashboard and analytics.
"""

import sys, os
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from datetime import datetime, timezone

from app.db import (
    customers_collection,
    orders_collection,
    predictions_collection,
    strip_forbidden_fields
)
from app.core.scoring import score_order as ml_score_order
from app.services.action_recommendation import ActionRecommendationEngine
from app.services.cost_calculator import CostCalculator
from app.models import create_prediction_doc

CUSTOMERS_CSV = Path(__file__).resolve().parent.parent / "app" / "data" / "customers.csv"
ORDERS_CSV = Path(__file__).resolve().parent.parent / "app" / "data" / "orders.csv"

# Pre-defined test customers for easy manual UI testing
CONVENIENT_TEST_CUSTOMERS = [
    {
        "customer_id": "1",
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
        "created_at": datetime.now(timezone.utc),
    },
    {
        "customer_id": "2",
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
        "created_at": datetime.now(timezone.utc),
    },
    {
        "customer_id": "101",
        "past_orders_count": 10,
        "past_rto_orders": 6,
        "past_rto_rate": 0.60,
        "address_stability_score": 0.55,
        "distinct_addresses_used": 4,
        "tenure_months": 6,
        "orders_per_month": 1.7,
        "orders_last_90d": 5,
        "prev_cod_orders": 9,
        "prev_cod_success_rate": 0.44,
        "cod_share_history": 0.90,
        "avg_order_value": 2300.0,
        "created_at": datetime.now(timezone.utc),
    },
    {
        "customer_id": "102",
        "past_orders_count": 8,
        "past_rto_orders": 1,
        "past_rto_rate": 0.125,
        "address_stability_score": 0.88,
        "distinct_addresses_used": 1,
        "tenure_months": 10,
        "orders_per_month": 0.9,
        "orders_last_90d": 2,
        "prev_cod_orders": 5,
        "prev_cod_success_rate": 0.92,
        "cod_share_history": 0.63,
        "avg_order_value": 1400.0,
        "created_at": datetime.now(timezone.utc),
    },
    {
        "customer_id": "CUS-1001",
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
        "created_at": datetime.now(timezone.utc),
    },
]


def seed_database():
    print(f"Loading {CUSTOMERS_CSV} and {ORDERS_CSV}...")
    df_customers = pd.read_csv(CUSTOMERS_CSV)
    df_orders = pd.read_csv(ORDERS_CSV)

    print(f"Total customers in CSV: {len(df_customers)}")
    print(f"Total orders in CSV:    {len(df_orders)}")

    rec_engine = ActionRecommendationEngine()
    cost_calc = CostCalculator()

    # Clear existing collections
    print("Clearing existing collections in MongoDB...")
    customers_collection.delete_many({})
    orders_collection.delete_many({})
    predictions_collection.delete_many({})

    # 1. Build and seed customer profiles from order history
    df_orders["order_ts_dt"] = pd.to_datetime(df_orders["order_ts"])
    df_customers["signup_date_dt"] = pd.to_datetime(df_customers["signup_date"])
    max_order_ts = df_orders["order_ts_dt"].max()
    ninety_days_prior = max_order_ts - pd.Timedelta(days=90)

    orders_by_cust = {}
    for cid, group in df_orders.groupby("customer_id"):
        orders_by_cust[str(cid).strip().lower()] = group

    print("Building and inserting customer behavioral profiles...")
    cust_docs = []
    cust_pincode_map = {}

    for _, row in df_customers.iterrows():
        cid = str(row["customer_id"]).strip().lower()
        signup_dt = row["signup_date_dt"]
        pincode = str(row.get("pincode", "110001")).strip()
        cust_pincode_map[cid] = pincode

        group = orders_by_cust.get(cid)
        if group is not None and len(group) > 0:
            past_orders_count = int(len(group))
            rto_orders = int((group["outcome"].astype(str).str.upper() == "RTO").sum())
            past_rto_orders = rto_orders
            past_rto_rate = round(past_rto_orders / past_orders_count, 4)
            avg_order_val = round(float(group["value"].mean()), 2)
            
            cod_orders = group[group["payment_mode"].astype(str).str.upper() == "COD"]
            prev_cod_orders = int(len(cod_orders))
            cod_share = round(prev_cod_orders / past_orders_count, 4)
            if prev_cod_orders > 0:
                cod_rto = int((cod_orders["outcome"].astype(str).str.upper() == "RTO").sum())
                prev_cod_success_rate = round((prev_cod_orders - cod_rto) / prev_cod_orders, 4)
            else:
                prev_cod_success_rate = 0.85

            address_stability = round(float(group["address_completeness"].mean()), 2)
            distinct_addresses = int(max(1, round(4 * (1.0 - address_stability))))

            latest_order_dt = group["order_ts_dt"].max()
            tenure_days = max(1, (latest_order_dt - signup_dt).days)
            tenure_months = max(1, round(tenure_days / 30.0))
            orders_per_month = round(past_orders_count / max(tenure_months, 1), 2)
            orders_last_90d = int((group["order_ts_dt"] >= ninety_days_prior).sum())
        else:
            past_orders_count = 0
            past_rto_orders = 0
            past_rto_rate = 0.0
            avg_order_val = 0.0
            prev_cod_orders = 0
            prev_cod_success_rate = 0.0
            cod_share = 0.0
            address_stability = 0.50
            distinct_addresses = 1
            tenure_months = 0
            orders_per_month = 0.0
            orders_last_90d = 0

        doc = {
            "customer_id": cid,
            "pincode": pincode,
            "past_orders_count": past_orders_count,
            "past_rto_orders": past_rto_orders,
            "past_rto_rate": past_rto_rate,
            "address_stability_score": address_stability,
            "distinct_addresses_used": distinct_addresses,
            "tenure_months": tenure_months,
            "orders_per_month": orders_per_month,
            "orders_last_90d": orders_last_90d,
            "prev_cod_orders": prev_cod_orders,
            "prev_cod_success_rate": prev_cod_success_rate,
            "cod_share_history": cod_share,
            "avg_order_value": avg_order_val,
            "created_at": signup_dt.to_pydatetime().replace(tzinfo=timezone.utc),
        }
        cust_docs.append(strip_forbidden_fields(doc))

    # Add convenient test customers
    for tc in CONVENIENT_TEST_CUSTOMERS:
        cust_docs.append(strip_forbidden_fields(tc))

    if cust_docs:
        customers_collection.insert_many(cust_docs)
    print(f"[OK] Seeded {len(cust_docs)} customer profiles into MongoDB.")

    # 2. Score and seed ALL 1,000 real orders
    print(f"Scoring and inserting all {len(df_orders)} orders into MongoDB...")
    order_docs = []
    prediction_docs = []

    for idx, row in df_orders.iterrows():
        oid = str(row["order_id"]).strip()
        cid = str(row["customer_id"]).strip().lower()
        val = float(row["value"])
        pmode = "COD" if str(row["payment_mode"]).strip().upper() == "COD" else "PREPAID"
        category = str(row.get("category", "General")).strip()
        is_festive = bool(row.get("is_festive", 0))
        hour = int(row.get("hour_of_day", 14))
        addr_score = float(row.get("address_completeness", 0.8))
        raw_outcome = str(row.get("outcome", "delivered")).strip().upper()
        norm_outcome = "RTO" if raw_outcome == "RTO" else "DELIVERED"
        order_ts_str = str(row["order_ts"])
        pincode = cust_pincode_map.get(cid, "110001")

        # Prepare order dict for ML scoring engine
        order_payload = {
            "order_id": oid,
            "customer_id": cid,
            "order_value": val,
            "payment_mode": pmode,
            "pincode": pincode,
            "category": category,
            "is_festive_window": is_festive,
            "checkout_hour": hour,
            "address_quality_score": addr_score,
        }

        # Run real ML scoring engine
        ml_result = ml_score_order(order_payload)
        risk_score = ml_result["risk_score"]
        top_factors = ml_result.get("top_factors", [])

        # Run Action Recommendation Engine
        rec = rec_engine.recommend(
            risk_score=risk_score,
            order_value=val,
            payment_mode=pmode,
            top_factors=top_factors,
        )

        # Run Cost Calculator
        econ = cost_calc.calculate(
            order_value=val,
            risk_score=risk_score,
            action=rec["recommended_action"],
            suggested_deposit=rec["suggested_deposit"],
        )

        # Prepare Order Document
        order_doc = {
            "order_id": oid,
            "customer_id": cid,
            "order_value": val,
            "payment_mode": pmode,
            "pincode": pincode,
            "category": category,
            "is_festive_window": is_festive,
            "status": "DELIVERED" if norm_outcome == "DELIVERED" else "RTO",
            "delivery_status": norm_outcome,
            "created_at": order_ts_str,
            "scored_at": order_ts_str,
        }

        # Prepare Prediction Document
        pred_doc = create_prediction_doc(
            order_id=oid,
            risk_score=risk_score,
            action=rec["recommended_action"],
            reason="; ".join(top_factors[:3]),
        )
        pred_doc["customer_id"] = cid
        pred_doc["customer_status"] = "returning" if orders_by_cust.get(cid) is not None else "new"
        pred_doc["top_factors"] = top_factors
        pred_doc["suggested_deposit"] = rec["suggested_deposit"]
        pred_doc["economics"] = econ
        pred_doc["payment_mode"] = pmode
        pred_doc["order_value"] = val
        pred_doc["features"] = {
            "customer_type": "RETURNING" if orders_by_cust.get(cid) is not None else "NEW",
            "past_orders": len(orders_by_cust.get(cid, [])),
            "past_rtos": int((orders_by_cust.get(cid, pd.DataFrame())["outcome"].astype(str).str.upper() == "RTO").sum()) if cid in orders_by_cust else 0,
            "pincode": pincode,
            "festive_window": is_festive
        }
        pred_doc["scored_at"] = order_ts_str

        order_docs.append(strip_forbidden_fields(order_doc))
        prediction_docs.append(strip_forbidden_fields(pred_doc))

        if (idx + 1) % 200 == 0:
            print(f"Scored {idx + 1}/{len(df_orders)} orders...")

    print("Inserting orders and predictions into MongoDB Atlas...")
    orders_collection.insert_many(order_docs)
    predictions_collection.insert_many(prediction_docs)

    print("Creating indexes on collections...")
    customers_collection.create_index("customer_id", unique=True)
    orders_collection.create_index("order_id", unique=True)
    orders_collection.create_index("customer_id")
    predictions_collection.create_index("order_id", unique=True)
    predictions_collection.create_index("customer_id")
    predictions_collection.create_index("risk_score")

    print("\n" + "="*50)
    print("DATABASE SEEDING COMPLETE")
    print("="*50)
    print(f"Customers seeded:   {customers_collection.count_documents({})}")
    print(f"Orders seeded:      {orders_collection.count_documents({})}")
    print(f"Predictions seeded: {predictions_collection.count_documents({})}")
    print("="*50)


if __name__ == "__main__":
    seed_database()
