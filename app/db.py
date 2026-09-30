from pymongo import MongoClient

from app.config import settings

client: MongoClient = MongoClient(settings.MONGO_URI)
db = client[settings.MONGO_DB_NAME]

# ── Collections ──────────────────────────────────────────
orders_collection      = db["orders"]
customers_collection   = db["customers"]
predictions_collection = db["predictions"]

# ── Privacy Guard ─────────────────────────────────────────
FORBIDDEN_PII_FIELDS = {"name", "phone", "email", "address"}


def strip_forbidden_fields(doc: dict) -> dict:
    """Removes any forbidden PII keys (name, phone, email, address) from a document or update dict."""
    if not isinstance(doc, dict):
        return doc
    clean = {k: v for k, v in doc.items() if k.lower() not in FORBIDDEN_PII_FIELDS}
    for op in ("$set", "$setOnInsert"):
        if op in clean and isinstance(clean[op], dict):
            clean[op] = {k: v for k, v in clean[op].items() if k.lower() not in FORBIDDEN_PII_FIELDS}
    return clean


def ping_db() -> bool:
    """Return True if MongoDB is reachable."""
    try:
        client.admin.command("ping")
        return True
    except Exception:
        return False
