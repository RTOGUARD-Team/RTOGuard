from fastapi import APIRouter, Query

from app.schemas import SimulationResponse
from app.core.simulate import run_simulation      # ASSUMED: run_simulation(window: str) -> dict

router = APIRouter(prefix="/api")


@router.get("/simulate", response_model=SimulationResponse)
def simulate(window: str = Query("festive")):
    result = run_simulation(window)
    return SimulationResponse(**result)