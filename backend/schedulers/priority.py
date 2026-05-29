"""
Priority Scheduling — Non-Preemptive with Aging (Starvation Prevention)

Non-preemptive: when the CPU becomes free, pick the highest-priority (lowest
priority number) process from the ready queue.

Aging: priority number decreases by 1 for every `aging_interval` time units
a process waits, ensuring no process starves indefinitely.

Characteristics:
- Good for real-time and mixed-criticality workloads.
- Suffers from starvation without aging.
- Aging transforms it into a near-fair scheduler over time.
"""

from __future__ import annotations

import heapq
from typing import List, Tuple

from .base import BaseScheduler, GanttEntry, Process


class PriorityScheduler(BaseScheduler):
    """
    Non-preemptive Priority Scheduling with optional aging.

    Lower priority number = higher priority (as in UNIX nice values).

    Args:
        aging_interval: Time units after which a waiting process's priority
                        improves by 1 level (0 to disable aging).
    """

    name = "Priority"

    def __init__(self, aging_interval: float = 10.0):
        self.aging_interval = aging_interval

    def schedule(
        self,
        processes: List[Process],
        num_cores: int = 1,
    ) -> Tuple[List[Process], List[GanttEntry]]:
        gantt: List[GanttEntry] = []
        if not processes:
            return processes, gantt

        # Sort by arrival time initially
        arrivals = sorted(processes, key=lambda p: (p.arrival_time, p.priority, p.pid))
        arrival_idx = 0
        n = len(processes)
        current_time = 0.0
        completed = 0

        # Effective priorities (aged) tracked separately
        effective_priority: dict[int, float] = {p.pid: float(p.priority) for p in processes}
        # Track when each process entered the ready queue
        queue_entry_time: dict[int, float] = {}

        # Min-heap: (effective_priority, pid, process)
        ready_heap: list = []

        def enqueue_arrivals(up_to: float) -> None:
            nonlocal arrival_idx
            while arrival_idx < n and arrivals[arrival_idx].arrival_time <= up_to:
                p = arrivals[arrival_idx]
                queue_entry_time[p.pid] = up_to
                heapq.heappush(ready_heap, (effective_priority[p.pid], p.pid, p))
                arrival_idx += 1

        enqueue_arrivals(0.0)

        while completed < n:
            # Apply aging: rebuild heap with updated priorities if needed
            if self.aging_interval > 0 and ready_heap:
                aged: list = []
                for ep, pid, p in ready_heap:
                    wait = current_time - queue_entry_time.get(pid, current_time)
                    age_levels = int(wait / self.aging_interval)
                    new_prio = max(1.0, float(p.priority) - age_levels)
                    effective_priority[pid] = new_prio
                    aged.append((new_prio, pid, p))
                heapq.heapify(aged)
                ready_heap = aged

            if not ready_heap:
                if arrival_idx < n:
                    next_t = arrivals[arrival_idx].arrival_time
                    gantt.append(GanttEntry(pid=-1, start_time=current_time, end_time=next_t))
                    current_time = next_t
                    enqueue_arrivals(current_time)
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

            # Enqueue any new arrivals
            enqueue_arrivals(current_time)

        return processes, gantt
