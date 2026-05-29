"""
Round Robin (RR) Scheduler — Preemptive

Each process receives a fixed CPU time quantum. If it doesn't complete
within the quantum, it is preempted and added to the back of the ready queue.

This is the most widely used general-purpose scheduling algorithm in practice
(used by Linux's CFS and Windows NT schedulers as a foundation).

Characteristics:
- Fair — no starvation.
- Good response time for short interactive processes.
- Throughput degrades with many context switches for small quanta.
- Performance is highly sensitive to quantum size.
"""

from __future__ import annotations

from collections import deque
from typing import List, Tuple

from .base import BaseScheduler, GanttEntry, Process


class RoundRobinScheduler(BaseScheduler):
    """
    Round Robin preemptive scheduler.

    Args:
        time_quantum: CPU time slice per process (default = 4 time units).
    """

    name = "Round Robin"

    def __init__(self, time_quantum: float = 4.0):
        self.time_quantum = time_quantum
        self.name = f"Round Robin (q={time_quantum})"

    def schedule(
        self,
        processes: List[Process],
        num_cores: int = 1,
    ) -> Tuple[List[Process], List[GanttEntry]]:
        gantt: List[GanttEntry] = []
        if not processes:
            return processes, gantt

        # Sort by arrival time for initial queueing
        arrivals = sorted(processes, key=lambda p: (p.arrival_time, p.pid))
        arrival_idx = 0
        n = len(processes)
        ready_queue: deque[Process] = deque()

        current_time = 0.0
        completed = 0
        prev_pid: int = -1

        def enqueue_new_arrivals(up_to: float) -> None:
            nonlocal arrival_idx
            while arrival_idx < n and arrivals[arrival_idx].arrival_time <= up_to:
                ready_queue.append(arrivals[arrival_idx])
                arrival_idx += 1

        # Seed initial arrivals at time 0
        enqueue_new_arrivals(0.0)

        while completed < n:
            if not ready_queue:
                # CPU idle — jump to next arrival
                if arrival_idx < n:
                    next_t = arrivals[arrival_idx].arrival_time
                    gantt.append(GanttEntry(pid=-1, start_time=current_time, end_time=next_t))
                    current_time = next_t
                    enqueue_new_arrivals(current_time)
                continue

            p = ready_queue.popleft()

            # First response
            if p.start_time < 0:
                p.start_time = current_time
                p.response_time = current_time - p.arrival_time

            # Context switch detection
            if prev_pid != -1 and prev_pid != p.pid:
                p.context_switches += 1

            # Determine how long this process runs this quantum
            run_time = min(self.time_quantum, p.remaining_time)
            run_end = current_time + run_time

            # Merge adjacent Gantt entries for the same process
            if gantt and gantt[-1].pid == p.pid and gantt[-1].end_time == current_time:
                gantt[-1].end_time = run_end
            else:
                gantt.append(GanttEntry(pid=p.pid, start_time=current_time, end_time=run_end))

            p.remaining_time -= run_time
            prev_pid = p.pid
            current_time = run_end

            # Enqueue processes that arrived during this quantum
            enqueue_new_arrivals(current_time)

            if p.remaining_time <= 1e-9:
                # Process finished
                p.completion_time = current_time
                p.remaining_time = 0.0
                completed += 1
            else:
                # Re-queue at the back
                ready_queue.append(p)

        return processes, gantt
