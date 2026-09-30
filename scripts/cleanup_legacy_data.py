"""
One-time cleanup script to wipe all legacy fake seed data (IDs like '1', '101', 'CUS-1001')
from customers_collection, orders_collection, and predictions_collection.
"""
import sys, os
sys.path.insert(0, os.getcwd())

from app.db import customers_collection, orders_collection, predictions_collection

def cleanup_legacy_data():
    c_deleted = customers_collection.delete_many({})
    o_deleted = orders_collection.delete_many({})
    p_deleted = predictions_collection.delete_many({})

    print(f"[OK] Cleaned up MongoDB Atlas collections:")
    print(f"  Customers deleted:   {c_deleted.deleted_count}")
    print(f"  Orders deleted:      {o_deleted.deleted_count}")
    print(f"  Predictions deleted: {p_deleted.deleted_count}")
    print(f"Remaining in DB:")
    print(f"  Customers:   {customers_collection.count_documents({})}")
    print(f"  Orders:      {orders_collection.count_documents({})}")
    print(f"  Predictions: {predictions_collection.count_documents({})}")

if __name__ == "__main__":
    cleanup_legacy_data()
