"""
Populate a rich, diverse dataset of Customers, Orders, and Predictions
directly into MongoDB Atlas for realistic real-time dashboard analytics.
"""

from app.db import customers_collection, orders_collection, predictions_collection
from app.api.rto_routes import score_order
from app.rto_schemas import RawOrder
from datetime import datetime, timezone, timedelta
import random

def _dt(days_ago=0, hours_ago=0):
    return datetime.now(timezone.utc) - timedelta(days=days_ago, hours=hours_ago)

CUSTOMERS_DATA = [
    {
        "customer_id": "1",
        "name": "Amit Shah",
        "past_orders_count": 14,
        "past_rto_orders": 1,
        "past_rto_rate": 0.0714,
        "address_stability_score": 0.95,
        "distinct_addresses_used": 1,
        "tenure_months": 18,
        "orders_per_month": 0.9,
        "orders_last_90d": 4,
        "prev_cod_orders": 8,
        "prev_cod_success_rate": 0.88,
        "cod_share_history": 0.57,
        "avg_order_value": 1650.0,
        "created_at": _dt(180)
    },
    {
        "customer_id": "101",
        "name": "Rajan Mehta",
        "past_orders_count": 12,
        "past_rto_orders": 7,
        "past_rto_rate": 0.5833,
        "address_stability_score": 0.50,
        "distinct_addresses_used": 4,
        "tenure_months": 6,
        "orders_per_month": 2.0,
        "orders_last_90d": 6,
        "prev_cod_orders": 10,
        "prev_cod_success_rate": 0.40,
        "cod_share_history": 0.83,
        "avg_order_value": 2800.0,
        "created_at": _dt(90)
    },
    {
        "customer_id": "102",
        "name": "Sneha Patel",
        "past_orders_count": 9,
        "past_rto_orders": 1,
        "past_rto_rate": 0.1111,
        "address_stability_score": 0.89,
        "distinct_addresses_used": 1,
        "tenure_months": 11,
        "orders_per_month": 0.8,
        "orders_last_90d": 3,
        "prev_cod_orders": 6,
        "prev_cod_success_rate": 0.85,
        "cod_share_history": 0.67,
        "avg_order_value": 1350.0,
        "created_at": _dt(120)
    },
    {
        "customer_id": "103",
        "name": "Rohan Verma",
        "past_orders_count": 16,
        "past_rto_orders": 2,
        "past_rto_rate": 0.1250,
        "address_stability_score": 0.92,
        "distinct_addresses_used": 1,
        "tenure_months": 15,
        "orders_per_month": 1.1,
        "orders_last_90d": 4,
        "prev_cod_orders": 7,
        "prev_cod_success_rate": 0.90,
        "cod_share_history": 0.44,
        "avg_order_value": 1850.0,
        "created_at": _dt(150)
    },
    {
        "customer_id": "104",
        "name": "Arjun Kulkarni",
        "past_orders_count": 11,
        "past_rto_orders": 5,
        "past_rto_rate": 0.4545,
        "address_stability_score": 0.60,
        "distinct_addresses_used": 3,
        "tenure_months": 8,
        "orders_per_month": 1.4,
        "orders_last_90d": 5,
        "prev_cod_orders": 9,
        "prev_cod_success_rate": 0.55,
        "cod_share_history": 0.82,
        "avg_order_value": 2400.0,
        "created_at": _dt(80)
    },
    {
        "customer_id": "CUS-1001",
        "name": "Vikram Joshi",
        "past_orders_count": 13,
        "past_rto_orders": 4,
        "past_rto_rate": 0.3077,
        "address_stability_score": 0.65,
        "distinct_addresses_used": 2,
        "tenure_months": 9,
        "orders_per_month": 1.4,
        "orders_last_90d": 4,
        "prev_cod_orders": 10,
        "prev_cod_success_rate": 0.65,
        "cod_share_history": 0.77,
        "avg_order_value": 1950.0,
        "created_at": _dt(100)
    },
    {
        "customer_id": "CUS-1002",
        "name": "Neha Sharma",
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
        "created_at": _dt(10)
    },
    {
        "customer_id": "CUS-1003",
        "name": "Aditya Rao",
        "past_orders_count": 19,
        "past_rto_orders": 1,
        "past_rto_rate": 0.0526,
        "address_stability_score": 0.98,
        "distinct_addresses_used": 1,
        "tenure_months": 24,
        "orders_per_month": 0.8,
        "orders_last_90d": 3,
        "prev_cod_orders": 3,
        "prev_cod_success_rate": 1.0,
        "cod_share_history": 0.16,
        "avg_order_value": 3200.0,
        "created_at": _dt(300)
    },
    {
        "customer_id": "CUS-1004",
        "name": "Kavita Reddy",
        "past_orders_count": 7,
        "past_rto_orders": 4,
        "past_rto_rate": 0.5714,
        "address_stability_score": 0.52,
        "distinct_addresses_used": 3,
        "tenure_months": 5,
        "orders_per_month": 1.4,
        "orders_last_90d": 4,
        "prev_cod_orders": 6,
        "prev_cod_success_rate": 0.33,
        "cod_share_history": 0.86,
        "avg_order_value": 2900.0,
        "created_at": _dt(45)
    },
    {
        "customer_id": "CUS-1005",
        "name": "Siddharth Jain",
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
        "created_at": _dt(2)
    },
]

ORDERS_TO_EVALUATE = [
    # High Risk Orders (Returning high RTO users / high cart values COD)
    {"order_id": "ORD-78210", "customer_id": "101", "order_value": 3499.0, "payment_mode": "COD", "pincode": "411001", "category": "Electronics", "is_festive_window": True},
    {"order_id": "ORD-78211", "customer_id": "104", "order_value": 2899.0, "payment_mode": "COD", "pincode": "560001", "category": "Home & Kitchen", "is_festive_window": False},
    {"order_id": "ORD-78212", "customer_id": "CUS-1004", "order_value": 3150.0, "payment_mode": "COD", "pincode": "110001", "category": "Fashion", "is_festive_window": True},
    {"order_id": "ORD-78213", "customer_id": "101", "order_value": 4200.0, "payment_mode": "COD", "pincode": "800001", "category": "Electronics", "is_festive_window": True},
    
    # Medium Risk Orders (Partial Deposit recommended)
    {"order_id": "ORD-78214", "customer_id": "CUS-1001", "order_value": 1850.0, "payment_mode": "COD", "pincode": "411014", "category": "Apparel", "is_festive_window": False},
    {"order_id": "ORD-78215", "customer_id": "102", "order_value": 1699.0, "payment_mode": "COD", "pincode": "400001", "category": "Fashion", "is_festive_window": True},
    {"order_id": "ORD-78216", "customer_id": "104", "order_value": 1450.0, "payment_mode": "COD", "pincode": "110001", "category": "Apparel", "is_festive_window": False},
    {"order_id": "ORD-78217", "customer_id": "CUS-1002", "order_value": 2400.0, "payment_mode": "COD", "pincode": "110001", "category": "Electronics", "is_festive_window": True},
    
    # Safe / Low Risk Orders (Ship normal COD or Prepaid)
    {"order_id": "ORD-78218", "customer_id": "1", "order_value": 1250.0, "payment_mode": "COD", "pincode": "411001", "category": "Apparel", "is_festive_window": False},
    {"order_id": "ORD-78219", "customer_id": "103", "order_value": 1499.0, "payment_mode": "COD", "pincode": "560001", "category": "Fashion", "is_festive_window": False},
    {"order_id": "ORD-78220", "customer_id": "CUS-1003", "order_value": 3800.0, "payment_mode": "PREPAID", "pincode": "400001", "category": "Electronics", "is_festive_window": False},
    {"order_id": "ORD-78221", "customer_id": "1", "order_value": 999.0, "payment_mode": "PREPAID", "pincode": "411001", "category": "Apparel", "is_festive_window": False},
    {"order_id": "ORD-78222", "customer_id": "CUS-1003", "order_value": 2100.0, "payment_mode": "COD", "pincode": "400001", "category": "Home & Kitchen", "is_festive_window": False},
    {"order_id": "ORD-78223", "customer_id": "103", "order_value": 850.0, "payment_mode": "COD", "pincode": "560001", "category": "Fashion", "is_festive_window": False},
    {"order_id": "ORD-78224", "customer_id": "CUS-1005", "order_value": 750.0, "payment_mode": "COD", "pincode": "411001", "category": "Apparel", "is_festive_window": False},
]

def populate_database():
    print("Clearing and re-populating MongoDB Atlas collections...")
    customers_collection.delete_many({})
    orders_collection.delete_many({})
    predictions_collection.delete_many({})

    # 1. Insert rich customer profiles
    for c in CUSTOMERS_DATA:
        customers_collection.insert_one(c)
    print(f"[OK] Inserted {len(CUSTOMERS_DATA)} customer profiles into 'customers' collection.")

    # 2. Score and evaluate each order through the full ML risk pipeline
    print("Evaluating orders through ML Risk Engine & Cost Calculator...")
    for o in ORDERS_TO_EVALUATE:
        raw_req = RawOrder(**o)
        score_order(raw_req)

    print(f"[OK] Evaluated and saved {len(ORDERS_TO_EVALUATE)} orders into 'orders' & 'predictions' collections.")
    print(f"Current counts in MongoDB Atlas:")
    print(f"  Customers:   {customers_collection.count_documents({})}")
    print(f"  Orders:      {orders_collection.count_documents({})}")
    print(f"  Predictions: {predictions_collection.count_documents({})}")

if __name__ == "__main__":
    populate_database()

