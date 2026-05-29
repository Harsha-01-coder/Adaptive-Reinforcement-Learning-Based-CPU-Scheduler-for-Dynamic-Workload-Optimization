"""Tests for the CPUSchedulerEnv Gymnasium environment."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    import gymnasium as gym
    import numpy as np
    HAS_GYM = True
except ImportError:
    HAS_GYM = False

pytestmark = pytest.mark.skipif(not HAS_GYM, reason="gymnasium not installed")


@pytest.fixture
def env():
    from rl_agent.cpu_env import CPUSchedulerEnv
    e = CPUSchedulerEnv(workload_mode="small", seed=42)
    yield e
    e.close()


class TestCPUSchedulerEnv:
    def test_spaces(self, env):
        from rl_agent.cpu_env import OBS_DIM
        assert env.observation_space.shape == (OBS_DIM,)
        assert env.action_space.n == 50

    def test_reset_returns_obs(self, env):
        obs, info = env.reset(seed=42)
        assert obs.shape == env.observation_space.shape
        assert obs.dtype.kind == "f"  # float32
        assert "n_processes" in info

    def test_obs_in_bounds(self, env):
        obs, _ = env.reset(seed=1)
        assert np.all(obs >= 0.0)
        assert np.all(obs <= 1.0 + 1e-6)

    def test_step_returns_tuple(self, env):
        env.reset(seed=42)
        result = env.step(0)
        assert len(result) == 5
        obs, reward, terminated, truncated, info = result
        assert obs.shape == env.observation_space.shape
        assert isinstance(reward, float)
        assert isinstance(terminated, bool)
        assert isinstance(truncated, bool)
        assert isinstance(info, dict)

    def test_episode_terminates(self, env):
        """A full episode must eventually terminate."""
        obs, _ = env.reset(seed=42)
        done = False
        steps = 0
        max_steps = 5000
        while not done and steps < max_steps:
            action = env.action_space.sample()
            obs, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated
            steps += 1
        assert done, "Episode should terminate within max_steps"

    def test_reward_finite(self, env):
        """All rewards must be finite numbers."""
        env.reset(seed=42)
        for _ in range(50):
            _, reward, done, trunc, _ = env.step(0)
            assert np.isfinite(reward)
            if done or trunc:
                break

    def test_info_keys(self, env):
        env.reset(seed=42)
        _, _, _, _, info = env.step(0)
        assert "completed" in info
        assert "total" in info
        assert "current_time" in info
        assert "cpu_utilization" in info

    def test_invalid_action_clamped(self, env):
        """Invalid action index should not raise."""
        env.reset(seed=42)
        obs, reward, done, trunc, info = env.step(999)  # out of range
        assert obs is not None

    def test_multiple_resets(self, env):
        """Environment should be re-usable across resets."""
        for seed in range(5):
            obs, info = env.reset(seed=seed)
            assert obs.shape == env.observation_space.shape
            assert info["n_processes"] > 0
