"""
RL Agent Evaluation Module

Evaluates a trained PPO model against a workload and returns performance
metrics comparable to traditional scheduling algorithms.

Usage:
    python -m rl_agent.evaluate --model rl_agent/models/ppo_cpu_scheduler
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))


def evaluate(
    model_path: str = "rl_agent/models/ppo_cpu_scheduler",
    n_episodes: int = 10,
    workload_mode: str = "medium",
    seed: int = 100,
) -> Dict[str, Any]:
    """
    Evaluate a trained PPO model on CPU scheduling.

    Returns:
        Dictionary with mean/std metrics across episodes.
    """
    from stable_baselines3 import PPO
    from rl_agent.cpu_env import CPUSchedulerEnv

    path = model_path
    if not path.endswith(".zip"):
        path += ".zip"

    if not os.path.exists(path):
        return {
            "error": f"Model not found at {path}",
            "status": "no_model",
        }

    model = PPO.load(path)
    env = CPUSchedulerEnv(workload_mode=workload_mode, seed=seed)

    episode_stats: List[Dict[str, float]] = []

    for ep in range(n_episodes):
        obs, info = env.reset(seed=seed + ep)
        terminated = False
        truncated = False
        total_reward = 0.0

        while not (terminated or truncated):
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(int(action))
            total_reward += reward

        # Gather final metrics from completed processes
        procs = env._processes
        completed_procs = [p for p in procs if p.completion_time >= 0]

        if completed_procs:
            avg_wt = sum(
                max(0.0, p.turnaround_time - p.burst_time)
                for p in completed_procs
            ) / len(completed_procs)
            avg_tat = sum(p.turnaround_time for p in completed_procs) / len(completed_procs)
            avg_rt = sum(p.response_time for p in completed_procs if p.response_time >= 0) / len(completed_procs)
        else:
            avg_wt = avg_tat = avg_rt = 0.0

        episode_stats.append({
            "episode": ep + 1,
            "total_reward": round(total_reward, 4),
            "avg_waiting_time": round(avg_wt, 4),
            "avg_turnaround_time": round(avg_tat, 4),
            "avg_response_time": round(avg_rt, 4),
            "cpu_utilization": round(info.get("cpu_utilization", 0.0) * 100, 2),
            "context_switches": info.get("context_switches", 0),
            "completion_rate": info.get("completed", 0) / max(info.get("total", 1), 1),
        })

    import numpy as np
    rewards = [s["total_reward"] for s in episode_stats]
    waits = [s["avg_waiting_time"] for s in episode_stats]
    tats = [s["avg_turnaround_time"] for s in episode_stats]

    return {
        "status": "ok",
        "model_path": path,
        "n_episodes": n_episodes,
        "workload_mode": workload_mode,
        "mean_reward": round(float(np.mean(rewards)), 4),
        "std_reward": round(float(np.std(rewards)), 4),
        "mean_waiting_time": round(float(np.mean(waits)), 4),
        "mean_turnaround_time": round(float(np.mean(tats)), 4),
        "episode_stats": episode_stats,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate PPO CPU Scheduler")
    parser.add_argument("--model", type=str, default="rl_agent/models/ppo_cpu_scheduler")
    parser.add_argument("--episodes", type=int, default=10)
    parser.add_argument("--mode", type=str, default="medium")
    parser.add_argument("--seed", type=int, default=100)
    args = parser.parse_args()

    result = evaluate(
        model_path=args.model,
        n_episodes=args.episodes,
        workload_mode=args.mode,
        seed=args.seed,
    )
    print(json.dumps(result, indent=2))
