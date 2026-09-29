from app.db import orders_collection, customers_collection
from app.models import (
    create_order_doc,
    create_customer_doc,
)


def seed_database():

    orders = [
        create_order_doc(
            order_id=1,
            customer_id=101,
            order_value=2500,
            payment_mode="COD",
            pincode="411001",
            category="Electronics",
            is_festive_window=False,
        ),
        create_order_doc(
            order_id=2,
            customer_id=102,
            order_value=1200,
            payment_mode="COD",
            pincode="411014",
            category="Fashion",
            is_festive_window=False,
        ),
    ]

    orders_collection.insert_many(orders)

    customers = [
        create_customer_doc(
            customer_id=101,
            total_orders=10,
            total_rto=6,
            avg_order_value=2300,
        ),
        create_customer_doc(
            customer_id=102,
            total_orders=8,
            total_rto=1,
            avg_order_value=1400,
        ),
    ]

    customers_collection.insert_many(customers)

    print("Database seeded successfully")


if __name__ == "__main__":
    seed_database()