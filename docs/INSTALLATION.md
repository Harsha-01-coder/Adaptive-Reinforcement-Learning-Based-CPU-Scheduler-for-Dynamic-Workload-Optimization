# Installation Guide

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11+ | https://python.org |
| Node.js | 18+ | https://nodejs.org |
| pip | latest | included with Python |
| npm | latest | included with Node |
| Docker (optional) | 24+ | https://docker.com |

---

## Option A: Local Development (No Docker)

### 1. Clone the repository

```bash
git clone <repo-url>
cd "Adaptive Reinforcement Learning-Based CPU Scheduler for Dynamic Workload Optimization"
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env if needed (defaults work for local dev)
```

### 3. Install backend dependencies

```bash
cd backend
pip install -r requirements.txt
```

> **Note**: `torch` (PyTorch) is included for the RL agent. For CPU-only systems,
> consider installing the CPU build: `pip install torch --index-url https://download.pytorch.org/whl/cpu`

### 4. Start the backend

```bash
# From the backend/ directory:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend available at: http://localhost:8000
API Docs (Swagger): http://localhost:8000/docs

### 5. Install frontend dependencies

```bash
cd ../frontend
npm install
```

### 6. Start the frontend

```bash
npm run dev
```

Dashboard available at: http://localhost:5173

---

## Option B: Docker Compose (Recommended for Production)

```bash
docker-compose up --build
```

Services:
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- PostgreSQL: localhost:5432

> Set `DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/scheduler_db` in `.env`
> when using Docker (already configured in docker-compose.yml).

---

## Option C: Backend-Only (API testing)

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
# Test at http://localhost:8000/docs
```

---

## Running Tests

```bash
cd backend
pytest tests/ -v --cov=schedulers --cov=workload_generator
```

Expected output: 20+ tests passing.

---

## Training the RL Agent

```bash
cd backend
python -m rl_agent.train --timesteps 100000 --mode medium --n-envs 2
```

The trained model is saved to `backend/rl_agent/models/ppo_cpu_scheduler.zip`.

Once trained, the RL Scheduler option in the dashboard will use the trained model.

### Training time estimates

| Timesteps | Approx. Time | Expected Quality |
|-----------|-------------|-----------------|
| 10,000 | ~1 min | Basic policy |
| 100,000 | ~10 min | Decent policy |
| 500,000 | ~30 min | Good policy |
| 2,000,000 | ~2 hrs | Production-quality |

---

## Common Issues

### `ModuleNotFoundError: No module named 'schedulers'`
Run from the `backend/` directory, or add it to PYTHONPATH:
```bash
export PYTHONPATH=$PYTHONPATH:/path/to/backend
```

### PyTorch installation slow
Use the CPU-only wheel:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### Frontend proxy errors (CORS)
Ensure the backend is running on port 8000. The Vite dev server proxies `/api` requests automatically.

### Database locked (SQLite)
SQLite only allows one writer at a time. Use PostgreSQL via docker-compose for concurrent access.
