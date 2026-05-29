"""
Base scheduler abstractions and shared data types.

All schedulers operate on Process objects and return SimulationResult instances.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass, field
from typing import List, Optional


# ─────────────────────────────────────────────────────────────────────────────
#  Data Classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Process:
    """Represents a process submitted to the scheduler."""
    pid: int
    arrival_time: float
    burst_time: float
    priority: int = 1          # 1 = highest priority
    process_type: str = "cpu_bound"  # 'cpu_bound' | 'io_bound'

    # Runtime fields (set by scheduler)
    remaining_time: float = field(default=0.0, init=False)
    start_time: float = field(default=-1.0, init=False)
    completion_time: float = field(default=-1.0, init=False)
    waiting_time: float = field(default=0.0, init=False)
    turnaround_time: float = field(default=0.0, init=False)
    response_time: float = field(default=-1.0, init=False)
    context_switches: int = field(default=0, init=False)

    def __post_init__(self):
        self.remaining_time = self.burst_time

    def reset(self) -> None:
        """Reset runtime fields for re-use."""
        self.remaining_time = self.burst_time
        self.start_time = -1.0
        self.completion_time = -1.0
        self.waiting_time = 0.0
        self.turnaround_time = 0.0
        self.response_time = -1.0
        self.context_switches = 0


@dataclass
class GanttEntry:
    """A single segment on the Gantt chart."""
    pid: int           # -1 = CPU idle
    start_time: float
    end_time: float
    core_id: int = 0

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


@dataclass
class Metrics:
    """Aggregate performance metrics for a simulation run."""
    avg_waiting_time: float = 0.0
    avg_turnaround_time: float = 0.0
    avg_response_time: float = 0.0
    cpu_utilization: float = 0.0      # 0–100 %
    throughput: float = 0.0           # processes / time unit
    total_context_switches: int = 0
    fairness_score: float = 0.0       # Jain's fairness index 0–1
    total_idle_time: float = 0.0
    makespan: float = 0.0             # total simulation wall-clock time


@dataclass
class SimulationResult:
    """Complete result of a scheduling simulation."""
    algorithm: str
    processes: List[Process]
    gantt: List[GanttEntry]
    metrics: Metrics
    execution_time_ms: float = 0.0    # real time to run simulation

    def to_dict(self) -> dict:
        return {
            "algorithm": self.algorithm,
            "execution_time_ms": self.execution_time_ms,
            "metrics": {
                "avg_waiting_time": round(self.metrics.avg_waiting_time, 4),
                "avg_turnaround_time": round(self.metrics.avg_turnaround_time, 4),
                "avg_response_time": round(self.metrics.avg_response_time, 4),
                "cpu_utilization": round(self.metrics.cpu_utilization, 2),
                "throughput": round(self.metrics.throughput, 4),
                "total_context_switches": self.metrics.total_context_switches,
                "fairness_score": round(self.metrics.fairness_score, 4),
                "total_idle_time": round(self.metrics.total_idle_time, 4),
                "makespan": round(self.metrics.makespan, 4),
            },
            "processes": [
                {
                    "pid": p.pid,
                    "arrival_time": p.arrival_time,
                    "burst_time": p.burst_time,
                    "priority": p.priority,
                    "process_type": p.process_type,
                    "start_time": p.start_time,
                    "completion_time": p.completion_time,
                    "waiting_time": round(p.waiting_time, 4),
                    "turnaround_time": round(p.turnaround_time, 4),
                    "response_time": round(p.response_time, 4),
                    "context_switches": p.context_switches,
                }
                for p in self.processes
            ],
            "gantt": [
                {
                    "pid": g.pid,
                    "start_time": g.start_time,
                    "end_time": g.end_time,
                    "core_id": g.core_id,
                    "duration": round(g.duration, 4),
                }
                for g in self.gantt
            ],
        }


# ─────────────────────────────────────────────────────────────────────────────
#  Utility helpers
# ─────────────────────────────────────────────────────────────────────────────

def compute_metrics(processes: List[Process], gantt: List[GanttEntry]) -> Metrics:
    """
    Compute aggregate metrics from a completed simulation.
    Call this AFTER all processes have completion_time set.
    """
    n = len(processes)
    if n == 0:
        return Metrics()

    total_waiting = sum(p.waiting_time for p in processes)
    total_turnaround = sum(p.turnaround_time for p in processes)
    total_response = sum(p.response_time for p in processes if p.response_time >= 0)
    total_switches = sum(p.context_switches for p in processes)

    makespan = max(p.completion_time for p in processes)
    first_arrival = min(p.arrival_time for p in processes)
    sim_duration = makespan - first_arrival

    # CPU utilization: busy time / total time
    idle_time = sum(e.duration for e in gantt if e.pid == -1)
    total_time = sum(e.duration for e in gantt)
    cpu_util = (1.0 - idle_time / total_time) * 100.0 if total_time > 0 else 0.0

    # Throughput: processes per unit time
    throughput = n / sim_duration if sim_duration > 0 else 0.0

    # Jain's Fairness Index on waiting times
    wt = [p.waiting_time for p in processes]
    sum_wt = sum(wt)
    sum_wt_sq = sum(w ** 2 for w in wt)
    fairness = (sum_wt ** 2) / (n * sum_wt_sq) if sum_wt_sq > 0 else 1.0

    return Metrics(
        avg_waiting_time=total_waiting / n,
        avg_turnaround_time=total_turnaround / n,
        avg_response_time=total_response / n if n > 0 else 0.0,
        cpu_utilization=cpu_util,
        throughput=throughput,
        total_context_switches=total_switches,
        fairness_score=fairness,
        total_idle_time=idle_time,
        makespan=makespan,
    )


def clone_processes(processes: List[Process]) -> List[Process]:
    """Deep-copy a process list and reset runtime fields."""
    cloned = deepcopy(processes)
    for p in cloned:
        p.reset()
    return cloned


# ─────────────────────────────────────────────────────────────────────────────
#  Abstract Base Scheduler
# ─────────────────────────────────────────────────────────────────────────────

class BaseScheduler(ABC):
    """
    Abstract base class for all CPU scheduling algorithms.

    Subclasses implement `schedule()` which takes a process list
    and returns a SimulationResult.
    """

    name: str = "Base"

    def run(
        self,
        processes: List[Process],
        num_cores: int = 1,
    ) -> SimulationResult:
        """
        Public entry point. Clones processes, runs the scheduling
        algorithm, computes metrics, and wraps in SimulationResult.
        """
        procs = clone_processes(processes)
        t0 = time.perf_counter()
        scheduled_procs, gantt = self.schedule(procs, num_cores)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        # Compute final waiting / turnaround / response times
        for p in scheduled_procs:
            p.turnaround_time = p.completion_time - p.arrival_time
            p.waiting_time = p.turnaround_time - p.burst_time
            if p.waiting_time < 0:
                p.waiting_time = 0.0
            if p.response_time < 0:
                p.response_time = p.waiting_time

        metrics = compute_metrics(scheduled_procs, gantt)

        return SimulationResult(
            algorithm=self.name,
            processes=scheduled_procs,
            gantt=gantt,
            metrics=metrics,
            execution_time_ms=elapsed_ms,
        )

    @abstractmethod
    def schedule(
        self,
        processes: List[Process],
        num_cores: int,
    ) -> tuple[List[Process], List[GanttEntry]]:
        """
        Core scheduling logic.

        Args:
            processes: Pre-cloned, reset processes.
            num_cores: Number of CPU cores to simulate.

        Returns:
            (processes_with_times_set, gantt_entries)
        """
        ...
