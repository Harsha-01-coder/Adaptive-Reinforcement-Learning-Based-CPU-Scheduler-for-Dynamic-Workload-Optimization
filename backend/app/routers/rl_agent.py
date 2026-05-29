"""
RL Agent API routes — training, status, and evaluation.

Training runs as a background task. Status is tracked globally
(single-training-at-a-time model; suitable for local/demo use).
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Dict, List

from fastapi import APIRouter, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect

from ..schemas import TrainRequest, TrainStatusResponse
from ..config import get_settings

router = APIRouter(prefix="/api/rl", tags=["RL Agent"])
settings = get_settings()

# ── Global training state ─────────────────────────────────────────────────────

_training_state: Dict[str, Any] = {
    "status": "idle",          # idle | training | completed | failed
    "current_timestep": 0,
    "total_timesteps": 0,
    "reward_log": {"steps": [], "rewards": []},
    "error": None,
}
_ws_clients: List[WebSocket] = []


async def _broadcast(data: Dict) -> None:
    """Send update to all connected WebSocket clients."""
    dead = []
    for ws in _ws_clients:
        try:
            await ws.send_json(data)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _ws_clients.remove(ws)


def _progress_callback(step: int, reward: float) -> None:
    """Called by training loop to update state."""
    state = _training_state
    state["current_timestep"] = step
    reward_log = state["reward_log"]
    reward_log["steps"].append(step)
    reward_log["rewards"].append(reward)

    # Keep only last 1000 points for live chart
    if len(reward_log["steps"]) > 1000:
        reward_log["steps"] = reward_log["steps"][-1000:]
        reward_log["rewards"] = reward_log["rewards"][-1000:]

    # Async broadcast from sync context — schedule on event loop
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(
                _broadcast({
                    "type": "progress",
                    "step": step,
                    "reward": reward,
                    "total": state["total_timesteps"],
                }),
                loop,
            )
    except RuntimeError:
        pass


async def _train_background(req: TrainRequest) -> None:
    """Background training task."""
    state = _training_state
    state["status"] = "training"
    state["total_timesteps"] = req.timesteps
    state["current_timestep"] = 0
    state["reward_log"] = {"steps": [], "rewards": []}
    state["error"] = None

    try:
        import sys, os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from rl_agent.train import train

        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: train(
                timesteps=req.timesteps,
                n_envs=req.n_envs,
                workload_mode=req.workload_mode,
                model_save_path=settings.rl_model_path,
                progress_callback=_progress_callback,
                seed=req.seed,
            ),
        )
        # Merge final reward log from training script
        if result.get("reward_log"):
            state["reward_log"] = result["reward_log"]
        state["status"] = "completed"
        await _broadcast({"type": "completed", "summary": result})

    except Exception as e:
        state["status"] = "failed"
        state["error"] = str(e)
        await _broadcast({"type": "error", "error": str(e)})


# ── REST Endpoints ─────────────────────────────────────────────────────────────

@router.get("/status", response_model=None)
async def get_status() -> Dict[str, Any]:
    """Get current RL training status and reward log."""
    state = _training_state
    total = state["total_timesteps"]
    current = state["current_timestep"]
    progress = (current / total * 100) if total > 0 else 0.0

    rewards = state["reward_log"].get("rewards", [])
    mean_reward = sum(rewards[-50:]) / len(rewards[-50:]) if rewards else 0.0

    model_exists = os.path.exists(settings.rl_model_path + ".zip")

    return {
        "status": state["status"],
        "progress_pct": round(progress, 1),
        "current_timestep": current,
        "total_timesteps": total,
        "mean_reward": round(mean_reward, 4),
        "reward_log": state["reward_log"],
        "error": state["error"],
        "model_available": model_exists,
    }


@router.post("/train")
async def start_training(
    request: TrainRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Start RL agent training in the background.

    Only one training session can run at a time.
    """
    if _training_state["status"] == "training":
        raise HTTPException(status_code=409, detail="Training already in progress")

    background_tasks.add_task(_train_background, request)
    return {
        "message": "Training started",
        "timesteps": request.timesteps,
        "workload_mode": request.workload_mode,
    }


@router.post("/evaluate")
async def evaluate_model(
    n_episodes: int = 10,
    workload_mode: str = "medium",
    seed: int = 100,
) -> Dict[str, Any]:
    """Evaluate the trained RL model over N episodes."""
    model_path = settings.rl_model_path
    if not os.path.exists(model_path + ".zip"):
        raise HTTPException(
            status_code=404,
            detail="No trained model found. Train the agent first via POST /api/rl/train.",
        )

    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from rl_agent.evaluate import evaluate

        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: evaluate(
                model_path=model_path,
                n_episodes=n_episodes,
                workload_mode=workload_mode,
                seed=seed,
            ),
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── WebSocket ──────────────────────────────────────────────────────────────────

@router.websocket("/ws/training")
async def training_websocket(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for live training updates.

    Messages emitted:
        {"type": "progress", "step": N, "reward": R, "total": T}
        {"type": "completed", "summary": {...}}
        {"type": "error", "error": "..."}
    """
    await websocket.accept()
    _ws_clients.append(websocket)

    # Send current state immediately
    await websocket.send_json({
        "type": "state",
        "data": await get_status(),
    })

    try:
        while True:
            # Keep connection alive; actual data pushed via _broadcast
            await asyncio.sleep(30)
            await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        if websocket in _ws_clients:
            _ws_clients.remove(websocket)
