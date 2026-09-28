"""
FastAPI Data Feed Service for RTOGuard.

Provides real-time ingestion, validation, and retrieval endpoints for:
- Orders: Ingestion & Pydantic validation
- Customers: Ingestion & hashed ID validation
- Pincode Stats: Lookup pincode tier and smoothed RTO rates
"""

from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

from ..models import Customer, Order, PincodeStats

app = FastAPI(
    title="RTOGuard Data Feed Service",
    description="Real-time ingestion and validation data feed for RTOGuard checkout risk analysis.",
    version="1.0.0"
)

# In-memory datasets store for feed service
IN_MEMORY_CUSTOMERS: Dict[str, Customer] = {}
IN_MEMORY_PINCODES: Dict[str, PincodeStats] = {}
IN_MEMORY_ORDERS: List[Order] = []


class DataIngestResponse(BaseModel):
    status: str
    record_id: str
    message: str


@app.get("/")
def root_welcome():
    """Root welcome endpoint with service summary and links."""
    return {
        "service": "RTOGuard Data Feed Service",
        "status": "online",
        "documentation": "http://127.0.0.1:8000/docs",
        "health_check": "http://127.0.0.1:8000/health",
        "endpoints": {
            "health": "GET /health",
            "ingest_customer": "POST /feed/customer",
            "ingest_order": "POST /feed/order",
            "ingest_pincode": "POST /feed/pincode",
            "get_pincode_stats": "GET /stats/pincode/{pincode}"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "rtoguard-data-feed",
        "customers_loaded": len(IN_MEMORY_CUSTOMERS),
        "orders_loaded": len(IN_MEMORY_ORDERS),
        "pincodes_loaded": len(IN_MEMORY_PINCODES)
    }


@app.post("/feed/customer", response_model=DataIngestResponse, status_code=status.HTTP_201_CREATED)
def ingest_customer(customer: Customer):
    """
    Ingest and validate a customer record.
    Rejects any unhashed IDs or PII attributes.
    """
    IN_MEMORY_CUSTOMERS[customer.customer_id] = customer
    return DataIngestResponse(
        status="success",
        record_id=customer.customer_id,
        message="Customer ingested and validated successfully."
    )


@app.post("/feed/order", response_model=DataIngestResponse, status_code=status.HTTP_201_CREATED)
def ingest_order(order: Order):
    """
    Ingest and validate an order event at checkout.
    """
    IN_MEMORY_ORDERS.append(order)
    return DataIngestResponse(
        status="success",
        record_id=order.order_id,
        message="Order ingested and validated successfully."
    )


@app.post("/feed/pincode", response_model=DataIngestResponse, status_code=status.HTTP_201_CREATED)
def ingest_pincode(pincode_stat: PincodeStats):
    """
    Ingest and update pincode risk statistics.
    """
    IN_MEMORY_PINCODES[pincode_stat.pincode] = pincode_stat
    return DataIngestResponse(
        status="success",
        record_id=pincode_stat.pincode,
        message="Pincode stats updated successfully."
    )


@app.get("/stats/pincode/{pincode}", response_model=PincodeStats)
def get_pincode_stats(pincode: str):
    """
    Retrieve tier and smoothed RTO rate for a given pincode.
    """
    if pincode not in IN_MEMORY_PINCODES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pincode {pincode} not found in statistics dataset."
        )
    return IN_MEMORY_PINCODES[pincode]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.feed.data_feed:app", host="0.0.0.0", port=8000, reload=True)
