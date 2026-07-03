# 🧠 Adaptive Reinforcement Learning CPU Scheduler for Dynamic Workload Optimization

A **production-quality, portfolio-grade** full-stack CPU scheduling simulator that benchmarks traditional Operating System heuristics against an **Adaptive Reinforcement Learning-based scheduler** trained with **Proximal Policy Optimization (PPO)**. 

Designed as an advanced systems engineering and machine learning showcase, this project is fully optimized for **software engineering portfolios, research presentations, and technical system design interviews**.

---

## 🌟 Key Highlights
* 🚀 **6 Production Schedulers**: FCFS, SJF, SRTF (Preemptive), Round Robin, Priority (with Aging), and an **RL (PPO) agent**.
* ⚡ **FastAPI Asynchronous Backend**: ASGI-powered API with auto-generated OpenAPI (Swagger) schemas, async SQLAlchemy ORM transactions, and full GZip compression.
* ⚛️ **Responsive Dashboard**: React 18 frontend built with Vite, TailwindCSS, and Recharts, supporting dynamic multi-core Gantt charts and real-time benchmark side-by-side metrics.
* 🧠 **Custom Gymnasium Environment**: Modeling CPU cores and ready queues into a 252-dimensional normalized systems state space.
* 📈 **Live Training WebSocket Stream**: Streams real-time training steps and reward progress directly from PyTorch / Stable-Baselines3.
* 🎛️ **Dynamic Training Interruption**: Custom Stable-Baselines3 progress callback checking thread-safe cancel triggers to stop PyTorch learning instantly.
* 📦 **Production Containers**: Integrated multi-container orchestration via Docker & Docker Compose.

---

## 🏛️ Project Architecture & Data Flow

```
                     ┌─────────────────────────────────────────────────┐
                     │                   Frontend                      │
                     │  React 18 + Vite + TailwindCSS + Recharts        │
                     │  Pages: Dashboard, Simulator, Benchmark, RL      │
                     └──────────────────────┬──────────────────────────┘
                                            │ REST / WebSockets
                     ┌──────────────────────▼──────────────────────────┐
                     │                  FastAPI Backend                  │
                     │  /api/simulate  /api/benchmark  /api/rl/*        │
                     │  /api/workload  /api/export                      │
                     └──────────────────────┬──────────────────────────┘
                                            │
                          ┌─────────────────┼──────────────────┐
                          │                 │                  │
                     ┌───▼───┐       ┌──────▼──────┐   ┌──────▼──────┐
                     │  DB   │       │  Schedulers │   │   RL Agent   │
                     │SQLite │       │FCFS SJF RR  │   │PPO+Gymnasium │
                     │ORMs   │       │Priority SRTF│   │ Stable-SB3   │
                     └───────┘       └─────────────┘   └─────────────┘
```

---

## 🛠️ Implemented Schedulers Grid

| Algorithm | Type | Scheduling Criteria | Complexity | Starvation Prevention |
| :--- | :--- | :--- | :--- | :--- |
| **FCFS** | Non-preemptive | Order of arrival | $O(1)$ | N/A |
| **SJF** | Non-preemptive | Shortest total CPU burst first | $O(\log N)$ | No |
| **SRTF** | Preemptive | Shortest remaining burst first | $O(\log N)$ | No |
| **Round Robin** | Preemptive | Time-slice sharing (fixed quantum) | $O(1)$ | Yes |
| **Priority** | Preemptive | Process priority integer | $O(\log N)$ | **Yes (via Aging)** |
| **RL (PPO)** | Preemptive | Dynamic neural policy of queue state | $O(N)$ inference | **Yes (via Starvation Penalty)** |

---

## 🧠 Reinforcement Learning System Design

### 1. State Space (252-dimensional Observation Vector)
The state of the ready queue and cores is encoded for the neural network:
* **Ready Queue Processes (Up to 50 slots, 5 features per slot)**: Remaining Burst Time / 100, Wait Time / 100, Priority / 10, Process Type (0/1), and Slot Presence (0/1).
* **Global CPU State**: Cores utilization, active running tasks, and simulation elapsed time.

### 2. Action Space (`Discrete(50)`)
The agent chooses one of the active 50 slots in the Ready Queue to schedule next on the available CPU core. If the agent selects an empty slot, the environment executes **Action Masking** (redirection to the longest waiting process).

### 3. Composite Reward Function
$$\text{Reward} = - (\alpha \cdot \text{Wait Time}) - (\beta \cdot \text{Starvation}) - (\gamma \cdot \text{Context Switches}) + (\delta \cdot \text{CPU Utilization}) + (\theta \cdot \text{Completion})$$

> [!NOTE]
> Weights in our environment: $\alpha = 0.4$, $\beta = 0.2$, $\gamma = 0.1$, $\delta = 0.2$, and $\theta = 0.1$. This balances low average waiting time with core efficiency and process fairness.

---

## ☁️ Internet Cloud Deployment

The project is fully pre-configured to deploy on the internet for free using **Vercel** (Frontend) and **Render** (FastAPI Backend + PostgreSQL database):

### 1. Database (Render PostgreSQL)
1. Create a free **PostgreSQL Database** on Render.
2. Copy the **External Connection String**.
3. Convert the prefix from `postgresql://` to `postgresql+asyncpg://` for async python database compatibility.

### 2. Backend (Render Web Service)
1. Create a new **Web Service** pointing to your repository.
2. Set the **Root Directory** to `backend`.
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Set **Environment Variables**:
   * `DATABASE_URL` = (Your converted `postgresql+asyncpg://...` URL)
   * `DEBUG` = `false`
   * `ALLOWED_ORIGINS` = `https://your-app-name.vercel.app`

### 3. Frontend (Vercel SPA static hosting)
1. Import the repository in Vercel.
2. Set the **Root Directory** to `frontend`.
3. Add the **Environment Variable**:
   * `VITE_API_URL` = (Your Render backend URL, e.g., `https://your-backend.onrender.com`)
4. Hit **Deploy**. Vercel will read the `vercel.json` routing configuration and deploy the responsive React panel instantly.

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

## 📚 Reference Guides & Defense Documentation
For university presentations, placements, and system defense reviews, we have compiled comprehensive reference manuals inside the [docs/](file:///c:/Users/harsh/OneDrive/Desktop/Adaptive%20Reinforcement%20Learning-Based%20CPU%20Scheduler%20for%20Dynamic%20Workload%20Optimization/docs) directory:
* 🎓 **[Interview Masterclass](file:///c:/Users/harsh/OneDrive/Desktop/Adaptive%20Reinforcement%20Learning-Based%20CPU%20Scheduler%20for%20Dynamic%20Workload%20Optimization/docs/INTERVIEW_MASTERCLASS.docx)**: In-depth Q&A covering OS math, Gymnasium dimensions, rewards, PPO policy gradient details, and backend ASGI concurrency.
* 🚀 **[Future Scope & Roadmap](file:///c:/Users/harsh/OneDrive/Desktop/Adaptive%20Reinforcement%20Learning-Based%20CPU%20Scheduler%20for%20Dynamic%20Workload%20Optimization/docs/FUTURE_SCOPE.md)**: Conceptual guide to scaling this project to Kubernetes cluster scheduling, eBPF Linux kernel hooks, and thermal DVFS energy models.
* 📖 **[Project Design Guide](file:///c:/Users/harsh/OneDrive/Desktop/Adaptive%20Reinforcement%20Learning-Based%20CPU%20Scheduler%20for%20Dynamic%20Workload%20Optimization/docs/PROJECT_GUIDE.md)**: Step-by-step structural walkthrough of the simulator components.

---

## 📝 License
Distributed under the **MIT License**. See `LICENSE` for details.
