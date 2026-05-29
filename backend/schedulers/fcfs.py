"""
First Come First Serve (FCFS) Scheduler — Non-Preemptive

Processes are executed in the order they arrive. Simple but can suffer
from the "convoy effect" where short jobs wait behind long ones.

Time Complexity: O(n log n) for sorting, O(n) for scheduling.
"""

from __future__ import annotations

import heapq
from typing import List, Tuple

from .base import BaseScheduler, GanttEntry, Process


class FCFSScheduler(BaseScheduler):
    """
    First Come First Serve (FCFS) — Non-Preemptive.

    Characteristics:
    - Simple, fair ordering by arrival time.
    - No starvation (every process eventually runs).
    - Poor avg. waiting time for mixed burst-time workloads.
    - Convoy effect: long processes block short ones.
    """

    name = "FCFS"

    def schedule(
        self,
        processes: List[Process],
        num_cores: int = 1,
    ) -> Tuple[List[Process], List[GanttEntry]]:
        gantt: List[GanttEntry] = []

        if not processes:
            return processes, gantt

        # Sort by arrival time (stable — preserves submission order on ties)
        queue = sorted(processes, key=lambda p: (p.arrival_time, p.pid))
        current_time = 0.0

        for p in queue:
            # Advance clock if CPU is idle waiting for the next arrival
            if current_time < p.arrival_time:
                gantt.append(GanttEntry(pid=-1, start_time=current_time, end_time=p.arrival_time))
                current_time = p.arrival_time

            # First response
            p.start_time = current_time
            p.response_time = current_time - p.arrival_time

            # Execute process to completion (non-preemptive)
            run_end = current_time + p.burst_time
            gantt.append(GanttEntry(pid=p.pid, start_time=current_time, end_time=run_end))

            p.completion_time = run_end
            p.remaining_time = 0.0
            current_time = run_end

        return processes, gantt
