"""
PPO Training Script for CPU Scheduler RL Agent

Usage:
    python -m rl_agent.train [--timesteps 500000] [--n-envs 4] [--mode medium]

Trains a PPO agent on the CPUSchedulerEnv and saves the model
to rl_agent/models/ppo_cpu_scheduler.zip.

Logs reward curves to tensorboard (logs/ppo_cpu_scheduler/).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

# Allow running as script from backend/
sys.path.insert(0, str(Path(__file__).parent.parent))


def train(
    timesteps: int = 500_000,
    n_envs: int = 4,
    workload_mode: str = "medium",
    model_save_path: str = "rl_agent/models/ppo_cpu_scheduler",
    log_dir: str = "logs/ppo_cpu_scheduler",
    progress_callback: Optional[Any] = None,
    seed: int = 42,
    check_cancelled: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Train a PPO agent on the CPU scheduling environment.

    Args:
        timesteps: Total environment interaction steps.
        n_envs: Number of parallel environments.
        workload_mode: Workload difficulty preset.
        model_save_path: Where to save the trained model.
        log_dir: TensorBoard log directory.
        progress_callback: Optional callable(step, reward) for live updates.
        seed: Random seed.
        check_cancelled: Optional callable returning True to abort training.

    Returns:
        Dictionary with training summary metrics.
    """
    from stable_baselines3 import PPO
    from stable_baselines3.common.callbacks import (
        BaseCallback,
        CheckpointCallback,
        EvalCallback,
    )
    from stable_baselines3.common.env_util import make_vec_env
    from stable_baselines3.common.vec_env import SubprocVecEnv

    from rl_agent.cpu_env import CPUSchedulerEnv

    # Create output directories
    os.makedirs(os.path.dirname(model_save_path) or ".", exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    print(f"[Train] Starting PPO training:")
    print(f"  Timesteps : {timesteps:,}")
    print(f"  Envs      : {n_envs}")
    print(f"  Mode      : {workload_mode}")
    print(f"  Save path : {model_save_path}")

    # ── Environment setup ─────────────────────────────────────────────────────
    env_kwargs = dict(workload_mode=workload_mode, seed=seed)
    vec_env = make_vec_env(
        CPUSchedulerEnv,
        n_envs=n_envs,
        seed=seed,
        env_kwargs=env_kwargs,
    )

    # Eval env (single, fixed seed)
    eval_env = CPUSchedulerEnv(workload_mode=workload_mode, seed=seed + 999)

    # ── Callbacks ─────────────────────────────────────────────────────────────

    reward_log: List[float] = []
    step_log: List[int] = []

    class RewardLogCallback(BaseCallback):
        def __init__(self):
            super().__init__()
            self._ep_rewards: List[float] = []

        def _on_step(self) -> bool:
            # Check for early cancellation trigger
            if check_cancelled is not None and check_cancelled():
                print("[Train] Stop requested by client callback. Aborting...")
                return False

            # Collect episode rewards from infos
            for info in self.locals.get("infos", []):
                if "episode" in info:
                    ep_r = info["episode"]["r"]
                    reward_log.append(float(ep_r))
                    step_log.append(self.num_timesteps)
                    if progress_callback is not None:
                        progress_callback(self.num_timesteps, float(ep_r))
            return True

    reward_callback = RewardLogCallback()
    checkpoint_cb = CheckpointCallback(
        save_freq=max(timesteps // 10, 10_000),
        save_path=os.path.dirname(model_save_path) or ".",
        name_prefix="ppo_cpu_ckpt",
    )

    # ── Model ─────────────────────────────────────────────────────────────────
    model = PPO(
        policy="MlpPolicy",
        env=vec_env,
        n_steps=2048,
        batch_size=256,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
        learning_rate=3e-4,
        verbose=1,
        tensorboard_log=log_dir,
        seed=seed,
        policy_kwargs=dict(
            net_arch=dict(pi=[256, 256], vf=[256, 256]),
        ),
    )

    # ── Training ──────────────────────────────────────────────────────────────
    t0 = time.time()
    model.learn(
        total_timesteps=timesteps,
        callback=[reward_callback, checkpoint_cb],
        progress_bar=False,
    )
    elapsed = time.time() - t0

    # ── Save ──────────────────────────────────────────────────────────────────
    model.save(model_save_path)
    print(f"[Train] Model saved to {model_save_path}.zip")

    # Save reward log
    reward_log_path = os.path.join(os.path.dirname(model_save_path) or ".", "reward_log.json")
    with open(reward_log_path, "w") as f:
        json.dump({"steps": step_log, "rewards": reward_log}, f)

    # Smooth rewards for reporting
    if reward_log:
        window = min(50, len(reward_log))
        recent_mean = float(np.mean(reward_log[-window:]))
        best_reward = float(max(reward_log))
    else:
        recent_mean = 0.0
        best_reward = 0.0

    return {
        "timesteps": timesteps,
        "training_time_seconds": round(elapsed, 1),
        "n_episodes": len(reward_log),
        "mean_reward_last_50": round(recent_mean, 4),
        "best_episode_reward": round(best_reward, 4),
        "model_path": model_save_path + ".zip",
        "reward_log": {"steps": step_log, "rewards": reward_log},
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train PPO CPU Scheduler")
    parser.add_argument("--timesteps", type=int, default=500_000)
    parser.add_argument("--n-envs", type=int, default=4)
    parser.add_argument("--mode", type=str, default="medium")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--save-path", type=str, default="rl_agent/models/ppo_cpu_scheduler")
    args = parser.parse_args()

    result = train(
        timesteps=args.timesteps,
        n_envs=args.n_envs,
        workload_mode=args.mode,
        model_save_path=args.save_path,
        seed=args.seed,
    )
    print("\n[Train] Summary:")
    for k, v in result.items():
        if k != "reward_log":
            print(f"  {k}: {v}")
