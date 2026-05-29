"""Scheduler and simulation API routes."""

from __future__ import annotations

from typing import Annotated, Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas import SimulateRequest, SimulationResponse
from ..services.simulation_service import processes_from_schema, run_simulation
from ..config import get_settings

router = APIRouter(prefix="/api", tags=["Scheduler"])
settings = get_settings()


@router.get("/algorithms")
async def list_algorithms() -> Dict[str, Any]:
    """Return all supported scheduling algorithms and their parameters."""
    return {
        "algorithms": [
            {
                "id": "FCFS",
                "name": "First Come First Serve",
                "type": "Non-Preemptive",
                "description": "Processes are executed in arrival order. Simple but can cause convoy effect.",
                "parameters": [],
            },
            {
                "id": "SJF",
                "name": "Shortest Job First",
                "type": "Non-Preemptive",
                "description": "Schedules shortest burst-time process first. Optimal avg waiting time.",
                "parameters": [],
            },
            {
                "id": "SRTF",
                "name": "Shortest Remaining Time First",
                "type": "Preemptive",
                "description": "Preemptive version of SJF. Preempts running process if shorter job arrives.",
                "parameters": [],
            },
            {
                "id": "Round Robin",
                "name": "Round Robin",
                "type": "Preemptive",
                "description": "Each process gets a fixed CPU time quantum. Fair, no starvation.",
                "parameters": [
                    {"name": "time_quantum", "type": "float", "default": 4.0, "min": 0.5, "max": 100.0},
                ],
            },
            {
                "id": "Priority",
                "name": "Priority Scheduling",
                "type": "Non-Preemptive",
                "description": "Schedules by priority (lower number = higher priority). Aging prevents starvation.",
                "parameters": [
                    {"name": "aging_interval", "type": "float", "default": 10.0, "min": 0.0, "max": 100.0},
                ],
            },
            {
                "id": "RL",
                "name": "RL Scheduler (PPO)",
                "type": "Adaptive",
                "description": "Trained PPO agent that learns an optimal scheduling policy. Falls back to SRTF if no model.",
                "parameters": [],
            },
        ]
    }


@router.post("/simulate", response_model=None)
async def simulate(
    request: SimulateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Dict[str, Any]:
    """
    Run a scheduling simulation.

    Returns full simulation result including Gantt chart,
    per-process timing data, and aggregate metrics.
    """
    try:
        processes = processes_from_schema(request.processes)
        result = await run_simulation(
            algorithm=request.algorithm,
            processes=processes,
            num_cores=request.num_cores,
            time_quantum=request.time_quantum,
            aging_interval=request.aging_interval,
            rl_model_path=settings.rl_model_path,
            db=db,
            workload_mode="custom",
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {e}")
