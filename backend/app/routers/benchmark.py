"""Benchmark comparison API routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas import BenchmarkRequest
from ..services.simulation_service import processes_from_schema, run_benchmark
from ..config import get_settings

router = APIRouter(prefix="/api/benchmark", tags=["Benchmark"])
settings = get_settings()


@router.post("/run")
async def run_benchmark_endpoint(
    request: BenchmarkRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Run all scheduling algorithms on the same workload.

    Returns per-algorithm metrics plus statistical rankings.
    The algorithm with the lowest average waiting time wins.
    """
    try:
        processes = processes_from_schema(request.processes)
        result = await run_benchmark(
            processes=processes,
            num_cores=request.num_cores,
            include_rl=request.include_rl,
            time_quantum=request.time_quantum,
            rl_model_path=settings.rl_model_path,
            db=db,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmark error: {e}")
