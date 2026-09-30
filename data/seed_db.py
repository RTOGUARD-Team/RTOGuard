"""
seed_db.py — Populates MongoDB with realistic customer profiles and sample orders.

Run once before testing:
    python -m data.seed_db

The customers collection is the source of truth for the scoring engine.
"""

from app.db import customers_collection, orders_collection, predictions_collection
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc)


# ── Customer profiles ─────────────────────────────────────────────────────────
# These fields map 1:1 to what get_customer_profile() / score_order() expects.

CUSTOMERS = [
    {
        "customer_id"            : 1,
        "name"                   : "Amit Shah",
        "past_orders_count"      : 8,
        "past_rto_orders"        : 1,
        "past_rto_rate"          : 0.125,
        "address_stability_score": 0.90,
        "distinct_addresses_used": 1,
        "tenure_months"          : 14,
        "orders_per_month"       : 0.8,
        "orders_last_90d"        : 3,
        "prev_cod_orders"        : 6,
        "prev_cod_success_rate"  : 0.85,
        "cod_share_history"      : 0.75,
        "avg_order_value"        : 1400.0,
        "created_at"             : _now(),
    },
    {
    "customer_id"            : 103,               # int or str (e.g. 103, "CUS-2001")
    "name"                   : "Rohan Verma",
    "past_orders_count"      : 15,                # Total lifetime orders
    "past_rto_orders"        : 2,                 # How many orders returned
    "past_rto_rate"          : 0.133,             # past_rto_orders / past_orders_count
    "address_stability_score": 0.95,              # 0.0 to 1.0 (consistent delivery location)
    "distinct_addresses_used": 1,                 # Number of different addresses used
    "tenure_months"          : 18,                # Account age in months
    "orders_per_month"       : 0.83,              # Monthly order frequency
    "orders_last_90d"        : 4,                 # Recent order activity
    "prev_cod_orders"        : 8,                 # Past COD order count
    "prev_cod_success_rate"  : 0.875,             # Delivered COD / total COD
    "cod_share_history"      : 0.53,              # COD orders / total orders
    "avg_order_value"        : 1750.0,            # Average basket size
    "created_at"             : _now(),
},
    {
        "customer_id"            : 2,
        "name"                   : "Priya Nair",
        "past_orders_count"      : 0,   # first-time buyer
        "past_rto_orders"        : 0,
        "past_rto_rate"          : 0.0,
        "address_stability_score": 0.50,
        "distinct_addresses_used": 1,
        "tenure_months"          : 0,
        "orders_per_month"       : 0.0,
        "orders_last_90d"        : 0,
        "prev_cod_orders"        : 0,
        "prev_cod_success_rate"  : 0.0,
        "cod_share_history"      : 0.0,
        "avg_order_value"        : 0.0,
        "created_at"             : _now(),
    },
    {
        "customer_id"            : 101,
        "name"                   : "Rajan Mehta",
        "past_orders_count"      : 10,
        "past_rto_orders"        : 6,
        "past_rto_rate"          : 0.60,
        "address_stability_score": 0.55,
        "distinct_addresses_used": 4,
        "tenure_months"          : 6,
        "orders_per_month"       : 1.7,
        "orders_last_90d"        : 5,
        "prev_cod_orders"        : 9,
        "prev_cod_success_rate"  : 0.44,
        "cod_share_history"      : 0.90,
        "avg_order_value"        : 2300.0,
        "created_at"             : _now(),
    },
    {
        "customer_id"            : 102,
        "name"                   : "Sneha Patel",
        "past_orders_count"      : 8,
        "past_rto_orders"        : 1,
        "past_rto_rate"          : 0.125,
        "address_stability_score": 0.88,
        "distinct_addresses_used": 1,
        "tenure_months"          : 10,
        "orders_per_month"       : 0.9,
        "orders_last_90d"        : 2,
        "prev_cod_orders"        : 5,
        "prev_cod_success_rate"  : 0.92,
        "cod_share_history"      : 0.63,
        "avg_order_value"        : 1400.0,
        "created_at"             : _now(),
    },
    {
        "customer_id"            : "CUS-1001",
        "name"                   : "Vikram Joshi",
        "past_orders_count"      : 12,
        "past_rto_orders"        : 4,
        "past_rto_rate"          : 0.33,
        "address_stability_score": 0.65,
        "distinct_addresses_used": 3,
        "tenure_months"          : 8,
        "orders_per_month"       : 1.5,
        "orders_last_90d"        : 4,
        "prev_cod_orders"        : 10,
        "prev_cod_success_rate"  : 0.60,
        "cod_share_history"      : 0.83,
        "avg_order_value"        : 1800.0,
        "created_at"             : _now(),
    },
   {
  "customer_id": 104,
  "name": "Arjun Kulkarni",
  "past_orders_count": 11,
  "past_rto_orders": 5,
  "past_rto_rate": 0.455,
  "address_stability_score": 0.62,
  "distinct_addresses_used": 3,
  "tenure_months": 7,
  "orders_per_month": 1.57,
  "orders_last_90d": 5,
  "prev_cod_orders": 8,
  "prev_cod_success_rate": 0.50,
  "cod_share_history": 0.73,
  "avg_order_value": 2100.0
},
]

# ── Sample orders ─────────────────────────────────────────────────────────────

ORDERS = [
    {
        "order_id"        : "ORD-001",
        "customer_id"     : 101,
        "order_value"     : 2500.0,
        "payment_mode"    : "COD",
        "pincode"         : "411001",
        "category"        : "Electronics",
        "is_festive_window": False,
        "created_at"      : _now(),
    },
    {
        "order_id"        : "ORD-002",
        "customer_id"     : 102,
        "order_value"     : 1200.0,
        "payment_mode"    : "COD",
        "pincode"         : "411014",
        "category"        : "Fashion",
        "is_festive_window": False,
        "created_at"      : _now(),
    },
    {
    "order_id": "ORD-003",
    "customer_id": 104,
    "order_value": 4799.0,
    "payment_mode": "COD",
    "pincode": "560001",
    "category": "Home & Kitchen",
    "is_festive_window": False,
    "created_at": _now(),
},
]


def seed_database(clear_existing: bool = True):
    """
    Seed the MongoDB database.

    Args:
        clear_existing: If True, drops existing documents before inserting.
                        Set False in production to avoid data loss.
    """
    if clear_existing:
        customers_collection.delete_many({})
        orders_collection.delete_many({})
        # predictions_collection.delete_many({})
        print("Cleared existing data.")

    # Upsert customers (safe to run multiple times)
    for c in CUSTOMERS:
        customers_collection.update_one(
            {"customer_id": c["customer_id"]},
            {"$set": c},
            upsert=True,
        )
    print(f"Seeded {len(CUSTOMERS)} customers.")

    # Insert orders (idempotent via upsert on order_id)
    for o in ORDERS:
        orders_collection.update_one(
            {"order_id": o["order_id"]},
            {"$set": o},
            upsert=True,
        )
    print(f"Seeded {len(ORDERS)} orders.")

    # Create indexes for fast lookups
    customers_collection.create_index("customer_id", unique=True)
    orders_collection.create_index("order_id", unique=True)
    orders_collection.create_index("customer_id")
    predictions_collection.create_index("order_id")
    predictions_collection.create_index("customer_id")
    print("Indexes created.")
    print("Database seeded successfully.")



if __name__ == "__main__":
    seed_database()