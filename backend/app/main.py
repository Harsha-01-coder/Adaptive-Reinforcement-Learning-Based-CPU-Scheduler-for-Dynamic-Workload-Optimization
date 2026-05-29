"""
FastAPI Application Entry Point

Adaptive Reinforcement Learning-Based CPU Scheduler
"""

from __future__ import annotations

# ── Path setup ────────────────────────────────────────────────────────────────
# Ensure the backend/ directory is on sys.path so that sibling packages
# (schedulers, workload_generator, rl_agent) can be imported absolutely.
import sys
import os as _os
_backend_dir = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)
# ─────────────────────────────────────────────────────────────────────────────

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from .config import get_settings
from .database import create_tables
from .routers import (
    benchmark_router,
    export_router,
    rl_router,
    scheduler_router,
    workload_router,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # ── Startup ───────────────────────────────────────────────
    print("Starting Adaptive RL CPU Scheduler API...")
    await create_tables()

    # Ensure export directory exists
    os.makedirs(settings.export_dir, exist_ok=True)
    os.makedirs("rl_agent/models", exist_ok=True)

    print(f"  Database : {settings.database_url}")
    print(f"  CORS     : {settings.cors_origins}")
    print(f"  RL Model : {settings.rl_model_path}")
    print("API ready!")

    yield

    # ── Shutdown ──────────────────────────────────────────────
    print("Shutting down...")


# ── Application ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Adaptive RL CPU Scheduler",
    description="""
## Adaptive Reinforcement Learning-Based CPU Scheduler

A production-quality CPU scheduling simulator that benchmarks traditional OS
scheduling algorithms against a Reinforcement Learning-based scheduler.

### Algorithms
- **FCFS** — First Come First Serve
- **SJF** — Shortest Job First
- **SRTF** — Shortest Remaining Time First (preemptive)
- **Round Robin** — Time-quantum preemptive scheduling
- **Priority** — Priority-based with aging
- **RL (PPO)** — Trained Proximal Policy Optimization agent

### Features
- Real-time Gantt chart generation
- Multi-core CPU simulation (1–8 cores)
- Automated benchmark comparisons
- CSV and PDF export
- Live RL training via WebSocket
    """,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware ─────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1024)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(scheduler_router)
app.include_router(workload_router)
app.include_router(rl_router)
app.include_router(benchmark_router)
app.include_router(export_router)


# ── Health Check ──────────────────────────────────────────────────────────────

@app.get("/api/health", tags=["System"])
async def health_check():
    """API health check endpoint."""
    import os
    return {
        "status": "healthy",
        "version": settings.app_version,
        "debug": settings.debug,
        "rl_model_available": os.path.exists(settings.rl_model_path + ".zip"),
    }


@app.get("/", tags=["System"])
async def root():
    return {
        "message": "Adaptive RL CPU Scheduler API",
        "docs": "/docs",
        "health": "/api/health",
    }
