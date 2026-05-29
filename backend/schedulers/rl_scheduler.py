"""
RL Scheduler Wrapper

Wraps a trained Stable-Baselines3 PPO model to produce scheduling decisions.
Falls back to a heuristic (SRTF) if no trained model is available.
"""

from __future__ import annotations

import os
from typing import List, Optional, Tuple

import numpy as np

from .base import BaseScheduler, GanttEntry, Process, clone_processes

MAX_PROCESSES = 50
OBS_DIM = MAX_PROCESSES * 4 + 1   # remaining, waiting, priority, arrived + cpu_util


def _build_observation(
    ready: List[Process],
    current_time: float,
    total_cpu_busy: float,
) -> np.ndarray:
    """
    Build a fixed-length observation vector.

    Layout (per slot, padded to MAX_PROCESSES):
        [remaining_time, waiting_time, priority_norm, is_present]
    + [cpu_utilization]
    """
    obs = np.zeros(OBS_DIM, dtype=np.float32)
    cpu_util = total_cpu_busy / current_time if current_time > 0 else 0.0
    obs[-1] = cpu_util

    for i, p in enumerate(ready[:MAX_PROCESSES]):
        base = i * 4
        obs[base + 0] = p.remaining_time / 100.0
        obs[base + 1] = (current_time - p.arrival_time) / 100.0
        obs[base + 2] = p.priority / 10.0
        obs[base + 3] = 1.0   # is_present

    return obs


class RLScheduler(BaseScheduler):
    """
    Reinforcement Learning-based CPU Scheduler using PPO.

    Loads a pre-trained Stable-Baselines3 model if available.
    Falls back to SRTF heuristic when no model is found.
    """

    name = "RL (PPO)"

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or os.environ.get(
            "RL_MODEL_PATH", "rl_agent/models/ppo_cpu_scheduler"
        )
        self._model = None
        self._load_model()

    def _load_model(self) -> None:
        """Attempt to load the trained PPO model."""
        try:
            from stable_baselines3 import PPO
            path = self.model_path
            if not path.endswith(".zip"):
                path = path + ".zip"
            if os.path.exists(path):
                self._model = PPO.load(path)
                print(f"[RLScheduler] Loaded model from {path}")
            else:
                print(f"[RLScheduler] No model at {path} — using SRTF heuristic fallback.")
        except ImportError:
            print("[RLScheduler] stable_baselines3 not installed — using SRTF fallback.")

    @property
    def has_trained_model(self) -> bool:
        return self._model is not None

    def schedule(
        self,
        processes: List[Process],
        num_cores: int = 1,
    ) -> Tuple[List[Process], List[GanttEntry]]:
        if self._model is not None:
            return self._schedule_with_model(processes, num_cores)
        return self._schedule_heuristic(processes, num_cores)

    # ── PPO Model Inference ────────────────────────────────────────────────────

    def _schedule_with_model(
        self, processes: List[Process], num_cores: int
    ) -> Tuple[List[Process], List[GanttEntry]]:
        """
        Event-driven scheduling using trained PPO.

        At each decision point the model observes the ready queue and
        picks the next process index to run. We run that process for
        one time unit (granularity = 1) to allow preemption.
        """
        gantt: List[GanttEntry] = []
        arrivals = sorted(processes, key=lambda p: p.arrival_time)
        arrival_idx = 0
        n = len(processes)
        ready: List[Process] = []
        current_time = 0.0
        completed = 0
        total_cpu_busy = 0.0
        TIME_STEP = 1.0

        def enqueue(up_to: float) -> None:
            nonlocal arrival_idx
            while arrival_idx < n and arrivals[arrival_idx].arrival_time <= up_to:
                ready.append(arrivals[arrival_idx])
                arrival_idx += 1

        enqueue(0.0)
        prev_pid = -1

        while completed < n:
            enqueue(current_time)

            if not ready:
                next_t = arrivals[arrival_idx].arrival_time if arrival_idx < n else current_time + 1
                gantt.append(GanttEntry(pid=-1, start_time=current_time, end_time=next_t))
                current_time = next_t
                continue

            obs = _build_observation(ready, current_time, total_cpu_busy)
            action, _ = self._model.predict(obs, deterministic=True)
            action = int(action) % len(ready)

            p = ready[action]
            if p.start_time < 0:
                p.start_time = current_time
                p.response_time = current_time - p.arrival_time

            if prev_pid != p.pid and prev_pid != -1:
                p.context_switches += 1

            run_time = min(TIME_STEP, p.remaining_time)
            run_end = current_time + run_time

            if gantt and gantt[-1].pid == p.pid and gantt[-1].end_time == current_time:
                gantt[-1].end_time = run_end
            else:
                gantt.append(GanttEntry(pid=p.pid, start_time=current_time, end_time=run_end))

            total_cpu_busy += run_time
            p.remaining_time -= run_time
            prev_pid = p.pid
            current_time = run_end

            if p.remaining_time <= 1e-9:
                p.completion_time = current_time
                p.remaining_time = 0.0
                ready.remove(p)
                completed += 1

        return processes, gantt

    # ── SRTF Heuristic Fallback ───────────────────────────────────────────────

    def _schedule_heuristic(
        self, processes: List[Process], num_cores: int
    ) -> Tuple[List[Process], List[GanttEntry]]:
        """SRTF heuristic used when no trained model is available."""
        from .sjf import SJFScheduler
        srtf = SJFScheduler(preemptive=True)
        procs, gantt = srtf.schedule(processes, num_cores)
        return procs, gantt
