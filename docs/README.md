# Adaptive Reinforcement Learning-Based CPU Scheduler
## for Dynamic Workload Optimization

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-cyan?logo=react)](https://reactjs.org)
[![Stable-Baselines3](https://img.shields.io/badge/SB3-PPO-orange)](https://stable-baselines3.readthedocs.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

A **production-quality, portfolio-grade** CPU scheduling simulator that compares traditional OS
scheduling algorithms against a **Reinforcement Learning-based scheduler** trained with
**Proximal Policy Optimization (PPO)**.

> Built as a research + engineering showcase project suitable for internship portfolios,
> research presentations, and technical interviews.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 6 Scheduling Algorithms | FCFS, SJF, SRTF, Round Robin, Priority, RL (PPO) |
| Workload Generator | Small/Medium/Large/Random presets + CSV import |
| RL Agent | Custom Gymnasium env + PPO (Stable-Baselines3) |
| Live Gantt Chart | SVG-based, multi-core, color-coded |
| Benchmark System | All algorithms on identical workloads + statistical rankings |
| 9 Performance Metrics | Wait, TAT, Response, CPU%, Throughput, CTX SW, Fairness, Makespan |
| Export | CSV + PDF reports |
| Dark Mode Dashboard | React + TailwindCSS + Recharts |
| REST API | FastAPI + OpenAPI/Swagger docs |
| WebSocket | Live RL training reward curve |
| Multi-core Simulation | 1–8 configurable CPU cores |
| Docker | Full docker-compose setup |

---

## 🚀 Quick Start (Local Dev)

### Prerequisites
- Python 3.11+
- Node.js 18+
- pip, npm

### 1. Clone & Setup Backend

```bash
cd backend
pip install -r requirements.txt
cp ../.env.example ../.env
uvicorn app.main:app --reload
```

Backend available at: http://localhost:8000
API Docs: http://localhost:8000/docs

### 2. Setup Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard available at: http://localhost:5173

### 3. Docker (Full Stack)

```bash
docker-compose up --build
```

---

## 📁 Project Structure

```
/
├── backend/
│   ├── app/                  # FastAPI application
│   │   ├── main.py           # App entry point
│   │   ├── routers/          # API endpoints
│   │   ├── services/         # Business logic
│   │   ├── models/           # SQLAlchemy ORM
│   │   └── schemas/          # Pydantic validation
│   ├── schedulers/           # Algorithm implementations
│   ├── workload_generator/   # Workload generation
│   ├── rl_agent/             # PPO training & evaluation
│   ├── tests/                # pytest test suite
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/            # Dashboard, Simulator, Benchmark, RL, Docs
│       ├── components/       # GanttChart, MetricsTable, BenchmarkChart, etc.
│       └── api/              # axios client
├── docs/                     # Documentation
├── docker-compose.yml
└── .env.example
```

---

## 🧠 RL Agent Details

- **Environment**: Custom `CPUSchedulerEnv(gymnasium.Env)`
- **Observation**: 252-dim vector (ready queue state + global stats)
- **Action**: `Discrete(50)` — select which process to run next
- **Reward**: Composite signal minimizing wait, context switches, starvation
- **Algorithm**: PPO from Stable-Baselines3
- **Policy**: MLP [256, 256] for both policy and value networks

---

## 📊 Performance Metrics

| Metric | Formula |
|--------|---------|
| Avg Waiting Time | Σ(TAT - BurstTime) / n |
| Avg Turnaround Time | Σ(Completion - Arrival) / n |
| Avg Response Time | Σ(FirstRun - Arrival) / n |
| CPU Utilization | BusyTime / TotalTime × 100% |
| Throughput | n / Makespan |
| Fairness Score | Jain's Index on waiting times |

---

## 📚 Documentation

- [Architecture](ARCHITECTURE.md)
- [System Design](SYSTEM_DESIGN.md)
- [API Documentation](API_DOCS.md)
- [Installation Guide](INSTALLATION.md)
- [Resume Talking Points](RESUME_TALKING_POINTS.md)

---

## 🛠️ Tech Stack

**Backend**: Python 3.11 · FastAPI · SQLAlchemy · Pydantic  
**AI/ML**: Stable-Baselines3 · Gymnasium · PyTorch · NumPy  
**Frontend**: React 18 · Vite · TailwindCSS · Recharts · framer-motion  
**Database**: SQLite (dev) / PostgreSQL (production)  
**Export**: ReportLab (PDF) · CSV stdlib  
**Infrastructure**: Docker · docker-compose  

---

## 📝 License

MIT License — free for academic and portfolio use.
