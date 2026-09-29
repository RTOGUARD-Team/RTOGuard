from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import orders, dashboard
from app.api.rto_routes import router as rto_router
from app.db import ping_db

app = FastAPI(title="RTOGuard AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(orders.router)
app.include_router(dashboard.router)
app.include_router(rto_router)


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "RTOGuard AI",
        "db_connected": ping_db(),
    }

@app.get("/health")
def health_check():
    return {
        "api": "ok",
        "mongodb": "connected" if ping_db() else "disconnected"
    }