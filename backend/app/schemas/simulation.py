"""
Pydantic schemas for request/response validation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────────────────────────────────────────
#  Process
# ─────────────────────────────────────────────────────────────────────────────

class ProcessIn(BaseModel):
    pid: int = Field(..., ge=1)
    arrival_time: float = Field(..., ge=0)
    burst_time: float = Field(..., gt=0)
    priority: int = Field(default=5, ge=1, le=10)
    process_type: Literal["cpu_bound", "io_bound"] = "cpu_bound"


class ProcessOut(ProcessIn):
    start_time: float
    completion_time: float
    waiting_time: float
    turnaround_time: float
    response_time: float
    context_switches: int


# ─────────────────────────────────────────────────────────────────────────────
#  Gantt
# ─────────────────────────────────────────────────────────────────────────────

class GanttEntryOut(BaseModel):
    pid: int
    start_time: float
    end_time: float
    duration: float
    core_id: int = 0


# ─────────────────────────────────────────────────────────────────────────────
#  Metrics
# ─────────────────────────────────────────────────────────────────────────────

class MetricsOut(BaseModel):
    avg_waiting_time: float
    avg_turnaround_time: float
    avg_response_time: float
    cpu_utilization: float
    throughput: float
    total_context_switches: int
    fairness_score: float
    total_idle_time: float
    makespan: float


# ─────────────────────────────────────────────────────────────────────────────
#  Simulation
# ─────────────────────────────────────────────────────────────────────────────

class SimulateRequest(BaseModel):
    algorithm: Literal["FCFS", "SJF", "SRTF", "Round Robin", "Priority", "RL"] = "FCFS"
    processes: List[ProcessIn]
    num_cores: int = Field(default=1, ge=1, le=8)
    time_quantum: float = Field(default=4.0, gt=0)
    aging_interval: float = Field(default=10.0, ge=0)

    @field_validator("processes")
    @classmethod
    def validate_processes(cls, v: List[ProcessIn]) -> List[ProcessIn]:
        if not v:
            raise ValueError("Process list cannot be empty")
        if len(v) > 200:
            raise ValueError("Maximum 200 processes per simulation")
        return v


class SimulationResponse(BaseModel):
    simulation_id: str
    algorithm: str
    execution_time_ms: float
    metrics: MetricsOut
    processes: List[Dict[str, Any]]
    gantt: List[Dict[str, Any]]


# ─────────────────────────────────────────────────────────────────────────────
#  Workload
# ─────────────────────────────────────────────────────────────────────────────

class WorkloadResponse(BaseModel):
    mode: str
    n_processes: int
    processes: List[Dict[str, Any]]


# ─────────────────────────────────────────────────────────────────────────────
#  Benchmark
# ─────────────────────────────────────────────────────────────────────────────

class BenchmarkRequest(BaseModel):
    processes: List[ProcessIn]
    num_cores: int = Field(default=1, ge=1, le=8)
    include_rl: bool = False
    time_quantum: float = Field(default=4.0, gt=0)


class AlgorithmResult(BaseModel):
    algorithm: str
    metrics: MetricsOut
    execution_time_ms: float
    rank: int = 0


class BenchmarkResponse(BaseModel):
    benchmark_id: str
    n_processes: int
    results: List[AlgorithmResult]
    rankings: Dict[str, int]
    best_algorithm: str


# ─────────────────────────────────────────────────────────────────────────────
#  RL Agent
# ─────────────────────────────────────────────────────────────────────────────

class TrainRequest(BaseModel):
    timesteps: int = Field(default=100_000, ge=1_000, le=2_000_000)
    n_envs: int = Field(default=2, ge=1, le=8)
    workload_mode: Literal["small", "medium", "large"] = "medium"
    seed: int = 42


class TrainStatusResponse(BaseModel):
    status: Literal["idle", "training", "completed", "failed"]
    progress_pct: float = 0.0
    current_timestep: int = 0
    total_timesteps: int = 0
    mean_reward: float = 0.0
    reward_log: Dict[str, List] = Field(default_factory=dict)
    error: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
#  Export
# ─────────────────────────────────────────────────────────────────────────────

class ExportRequest(BaseModel):
    simulation_id: str
    format: Literal["csv", "pdf"] = "csv"
