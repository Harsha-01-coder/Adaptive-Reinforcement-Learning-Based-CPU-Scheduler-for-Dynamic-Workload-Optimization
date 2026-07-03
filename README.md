# 🧠 Adaptive Reinforcement Learning-Based CPU Scheduler for Dynamic Workload Optimization

A **production-quality, portfolio-grade** full-stack CPU scheduling simulator that benchmarks traditional Operating System scheduling algorithms against an **Adaptive Reinforcement Learning-based scheduler** trained with **Proximal Policy Optimization (PPO)**.

Designed as an advanced systems engineering and machine learning showcase, this project is fully optimized for **software engineering portfolios, research presentations, and technical system design interviews**.

---

## 🌟 Key Highlights
* 🚀 **6 Production-Ready Schedulers**: FCFS, SJF, SRTF (Preemptive), Round Robin, Priority (with Aging), and an **RL (PPO) agent**.
* ⚡ **FastAPI High-Performance Backend**: Robust REST API with auto-generated OpenAPI (Swagger) docs, async SQLAlchemy/SQLite database structure, and full GZip compression.
* ⚛️ **Futuristic Dark-Mode React Dashboard**: Built with React 18, Vite, Recharts, and TailwindCSS for extremely smooth rendering of real-time multi-core Gantt charts, metrics, and comparisons.
* 🧠 **Custom Gymnasium Environment**: Comprehensive systems state space (ready queues, CPU cores) mapped to a composite reward signal designed to minimize wait time, CPU idle cycles, and context switches.
* 📈 **Live Training WebSocket**: Streams real-time training steps and reward progress directly from PyTorch / Stable-Baselines3 to a dynamic dashboard chart.
* 📦 **Production Infrastructure**: Built-in multi-container setup via Docker & `docker-compose`.

---

## 🛠️ Tech Stack & Libraries

* **Core Backend & Systems**: Python 3.11 · FastAPI · Async SQLAlchemy · Pydantic v2 · SQLite
* **Reinforcement Learning & AI**: Stable-Baselines3 · Gymnasium · PyTorch · NumPy · Pandas
* **Modern Frontend**: React 18 · Vite · TailwindCSS · Recharts · Lucide Icons
* **Reporting & Exports**: ReportLab (Dynamic PDF generation) · Python CSV
* **Containerization**: Docker · Docker Compose

---

## 📁 System Architecture & Design

```
                     ┌─────────────────────────────────────────────────┐
                     │                   Frontend                      │
                     │  React 18 + Vite + TailwindCSS + Recharts        │
                     │  Pages: Dashboard, Simulator, Benchmark, RL      │
                     └──────────────────────┬──────────────────────────┘
                                            │ REST / WebSocket
                     ┌──────────────────────▼──────────────────────────┐
                     │                  FastAPI Backend                  │
                     │  /api/simulate  /api/benchmark  /api/rl/*        │
                     │  /api/workload  /api/export                      │
                     └──────────────────────┬──────────────────────────┘
                                            │
                         ┌──────────────────┼──────────────────┐
                         │                  │                  │
                     ┌───▼───┐       ┌──────▼──────┐   ┌──────▼──────┐
                     │  DB   │       │  Schedulers │   │   RL Agent   │
                     │SQLite │       │FCFS SJF RR  │   │PPO+Gymnasium │
                     │ORMs   │       │Priority SRTF│   │ Stable-SB3   │
                     └───────┘       └─────────────┘   └─────────────┘
```

---

## 🚀 Quick Start & Installation

### Prerequisites
* Python 3.11+
* Node.js 18+

### 1. Clone & Set Up the Backend
```bash
# Navigate to the backend folder
cd backend

# Install all python dependencies
pip install -r requirements.txt

# Copy environment variables template
cp ../.env.example .env

# Run FastAPI server
uvicorn app.main:app --reload
```
* **API Server URL**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
* **Swagger API Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. Set Up the Frontend
Open a new terminal window:
```bash
# Navigate to the frontend folder
cd frontend

# Install npm dependencies
npm install

# Run the local Vite dev server
npm run dev
```
* **Dashboard URL**: [http://127.0.0.1:5173](http://127.0.0.1:5173)

---

## ☁️ Internet Cloud Deployment

This project is fully pre-configured to deploy on the internet for free using **Vercel** (Frontend) and **Render** (FastAPI Backend + PostgreSQL database):

### 1. Database (Render PostgreSQL)
* Create a free **PostgreSQL Database** on Render.
* Copy the **External Connection String** (format: `postgresql://...`).
* Convert the prefix from `postgresql://` to `postgresql+asyncpg://` for asynchronous python database driver compatibility.

### 2. Backend (Render Web Service)
* Create a new **Web Service** pointing to your repository.
* Set the **Root Directory** to `backend`.
* **Build Command**: `pip install -r requirements.txt`
* **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
* Set **Environment Variables**:
  * `DATABASE_URL` = (Your converted `postgresql+asyncpg://...` URL)
  * `DEBUG` = `false`
  * `ALLOWED_ORIGINS` = `https://your-app-name.vercel.app`

### 3. Frontend (Vercel SPA static hosting)
* Import the repository in Vercel.
* Set the **Root Directory** to `frontend`.
* Add the **Environment Variable**:
  * `VITE_API_URL` = (Your Render backend URL, e.g., `https://your-backend.onrender.com`)
* Hit **Deploy**. Vercel will read the `vercel.json` routing configuration and deploy the responsive React panel instantly.

---

## 🎛️ Dynamic Training Abort (Stop Training)
The project supports early cancellation of PPO agent training loops:
* **Custom SB3 Callback**: The training executor registers a callback that checks a cancellation flag on every environment step inside Stable-Baselines3.
* **Dashboard Control**: Click **Stop Training** (red button) during active training to send a `POST /api/rl/stop` request, immediately halting calculations and closing WebSocket logs.

---

## 📚 Study & Interview Guides
For university presentations, placements, and system defense reviews, we have compiled comprehensive reference manuals inside the [docs/](file:///c:/Users/harsh/OneDrive/Desktop/Adaptive%20Reinforcement%20Learning-Based%20CPU%20Scheduler%20for%20Dynamic%20Workload%20Optimization/docs) directory:
* 🎓 **[Interview Masterclass](file:///c:/Users/harsh/OneDrive/Desktop/Adaptive%20Reinforcement%20Learning-Based%20CPU%20Scheduler%20for%20Dynamic%20Workload%20Optimization/docs/INTERVIEW_MASTERCLASS.docx)**: In-depth Q&A covering OS math, Gymnasium dimensions, rewards, PPO policy gradient details, and backend ASGI concurrency.
* 🚀 **[Future Scope & Roadmap](file:///c:/Users/harsh/OneDrive/Desktop/Adaptive%20Reinforcement%20Learning-Based%20CPU%20Scheduler%20for%20Dynamic%20Workload%20Optimization/docs/FUTURE_SCOPE.md)**: Conceptual guide to scaling this project to Kubernetes cluster scheduling, eBPF Linux kernel hooks, and thermal DVFS energy models.
* 📖 **[Project Design Guide](file:///c:/Users/harsh/OneDrive/Desktop/Adaptive%20Reinforcement%20Learning-Based%20CPU%20Scheduler%20for%20Dynamic%20Workload%20Optimization/docs/PROJECT_GUIDE.md)**: Step-by-step structural walkthrough of the simulator components.

---

## 🧠 Reinforcement Learning Design

### 1. State Space (252-dimensional Observation Vector)
The state of the ready queue and cores is encoded for the neural network:
* **Ready Queue Processes (Up to 50 slots)**: Remaining Burst Time, Priority, Process Type (CPU-bound vs I/O-bound), and Waiting Time.
* **Global CPU State**: Cores utilization, active running tasks, and simulation elapsed time.

### 2. Action Space (`Discrete(50)`)
The agent chooses one of the active 50 slots in the Ready Queue to schedule next on the available CPU core.

### 3. Composite Reward Function
$$\text{Reward} = - \alpha \cdot \text{Wait Time} - \beta \cdot \text{Starvation Penalty} - \gamma \cdot \text{Context Switch Cost} + \delta \cdot \text{CPU Utilization}$$
This rewards high throughput while penalizing starvation and frequent context switching.

---

## 📝 License
Distributed under the **MIT License**. See `LICENSE` for details.
