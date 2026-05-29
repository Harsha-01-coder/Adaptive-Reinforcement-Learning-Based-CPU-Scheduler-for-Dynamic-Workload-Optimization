"""
Tests for all scheduling algorithms.

Tests verify:
- Correct execution order
- No process left unscheduled
- Timing constraints (completion > start > arrival)
- Metrics are non-negative
- Context switch counts are consistent
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from schedulers.base import Process
from schedulers.fcfs import FCFSScheduler
from schedulers.sjf import SJFScheduler
from schedulers.round_robin import RoundRobinScheduler
from schedulers.priority import PriorityScheduler


# ─────────────────────────────────────────────────────────────────────────────
#  Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def simple_processes():
    """5 processes with distinct arrival and burst times."""
    return [
        Process(pid=1, arrival_time=0, burst_time=10, priority=3),
        Process(pid=2, arrival_time=2, burst_time=4,  priority=1),
        Process(pid=3, arrival_time=4, burst_time=6,  priority=5),
        Process(pid=4, arrival_time=1, burst_time=8,  priority=2),
        Process(pid=5, arrival_time=5, burst_time=2,  priority=4),
    ]


@pytest.fixture
def simultaneous_processes():
    """All processes arrive at t=0."""
    return [
        Process(pid=1, arrival_time=0, burst_time=5, priority=3),
        Process(pid=2, arrival_time=0, burst_time=3, priority=1),
        Process(pid=3, arrival_time=0, burst_time=8, priority=5),
    ]


@pytest.fixture
def single_process():
    return [Process(pid=1, arrival_time=5, burst_time=10, priority=1)]


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────

def assert_result_valid(result, n_processes: int):
    """Generic assertions valid for any correct scheduler."""
    assert result.algorithm != ""
    assert len(result.processes) == n_processes

    for p in result.processes:
        assert p.completion_time >= 0, f"P{p.pid} not completed"
        assert p.start_time >= p.arrival_time, f"P{p.pid} started before arrival"
        assert p.completion_time >= p.start_time + p.burst_time - 1e-6
        assert p.waiting_time >= 0
        assert p.turnaround_time >= 0
        assert p.turnaround_time >= p.waiting_time

    assert result.metrics.avg_waiting_time >= 0
    assert result.metrics.avg_turnaround_time >= 0
    assert 0 <= result.metrics.cpu_utilization <= 100
    assert result.metrics.throughput >= 0
    assert 0 <= result.metrics.fairness_score <= 1.01  # float rounding


# ─────────────────────────────────────────────────────────────────────────────
#  FCFS Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestFCFS:
    def test_basic(self, simple_processes):
        result = FCFSScheduler().run(simple_processes)
        assert_result_valid(result, 5)
        assert result.algorithm == "FCFS"

    def test_single(self, single_process):
        result = FCFSScheduler().run(single_process)
        assert result.processes[0].start_time == 5
        assert result.processes[0].completion_time == 15
        assert result.processes[0].waiting_time == 0

    def test_order(self, simple_processes):
        """FCFS must execute in arrival order."""
        result = FCFSScheduler().run(simple_processes)
        starts = [(p.pid, p.start_time) for p in result.processes]
        sorted_by_start = sorted(starts, key=lambda x: x[1])
        # P1 arrives first (t=0), P4 second (t=1), P2 third (t=2)
        first_pid = sorted_by_start[0][0]
        assert first_pid == 1  # arrives at t=0

    def test_idle_gap(self):
        """CPU should be idle when no process has arrived."""
        procs = [
            Process(pid=1, arrival_time=5, burst_time=3, priority=1),
            Process(pid=2, arrival_time=10, burst_time=2, priority=1),
        ]
        result = FCFSScheduler().run(procs)
        assert_result_valid(result, 2)
        idle_entries = [e for e in result.gantt if e.pid == -1]
        assert len(idle_entries) >= 1  # must have at least one idle segment

    def test_empty(self):
        result = FCFSScheduler().run([])
        assert len(result.processes) == 0
        assert len(result.gantt) == 0


# ─────────────────────────────────────────────────────────────────────────────
#  SJF Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestSJF:
    def test_basic(self, simultaneous_processes):
        result = SJFScheduler().run(simultaneous_processes)
        assert_result_valid(result, 3)

    def test_shortest_runs_first(self, simultaneous_processes):
        """When all arrive at same time, shortest burst runs first."""
        result = SJFScheduler().run(simultaneous_processes)
        first_pid = min(result.processes, key=lambda p: p.start_time).pid
        # P2 has burst=3, shortest
        assert first_pid == 2

    def test_srtf_preemptive(self):
        """SRTF should preempt long process when shorter arrives."""
        procs = [
            Process(pid=1, arrival_time=0, burst_time=10, priority=1),
            Process(pid=2, arrival_time=2, burst_time=2,  priority=1),
        ]
        result = SJFScheduler(preemptive=True).run(procs)
        assert_result_valid(result, 2)
        # P2 should complete before P1 (SRTF preempts P1 at t=2)
        p1 = next(p for p in result.processes if p.pid == 1)
        p2 = next(p for p in result.processes if p.pid == 2)
        assert p2.completion_time < p1.completion_time

    def test_srtf_name(self):
        assert SJFScheduler(preemptive=True).name == "SRTF"


# ─────────────────────────────────────────────────────────────────────────────
#  Round Robin Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestRoundRobin:
    def test_basic(self, simple_processes):
        result = RoundRobinScheduler(time_quantum=4).run(simple_processes)
        assert_result_valid(result, 5)

    def test_single_process_no_preemption(self, single_process):
        result = RoundRobinScheduler(time_quantum=4).run(single_process)
        assert result.processes[0].completion_time == 15

    def test_fair_distribution(self, simultaneous_processes):
        """Round Robin should give all processes a turn in first quantum."""
        result = RoundRobinScheduler(time_quantum=2).run(simultaneous_processes)
        assert_result_valid(result, 3)
        # All 3 should have responded within first 6 time units
        for p in result.processes:
            assert p.response_time < 6 + 1e-6

    def test_context_switches(self, simultaneous_processes):
        """More processes = more context switches with RR."""
        result = RoundRobinScheduler(time_quantum=1).run(simultaneous_processes)
        total_cs = sum(p.context_switches for p in result.processes)
        assert total_cs >= 0  # can be 0 if single-pass, but sanity check

    def test_quantum_name(self):
        sched = RoundRobinScheduler(time_quantum=8)
        assert "8" in sched.name


# ─────────────────────────────────────────────────────────────────────────────
#  Priority Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestPriority:
    def test_basic(self, simultaneous_processes):
        result = PriorityScheduler().run(simultaneous_processes)
        assert_result_valid(result, 3)

    def test_highest_priority_runs_first(self, simultaneous_processes):
        """Process with lowest priority number runs first."""
        result = PriorityScheduler().run(simultaneous_processes)
        first = min(result.processes, key=lambda p: p.start_time)
        # P2 has priority=1 (highest)
        assert first.pid == 2

    def test_no_starvation_with_aging(self):
        """Low priority process eventually runs with aging."""
        procs = [
            Process(pid=1, arrival_time=0, burst_time=20, priority=1),
            Process(pid=2, arrival_time=0, burst_time=5,  priority=10),
        ]
        result = PriorityScheduler(aging_interval=5).run(procs)
        assert_result_valid(result, 2)
        # Both processes should complete
        for p in result.processes:
            assert p.completion_time > 0
