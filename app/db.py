
from pymongo import MongoClient

from app.config import settings

client: MongoClient = MongoClient(settings.MONGO_URI)
db = client[settings.MONGO_DB_NAME]

# ── Collections ──────────────────────────────────────────
orders_collection      = db["orders"]
customers_collection   = db["customers"]
predictions_collection = db["predictions"]


def ping_db() -> bool:
    """Return True if MongoDB is reachable."""
    try:
        client.admin.command("ping")
        return True
    except Exception:
        return False

