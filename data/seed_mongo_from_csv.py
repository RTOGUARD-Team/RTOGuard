"""
Seed MongoDB Atlas from real CSV datasets (customers.csv and orders.csv).
All customer_ids are 64-character SHA-256 hashes.
Strictly strips any forbidden PII keys (name, phone, email, address).
"""

import sys, os, re
sys.path.insert(0, os.getcwd())

import pandas as pd
from datetime import datetime, timezone
from app.db import (
    customers_collection,
    orders_collection,
    predictions_collection,
    strip_forbidden_fields
)
from app.rto_schemas import RawOrder
from app.api.rto_routes import score_order

CUSTOMERS_CSV = "app/data/customers.csv"
ORDERS_CSV = "app/data/orders.csv"

def seed_database():
    print(f"Loading {CUSTOMERS_CSV} and {ORDERS_CSV}...")
    df_customers = pd.read_csv(CUSTOMERS_CSV)
    df_orders = pd.read_csv(ORDERS_CSV)

    print(f"Total customers in CSV: {len(df_customers)}")
    print(f"Total orders in CSV:    {len(df_orders)}")

    # Clean existing collections
    customers_collection.delete_many({})
    orders_collection.delete_many({})
    predictions_collection.delete_many({})

    # Convert order_ts and signup_date
    df_orders["order_ts_dt"] = pd.to_datetime(df_orders["order_ts"])
    df_customers["signup_date_dt"] = pd.to_datetime(df_customers["signup_date"])
    max_order_ts = df_orders["order_ts_dt"].max()
    ninety_days_prior = max_order_ts - pd.Timedelta(days=90)

    # Pre-group orders by customer
    orders_by_cust = {}
    for cid, group in df_orders.groupby("customer_id"):
        orders_by_cust[cid] = group

    cust_docs = []
    for _, row in df_customers.iterrows():
        cid = str(row["customer_id"]).strip().lower()
        signup_dt = row["signup_date_dt"]
        pincode = str(row.get("pincode", "110001")).strip()

        group = orders_by_cust.get(cid)
        if group is not None and len(group) > 0:
            past_orders_count = int(len(group))
            rto_orders = int((group["outcome"].str.upper() == "RTO").sum())
            past_rto_orders = rto_orders
            past_rto_rate = round(past_rto_orders / past_orders_count, 4)
            avg_order_val = round(float(group["value"].mean()), 2)
            
            cod_orders = group[group["payment_mode"].str.upper() == "COD"]
            prev_cod_orders = int(len(cod_orders))
            cod_share = round(prev_cod_orders / past_orders_count, 4)
            if prev_cod_orders > 0:
                cod_rto = int((cod_orders["outcome"].str.upper() == "RTO").sum())
                prev_cod_success_rate = round((prev_cod_orders - cod_rto) / prev_cod_orders, 4)
            else:
                prev_cod_success_rate = 0.85

            address_stability = round(float(group["address_completeness"].mean()), 2)
            distinct_addresses = int(max(1, round(4 * (1.0 - address_stability))))

            # Tenure in months
            latest_order_dt = group["order_ts_dt"].max()
            tenure_days = max(1, (latest_order_dt - signup_dt).days)
            tenure_months = max(1, round(tenure_days / 30.0))
            orders_per_month = round(past_orders_count / max(tenure_months, 1), 2)
            orders_last_90d = int((group["order_ts_dt"] >= ninety_days_prior).sum())
        else:
            # Cold-start / new customer
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

        # Guard: Strip any forbidden PII field before insertion
        clean_doc = strip_forbidden_fields(doc)
        customers_collection.update_one(
            {"customer_id": cid},
            {"$set": clean_doc},
            upsert=True
        )

    print(f"[OK] Upserted {len(df_customers)} customer profiles into 'customers' collection.")

    # Seed a diverse subset of real orders from orders.csv into orders and predictions
    # Pick 25 varied orders so the dashboard & risk intelligence are populated
    sample_orders = df_orders.sample(n=min(25, len(df_orders)), random_state=42)
    print("Scoring and seeding sample orders into 'orders' & 'predictions'...")
    for _, o in sample_orders.iterrows():
        raw_req = RawOrder(
            order_id=str(o["order_id"]),
            customer_id=str(o["customer_id"]).strip().lower(),
            order_value=float(o["value"]),
            payment_mode=str(o["payment_mode"]).upper(),
            pincode="400001",  # valid standard pincode
            category=str(o["category"]),
            is_festive_window=bool(o.get("is_festive", 0))
        )
        score_order(raw_req)

    print(f"[OK] Seeded {len(sample_orders)} evaluated orders into 'orders' and 'predictions'.")

    # VERIFICATION AUDIT
    all_custs = list(customers_collection.find())
    all_orders = list(orders_collection.find())
    all_preds = list(predictions_collection.find())

    # Check for PII keys in customers
    pii_keys_found = []
    for c in all_custs:
        for k in c.keys():
            if k.lower() in ["name", "phone", "email", "address"]:
                pii_keys_found.append(k)

    # Check SHA-256 conformance
    sha256_pattern = re.compile(r"^[a-f0-9]{64}$")
    non_sha_custs = [c.get("customer_id") for c in all_custs if not sha256_pattern.match(str(c.get("customer_id", "")))]
    non_sha_orders = [o.get("customer_id") for o in all_orders if not sha256_pattern.match(str(o.get("customer_id", "")))]

    print("\n" + "="*50)
    print("SEEDING AUDIT SUMMARY")
    print("="*50)
    print(f"Total customers in MongoDB:   {len(all_custs)}")
    print(f"Total orders in MongoDB:      {len(all_orders)}")
    print(f"Total predictions in MongoDB: {len(all_preds)}")
    print(f"Forbidden PII keys found:     {len(pii_keys_found)} (Expected: 0)")
    print(f"Non-SHA-256 customer_ids:     {len(non_sha_custs)} (Expected: 0)")
    print(f"Non-SHA-256 in orders:        {len(non_sha_orders)} (Expected: 0)")

    if len(pii_keys_found) == 0 and len(non_sha_custs) == 0:
        print("[PASS] 100% of customer IDs match SHA-256 format and 0 documents contain PII.")
    else:
        print("[FAIL] Audit check failed!")

if __name__ == "__main__":
    seed_database()
