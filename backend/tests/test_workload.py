"""Tests for workload generator."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from workload_generator.generator import WorkloadGenerator, WorkloadConfig


class TestWorkloadGenerator:
    def setup_method(self):
        self.gen = WorkloadGenerator(seed=42)

    def test_small(self):
        procs = self.gen.generate("small")
        assert len(procs) == 10
        assert all(p.pid > 0 for p in procs)

    def test_medium(self):
        procs = self.gen.generate("medium")
        assert len(procs) == 30

    def test_large(self):
        procs = self.gen.generate("large")
        assert len(procs) == 100

    def test_random(self):
        procs = self.gen.generate("random")
        assert 5 <= len(procs) <= 200

    def test_override_n(self):
        procs = self.gen.generate("medium", n=15)
        assert len(procs) == 15

    def test_seed_reproducibility(self):
        a = self.gen.generate("medium", seed=99)
        b = self.gen.generate("medium", seed=99)
        assert [p.pid for p in a] == [p.pid for p in b]
        assert [p.burst_time for p in a] == [p.burst_time for p in b]

    def test_different_seeds(self):
        a = self.gen.generate("medium", seed=1)
        b = self.gen.generate("medium", seed=2)
        # burst times should differ for different seeds
        assert [p.burst_time for p in a] != [p.burst_time for p in b]

    def test_process_fields(self):
        procs = self.gen.generate("small")
        for p in procs:
            assert p.arrival_time >= 0
            assert p.burst_time > 0
            assert 1 <= p.priority <= 10
            assert p.process_type in ("cpu_bound", "io_bound")

    def test_sorted_by_arrival(self):
        procs = self.gen.generate("medium")
        arrivals = [p.arrival_time for p in procs]
        assert arrivals == sorted(arrivals)

    def test_csv_roundtrip(self):
        procs = self.gen.generate("small")
        csv_text = self.gen.to_csv(procs)
        loaded = self.gen.load_csv(csv_text)
        assert len(loaded) == len(procs)
        assert [p.pid for p in loaded] == [p.pid for p in procs]

    def test_csv_load_custom(self):
        csv = "pid,arrival_time,burst_time,priority,process_type\n1,0,5,3,cpu_bound\n2,2,3,1,io_bound\n"
        procs = self.gen.load_csv(csv)
        assert len(procs) == 2
        assert procs[0].burst_time == 5

    def test_invalid_mode(self):
        with pytest.raises(ValueError):
            self.gen.generate("invalid_mode")

    def test_csv_empty_raises(self):
        with pytest.raises(ValueError):
            self.gen.load_csv("pid,arrival_time,burst_time\n")

    def test_burst_types(self):
        procs = self.gen.generate("medium")
        cpu_procs = [p for p in procs if p.process_type == "cpu_bound"]
        io_procs  = [p for p in procs if p.process_type == "io_bound"]
        assert len(cpu_procs) > 0
        assert len(io_procs) > 0
        # CPU-bound should have longer avg burst
        avg_cpu = sum(p.burst_time for p in cpu_procs) / len(cpu_procs)
        avg_io  = sum(p.burst_time for p in io_procs)  / len(io_procs)
        assert avg_cpu > avg_io
