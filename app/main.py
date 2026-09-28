from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import orders, simulate, dashboard

app = FastAPI(title="RTOGuard AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(orders.router)
app.include_router(simulate.router)
app.include_router(dashboard.router)

@app.get("/")
def health():
    return {"status": "ok", "service": "RTOGuard AI"}