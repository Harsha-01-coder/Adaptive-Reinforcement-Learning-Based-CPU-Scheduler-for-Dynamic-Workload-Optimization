"""
Workload Generator

Produces realistic CPU scheduling workloads with configurable distributions.

Process types:
- cpu_bound: long burst times, low I/O wait, medium–high priority
- io_bound:  short burst times, frequent I/O, lower priority

Arrival patterns:
- Poisson arrivals (realistic)
- Uniform random
- Burst arrivals (cluster of processes at specific times)
"""

from __future__ import annotations

import csv
import io
import math
import random
from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np

try:
    from ..schedulers.base import Process
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from schedulers.base import Process


# ─────────────────────────────────────────────────────────────────────────────
#  Workload Configuration
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class WorkloadConfig:
    """Parameters controlling workload generation."""
    n_processes: int = 20
    cpu_bound_ratio: float = 0.6       # fraction of CPU-bound processes
    arrival_pattern: str = "poisson"   # 'poisson' | 'uniform' | 'burst'
    avg_arrival_rate: float = 0.5      # processes per time unit (Poisson λ)
    seed: Optional[int] = None

    # CPU-bound process parameters
    cpu_burst_min: float = 8.0
    cpu_burst_max: float = 40.0
    cpu_priority_min: int = 1
    cpu_priority_max: int = 5

    # I/O-bound process parameters
    io_burst_min: float = 2.0
    io_burst_max: float = 15.0
    io_priority_min: int = 3
    io_priority_max: int = 10


# ─────────────────────────────────────────────────────────────────────────────
#  Generator
# ─────────────────────────────────────────────────────────────────────────────

class WorkloadGenerator:
    """
    Generates synthetic CPU scheduling workloads.

    Usage:
        gen = WorkloadGenerator(seed=42)
        processes = gen.generate(mode="small")
    """

    PRESETS = {
        "small":  WorkloadConfig(n_processes=10, avg_arrival_rate=1.0, seed=42),
        "medium": WorkloadConfig(n_processes=30, avg_arrival_rate=0.5, seed=42),
        "large":  WorkloadConfig(n_processes=100, avg_arrival_rate=0.3, seed=42),
    }

    def __init__(self, seed: Optional[int] = None):
        self._base_seed = seed

    # ── Public API ────────────────────────────────────────────────────────────

    def generate(
        self,
        mode: str = "medium",
        n: Optional[int] = None,
        seed: Optional[int] = None,
    ) -> List[Process]:
        """
        Generate a workload.

        Args:
            mode: 'small' | 'medium' | 'large' | 'random'
            n: Override process count (used with mode='random').
            seed: Override random seed.

        Returns:
            List of Process objects sorted by arrival time.
        """
        if mode == "random":
            cfg = WorkloadConfig(
                n_processes=n or random.randint(15, 60),
                avg_arrival_rate=random.uniform(0.2, 1.5),
                seed=seed or self._base_seed,
            )
        elif mode in self.PRESETS:
            cfg = WorkloadConfig(**vars(self.PRESETS[mode]))
            if n is not None:
                cfg.n_processes = n
            if seed is not None:
                cfg.seed = seed
        else:
            raise ValueError(f"Unknown mode: {mode!r}. Choose from: small, medium, large, random")

        return self._build(cfg)

    def load_csv(self, csv_text: str) -> List[Process]:
        """
        Parse a CSV string into a list of Process objects.

        Expected columns (order-insensitive, case-insensitive):
            pid, arrival_time, burst_time, priority, process_type

        Missing columns default to sensible values.
        """
        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        # Normalize header names
        processes: List[Process] = []
        for i, row in enumerate(reader):
            norm = {k.strip().lower(): v.strip() for k, v in row.items()}
            try:
                p = Process(
                    pid=int(norm.get("pid", i + 1)),
                    arrival_time=float(norm.get("arrival_time", norm.get("arrival", 0))),
                    burst_time=float(norm.get("burst_time", norm.get("burst", 1))),
                    priority=int(norm.get("priority", 5)),
                    process_type=norm.get("process_type", norm.get("type", "cpu_bound")),
                )
                processes.append(p)
            except (ValueError, KeyError) as e:
                raise ValueError(f"Row {i+1} parse error: {e}. Row data: {row}") from e

        if not processes:
            raise ValueError("CSV file is empty or has no valid data rows.")

        return sorted(processes, key=lambda p: (p.arrival_time, p.pid))

    def to_csv(self, processes: List[Process]) -> str:
        """Serialize a process list to CSV text."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["pid", "arrival_time", "burst_time", "priority", "process_type"])
        for p in processes:
            writer.writerow([p.pid, p.arrival_time, p.burst_time, p.priority, p.process_type])
        return output.getvalue()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _build(self, cfg: WorkloadConfig) -> List[Process]:
        rng = np.random.default_rng(cfg.seed)

        n_cpu = int(cfg.n_processes * cfg.cpu_bound_ratio)
        n_io = cfg.n_processes - n_cpu

        arrival_times = self._generate_arrivals(cfg, rng)

        processes: List[Process] = []
        pid = 1

        # CPU-bound processes
        for _ in range(n_cpu):
            burst = float(rng.uniform(cfg.cpu_burst_min, cfg.cpu_burst_max))
            priority = int(rng.integers(cfg.cpu_priority_min, cfg.cpu_priority_max + 1))
            arrival = arrival_times[pid - 1]
            processes.append(Process(
                pid=pid,
                arrival_time=round(arrival, 2),
                burst_time=round(burst, 2),
                priority=priority,
                process_type="cpu_bound",
            ))
            pid += 1

        # I/O-bound processes
        for _ in range(n_io):
            burst = float(rng.uniform(cfg.io_burst_min, cfg.io_burst_max))
            priority = int(rng.integers(cfg.io_priority_min, cfg.io_priority_max + 1))
            arrival = arrival_times[pid - 1]
            processes.append(Process(
                pid=pid,
                arrival_time=round(arrival, 2),
                burst_time=round(burst, 2),
                priority=priority,
                process_type="io_bound",
            ))
            pid += 1

        # Sort by arrival time
        processes.sort(key=lambda p: (p.arrival_time, p.pid))
        # Re-assign sequential PIDs after sorting
        for i, p in enumerate(processes):
            p.pid = i + 1

        return processes

    def _generate_arrivals(self, cfg: WorkloadConfig, rng: np.random.Generator) -> List[float]:
        n = cfg.n_processes

        if cfg.arrival_pattern == "poisson":
            # Inter-arrival times ~ Exponential(λ)
            inter = rng.exponential(1.0 / cfg.avg_arrival_rate, size=n)
            arrivals = list(np.cumsum(inter))

        elif cfg.arrival_pattern == "uniform":
            span = n / cfg.avg_arrival_rate
            arrivals = sorted(rng.uniform(0, span, size=n).tolist())

        elif cfg.arrival_pattern == "burst":
            # Three bursts of processes
            arrivals = []
            cluster_times = [0.0, n / (2 * cfg.avg_arrival_rate), n / cfg.avg_arrival_rate]
            cluster_size = n // 3
            for j, t in enumerate(cluster_times):
                count = cluster_size if j < 2 else n - 2 * cluster_size
                jitter = rng.uniform(0, 2.0, size=count)
                arrivals.extend((t + jitter).tolist())
            arrivals.sort()

        else:
            # Fallback: uniform
            span = n / max(cfg.avg_arrival_rate, 0.01)
            arrivals = sorted(rng.uniform(0, span, size=n).tolist())

        return arrivals
