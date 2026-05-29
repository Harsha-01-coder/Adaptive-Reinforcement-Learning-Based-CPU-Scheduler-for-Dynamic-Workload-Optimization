"""
Custom Gymnasium Environment for CPU Scheduling RL Agent

The RL agent learns a scheduling policy by interacting with this environment.

State Space (Observation):
    Flattened vector of size MAX_PROCESSES × 5 + 2:
    For each process slot (padded to MAX_PROCESSES):
        [remaining_time_norm, waiting_time_norm, priority_norm,
         is_present, process_type_norm]
    Global stats:
        [cpu_utilization, n_ready_norm]

Action Space:
    Discrete(MAX_PROCESSES) — index of process to schedule next.
    Invalid actions (empty slots) are masked to the least-waiting process.

Reward Signal:
    At each step after a scheduling decision:
    R = - w1 * Δwaiting_time_avg
        - w2 * context_switch_penalty
        + w3 * cpu_utilization
        - w4 * starvation_penalty
        + w5 * completion_bonus (when a process finishes)
"""

from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from schedulers.base import Process
from workload_generator.generator import WorkloadGenerator

# ── Constants ─────────────────────────────────────────────────────────────────

MAX_PROCESSES = 50
OBS_DIM = MAX_PROCESSES * 5 + 2
TIME_STEP = 1.0          # simulation granularity (time units per step)
MAX_TIME = 5000.0        # episode time limit

# Reward weights
W_WAITING = 0.4
W_CONTEXT_SWITCH = 0.1
W_CPU_UTIL = 0.2
W_STARVATION = 0.2
W_COMPLETION = 0.1


class CPUSchedulerEnv(gym.Env):
    """
    OpenAI Gymnasium environment for the CPU scheduling problem.

    Each episode simulates a batch of processes arriving over time.
    The agent selects which ready process to run at each decision point.
    """

    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        workload_mode: str = "medium",
        n_processes: Optional[int] = None,
        seed: Optional[int] = None,
    ):
        super().__init__()
        self.workload_mode = workload_mode
        self.n_processes = n_processes
        self._gen = WorkloadGenerator(seed=seed)

        # Spaces
        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(OBS_DIM,), dtype=np.float32
        )
        self.action_space = spaces.Discrete(MAX_PROCESSES)

        # Episode state (initialized in reset)
        self._processes: List[Process] = []
        self._ready: List[Process] = []
        self._arrival_queue: List[Process] = []
        self._arrival_idx: int = 0
        self._current_time: float = 0.0
        self._total_cpu_busy: float = 0.0
        self._completed: int = 0
        self._prev_pid: int = -1
        self._total_waiting_last: float = 0.0
        self._context_switches: int = 0

    # ── Gymnasium Interface ───────────────────────────────────────────────────

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[Dict] = None,
    ) -> Tuple[np.ndarray, Dict]:
        super().reset(seed=seed)

        # Generate a fresh workload
        self._processes = self._gen.generate(
            mode=self.workload_mode,
            n=self.n_processes,
            seed=seed,
        )
        n = len(self._processes)
        self._arrival_queue = sorted(self._processes, key=lambda p: p.arrival_time)
        self._arrival_idx = 0
        self._ready = []
        self._current_time = 0.0
        self._total_cpu_busy = 0.0
        self._completed = 0
        self._prev_pid = -1
        self._total_waiting_last = 0.0
        self._context_switches = 0

        # Enqueue initial arrivals
        self._enqueue_arrivals(0.0)

        obs = self._get_obs()
        return obs, {"n_processes": n}

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """
        Execute one scheduling decision.

        Args:
            action: Index into ready queue (clamped to valid range).

        Returns:
            obs, reward, terminated, truncated, info
        """
        n_ready = len(self._ready)
        if n_ready == 0:
            # Nothing to schedule; advance time
            if self._arrival_idx < len(self._arrival_queue):
                next_t = self._arrival_queue[self._arrival_idx].arrival_time
                self._current_time = next_t
                self._enqueue_arrivals(next_t)
            obs = self._get_obs()
            return obs, 0.0, self._is_done(), False, self._info()

        # Clamp invalid actions to the longest-waiting process
        valid_action = int(action) % n_ready

        p = self._ready[valid_action]

        # Context switch detection
        if self._prev_pid != -1 and self._prev_pid != p.pid:
            self._context_switches += 1
            ctx_penalty = W_CONTEXT_SWITCH
        else:
            ctx_penalty = 0.0

        # First response
        if p.start_time < 0:
            p.start_time = self._current_time
            p.response_time = self._current_time - p.arrival_time

        # Run for TIME_STEP
        run_time = min(TIME_STEP, p.remaining_time)
        self._current_time += run_time
        self._total_cpu_busy += run_time
        p.remaining_time -= run_time
        self._prev_pid = p.pid

        # Enqueue new arrivals
        self._enqueue_arrivals(self._current_time)

        # Compute current avg waiting time
        total_waiting = sum(
            (self._current_time - q.arrival_time - (q.burst_time - q.remaining_time))
            for q in self._ready if q.remaining_time > 0
        )
        avg_waiting = total_waiting / max(len(self._ready), 1)

        # Starvation penalty: max waiting time
        if self._ready:
            max_wait = max(self._current_time - q.arrival_time for q in self._ready)
            starvation_penalty = W_STARVATION * min(max_wait / 100.0, 1.0)
        else:
            starvation_penalty = 0.0

        # CPU utilization reward
        cpu_util = self._total_cpu_busy / self._current_time if self._current_time > 0 else 0.0
        util_reward = W_CPU_UTIL * cpu_util

        # Completion bonus
        completion_bonus = 0.0
        if p.remaining_time <= 1e-9:
            p.completion_time = self._current_time
            p.remaining_time = 0.0
            p.turnaround_time = p.completion_time - p.arrival_time
            p.waiting_time = max(0.0, p.turnaround_time - p.burst_time)
            self._ready.remove(p)
            self._completed += 1
            completion_bonus = W_COMPLETION

        # Waiting time improvement reward
        waiting_delta = self._total_waiting_last - avg_waiting
        waiting_reward = W_WAITING * waiting_delta / 10.0
        self._total_waiting_last = avg_waiting

        # Total reward
        reward = (
            waiting_reward
            - ctx_penalty
            + util_reward
            - starvation_penalty
            + completion_bonus
        )

        terminated = self._is_done()
        truncated = self._current_time > MAX_TIME

        obs = self._get_obs()
        return obs, float(reward), terminated, truncated, self._info()

    def render(self) -> None:
        print(
            f"t={self._current_time:.1f} | ready={len(self._ready)} | "
            f"done={self._completed}/{len(self._processes)} | "
            f"switches={self._context_switches}"
        )

    # ── Private Helpers ───────────────────────────────────────────────────────

    def _enqueue_arrivals(self, up_to: float) -> None:
        while (
            self._arrival_idx < len(self._arrival_queue)
            and self._arrival_queue[self._arrival_idx].arrival_time <= up_to
        ):
            self._ready.append(self._arrival_queue[self._arrival_idx])
            self._arrival_idx += 1

    def _get_obs(self) -> np.ndarray:
        obs = np.zeros(OBS_DIM, dtype=np.float32)

        # Per-process features
        for i, p in enumerate(self._ready[:MAX_PROCESSES]):
            base = i * 5
            obs[base + 0] = min(p.remaining_time / 100.0, 1.0)
            obs[base + 1] = min((self._current_time - p.arrival_time) / 100.0, 1.0)
            obs[base + 2] = p.priority / 10.0
            obs[base + 3] = 1.0   # is_present
            obs[base + 4] = 1.0 if p.process_type == "cpu_bound" else 0.0

        # Global stats
        obs[-2] = self._total_cpu_busy / self._current_time if self._current_time > 0 else 0.0
        obs[-1] = min(len(self._ready) / MAX_PROCESSES, 1.0)

        return obs

    def _is_done(self) -> bool:
        return (
            self._completed >= len(self._processes)
            and self._arrival_idx >= len(self._arrival_queue)
            and len(self._ready) == 0
        )

    def _info(self) -> Dict[str, Any]:
        return {
            "completed": self._completed,
            "total": len(self._processes),
            "current_time": self._current_time,
            "context_switches": self._context_switches,
            "cpu_utilization": (
                self._total_cpu_busy / self._current_time
                if self._current_time > 0 else 0.0
            ),
        }
