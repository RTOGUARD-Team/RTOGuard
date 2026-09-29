

from typing import Literal

from fastapi import APIRouter, Query

from app.schemas import SimulationResponse
from app.services.simulation_engine import SimulationEngine

router = APIRouter(prefix="/api")


@router.get("/simulate", response_model=SimulationResponse)
def simulate(
    window: Literal["normal", "festive"] = Query(
        default="normal",
        description="Simulation period"
    )
):
    result = SimulationEngine(window)
    return SimulationResponse(**result)


@router.get("/simulate",response_model=SimulationResponse)
def simulate():
    result= SimulationEngine()
    return SimulationResponse(**result)


'''
from fastapi import APIRouter, Query
from app.schemas import simulation
from app.schemas import SimulationResponse
from app.core.simulate import run_simulation      # ASSUMED: run_simulation(window: str) -> dict

router = APIRouter(prefix="/api")


@router.get("/simulate", response_model=SimulationResponse)
def simulate(window: str = Query("festive")):
    result = run_simulation(window)
    return SimulationResponse(**result)




'''
