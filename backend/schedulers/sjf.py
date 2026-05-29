"""
Shortest Job First (SJF) Scheduler — Non-Preemptive (default)
                                     Preemptive variant: SRTF

Non-Preemptive SJF:
    When CPU becomes free, pick the ready process with the smallest burst time.
    Optimal average waiting time for a given set of non-preemptive jobs.

Preemptive SJF (SRTF — Shortest Remaining Time First):
    At each time unit, if a newly arrived process has a shorter remaining
    time than the currently running process, preempt and switch.

Time Complexity: O(n^2) worst-case due to repeated priority-queue ops.
"""

from __future__ import annotations

import heapq
from typing import List, Tuple

from .base import BaseScheduler, GanttEntry, Process


class SJFScheduler(BaseScheduler):
    """
    Shortest Job First — Non-Preemptive.

    Characteristics:
    - Optimal average waiting time (non-preemptive batch).
    - Can cause starvation for long processes in heavy workloads.
    - Requires knowledge of burst time (oracle assumption in simulation).
    """

    name = "SJF"

    def __init__(self, preemptive: bool = False):
        self.preemptive = preemptive
        if preemptive:
            self.name = "SRTF"

    def schedule(
        self,
        processes: List[Process],
        num_cores: int = 1,
    ) -> Tuple[List[Process], List[GanttEntry]]:
        if self.preemptive:
            return self._srtf(processes, num_cores)
        return self._sjf(processes, num_cores)

    # ── Non-Preemptive SJF ────────────────────────────────────────────────────

    def _sjf(
        self,
        processes: List[Process],
        num_cores: int,
    ) -> Tuple[List[Process], List[GanttEntry]]:
        gantt: List[GanttEntry] = []
        if not processes:
            return processes, gantt

        not_arrived = sorted(processes, key=lambda p: (p.arrival_time, p.burst_time, p.pid))
        # Min-heap: (burst_time, pid, process)
        ready_heap: list = []
        current_time = 0.0
        idx = 0
        completed = 0
        n = len(processes)

        while completed < n:
            # Enqueue all processes that have arrived by current_time
            while idx < len(not_arrived) and not_arrived[idx].arrival_time <= current_time:
                p = not_arrived[idx]
                heapq.heappush(ready_heap, (p.burst_time, p.pid, p))
                idx += 1

            if not ready_heap:
                # CPU idle — jump to next arrival
                if idx < len(not_arrived):
                    next_arrival = not_arrived[idx].arrival_time
                    gantt.append(GanttEntry(pid=-1, start_time=current_time, end_time=next_arrival))
                    current_time = next_arrival
                continue

            _, _, p = heapq.heappop(ready_heap)

            if p.start_time < 0:
                p.start_time = current_time
                p.response_time = current_time - p.arrival_time

            run_end = current_time + p.remaining_time
            gantt.append(GanttEntry(pid=p.pid, start_time=current_time, end_time=run_end))
            p.completion_time = run_end
            p.remaining_time = 0.0
            current_time = run_end
            completed += 1

        return processes, gantt

    # ── Preemptive SRTF ───────────────────────────────────────────────────────

    def _srtf(
        self,
        processes: List[Process],
        num_cores: int,
    ) -> Tuple[List[Process], List[GanttEntry]]:
        """
        Shortest Remaining Time First — event-driven simulation.
        Events: arrivals and current process completion.
        """
        gantt: List[GanttEntry] = []
        if not processes:
            return processes, gantt

        # Sort arrivals
        arrivals = sorted(processes, key=lambda p: p.arrival_time)
        current_time = 0.0
        current_proc: Process | None = None
        last_switch_time = 0.0
        ready_heap: list = []  # (remaining_time, pid, proc)
        idx = 0
        n = len(processes)
        completed = 0

        def enqueue_arrivals(up_to: float):
            nonlocal idx
            while idx < n and arrivals[idx].arrival_time <= up_to:
                p = arrivals[idx]
                heapq.heappush(ready_heap, (p.remaining_time, p.pid, p))
                idx += 1

        while completed < n:
            enqueue_arrivals(current_time)

            if not ready_heap and current_proc is None:
                # Idle — jump to next arrival
                if idx < n:
                    next_t = arrivals[idx].arrival_time
                    gantt.append(GanttEntry(pid=-1, start_time=current_time, end_time=next_t))
                    current_time = next_t
                continue

            if current_proc is not None:
                heapq.heappush(ready_heap, (current_proc.remaining_time, current_proc.pid, current_proc))
                current_proc = None

            _, _, p = heapq.heappop(ready_heap)

            if p.start_time < 0:
                p.start_time = current_time
                p.response_time = current_time - p.arrival_time

            # Determine next event: either next arrival or this process finishing
            next_arrival = arrivals[idx].arrival_time if idx < n else float("inf")
            time_to_finish = p.remaining_time
            run_until = min(current_time + time_to_finish, next_arrival)

            if gantt and gantt[-1].pid == p.pid and gantt[-1].end_time == current_time:
                gantt[-1].end_time = run_until
            else:
                gantt.append(GanttEntry(pid=p.pid, start_time=current_time, end_time=run_until))
                if current_proc is not None and current_proc.pid != p.pid:
                    p.context_switches += 1

            elapsed = run_until - current_time
            p.remaining_time -= elapsed
            current_time = run_until

            if p.remaining_time <= 1e-9:
                p.completion_time = current_time
                p.remaining_time = 0.0
                completed += 1
                current_proc = None
            else:
                current_proc = p

        return processes, gantt
