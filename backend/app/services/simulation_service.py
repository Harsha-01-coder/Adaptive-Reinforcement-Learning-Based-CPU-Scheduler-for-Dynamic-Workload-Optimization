"""
Simulation Service

Bridges FastAPI routers with scheduling algorithms and database persistence.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

try:
    from ...schedulers import (
        FCFSScheduler,
        PriorityScheduler,
        Process,
        RLScheduler,
        RoundRobinScheduler,
        SJFScheduler,
        SimulationResult,
    )
    from ..models import SimulationRecord
    from ..schemas import ProcessIn
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from schedulers import (
        FCFSScheduler, PriorityScheduler, Process, RLScheduler,
        RoundRobinScheduler, SJFScheduler, SimulationResult,
    )
    from app.models import SimulationRecord
    from app.schemas import ProcessIn


def processes_from_schema(process_list: List[ProcessIn]) -> List[Process]:
    """Convert Pydantic ProcessIn list → Process domain objects."""
    return [
        Process(
            pid=p.pid,
            arrival_time=p.arrival_time,
            burst_time=p.burst_time,
            priority=p.priority,
            process_type=p.process_type,
        )
        for p in process_list
    ]


def get_scheduler(
    algorithm: str,
    time_quantum: float = 4.0,
    aging_interval: float = 10.0,
    rl_model_path: Optional[str] = None,
):
    """Factory: return the correct scheduler for the given algorithm name."""
    mapping = {
        "FCFS": lambda: FCFSScheduler(),
        "SJF": lambda: SJFScheduler(preemptive=False),
        "SRTF": lambda: SJFScheduler(preemptive=True),
        "Round Robin": lambda: RoundRobinScheduler(time_quantum=time_quantum),
        "Priority": lambda: PriorityScheduler(aging_interval=aging_interval),
        "RL": lambda: RLScheduler(model_path=rl_model_path),
    }
    if algorithm not in mapping:
        raise ValueError(f"Unknown algorithm: {algorithm!r}")
    return mapping[algorithm]()


async def run_simulation(
    algorithm: str,
    processes: List[Process],
    num_cores: int = 1,
    time_quantum: float = 4.0,
    aging_interval: float = 10.0,
    rl_model_path: Optional[str] = None,
    db: Optional[AsyncSession] = None,
    workload_mode: str = "custom",
) -> Dict[str, Any]:
    """
    Run a scheduling simulation and optionally persist the result.

    Returns the simulation result as a dictionary.
    """
    scheduler = get_scheduler(algorithm, time_quantum, aging_interval, rl_model_path)
    result: SimulationResult = scheduler.run(processes, num_cores=num_cores)
    sim_id = str(uuid.uuid4())
    result_dict = result.to_dict()
    result_dict["simulation_id"] = sim_id

    # Persist to database
    if db is not None:
        record = SimulationRecord(
            id=sim_id,
            algorithm=result.algorithm,
            workload_mode=workload_mode,
            n_processes=len(processes),
            num_cores=num_cores,
            avg_waiting_time=result.metrics.avg_waiting_time,
            avg_turnaround_time=result.metrics.avg_turnaround_time,
            avg_response_time=result.metrics.avg_response_time,
            cpu_utilization=result.metrics.cpu_utilization,
            throughput=result.metrics.throughput,
            context_switches=result.metrics.total_context_switches,
            fairness_score=result.metrics.fairness_score,
            result_json=result_dict,
        )
        db.add(record)
        await db.commit()

    return result_dict


async def run_benchmark(
    processes: List[Process],
    num_cores: int = 1,
    include_rl: bool = False,
    time_quantum: float = 4.0,
    rl_model_path: Optional[str] = None,
    db: Optional[AsyncSession] = None,
) -> Dict[str, Any]:
    """
    Run all algorithms on the same workload and return a comparison.
    """
    algorithms = ["FCFS", "SJF", "SRTF", "Round Robin", "Priority"]
    if include_rl:
        algorithms.append("RL")

    results = []
    for algo in algorithms:
        try:
            r = await run_simulation(
                algorithm=algo,
                processes=processes,
                num_cores=num_cores,
                time_quantum=time_quantum,
                rl_model_path=rl_model_path,
            )
            results.append(r)
        except Exception as e:
            results.append({"algorithm": algo, "error": str(e)})

    # Rank by avg waiting time (lower = better)
    valid = [r for r in results if "error" not in r]
    ranked = sorted(valid, key=lambda r: r["metrics"]["avg_waiting_time"])
    rankings = {r["algorithm"]: i + 1 for i, r in enumerate(ranked)}
    best = ranked[0]["algorithm"] if ranked else "N/A"

    return {
        "benchmark_id": str(uuid.uuid4()),
        "n_processes": len(processes),
        "results": results,
        "rankings": rankings,
        "best_algorithm": best,
    }
