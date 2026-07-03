# 🧠 Adaptive Reinforcement Learning-Based CPU Scheduler: Project Summary & Interview Prep

This document serves as a comprehensive guide to understanding your project from top to bottom. It is designed to help you quickly review the architecture, data flow, and underlying logic, as well as prepare you for technical interviews.

---

## 1. 🌟 Overall Project Summary
This project is a **production-quality, full-stack CPU scheduling simulator**. It benchmarks traditional Operating System (OS) CPU scheduling algorithms (like FCFS, Round Robin, etc.) against an **Adaptive Reinforcement Learning (RL) agent**. 

The RL agent is trained using **Proximal Policy Optimization (PPO)** within a custom **Gymnasium** environment. The backend is powered by **FastAPI** (handling REST APIs and WebSockets), and the frontend is a sleek, dark-mode **React** dashboard that visualizes multi-core Gantt charts and live training metrics in real-time.

---

## 2. 🛠️ Tech Stack & Brief Explanation

### **Backend (Python 3.11, FastAPI, SQLite)**
*   **FastAPI**: A modern, high-performance web framework used for building the REST API and handling WebSockets. It is asynchronous, making it perfect for handling I/O bound tasks like database queries.
*   **SQLAlchemy (Async) & SQLite**: Used for the database layer to store benchmark results and workload scenarios. SQLAlchemy is an Object Relational Mapper (ORM) that translates Python objects into SQL tables.
*   **Pydantic v2**: Used for data validation. It ensures that the JSON data coming from the frontend exactly matches the expected Python data types.

### **Machine Learning / RL (Stable-Baselines3, Gymnasium, PyTorch)**
*   **Gymnasium (formerly OpenAI Gym)**: A standard API for reinforcement learning. We built a custom environment (`CPUSchedulerEnv`) that simulates a CPU ready-queue and processes.
*   **Stable-Baselines3 (SB3)**: A library containing reliable implementations of RL algorithms. We used SB3 to implement the PPO model.
*   **PyTorch**: The underlying deep learning framework that powers the neural networks in SB3.

### **Frontend (React 18, Vite, TailwindCSS, Recharts)**
*   **React 18 & Vite**: The core UI library and build tool. Vite provides a blazing-fast development server.
*   **TailwindCSS**: A utility-first CSS framework used to build the modern, responsive, dark-mode UI.
*   **Recharts**: A charting library used to render the complex CPU Gantt charts and real-time training graphs.

### **Infrastructure (Docker)**
*   **Docker & Docker Compose**: Used to containerize the application, ensuring it runs the exact same way on any machine without "it works on my machine" issues.

---

## 3. 🔄 How it Works: Architecture & Data Flow

### **The Working Flow**
1.  **User Input**: The user opens the React dashboard and specifies a workload (e.g., 50 processes, mix of CPU-bound and I/O-bound tasks).
2.  **API Request**: The React frontend sends an HTTP POST request with this configuration to the FastAPI backend (`/api/simulate` or `/api/benchmark`).
3.  **Simulation Execution**: 
    *   If a traditional scheduler (e.g., Round Robin) is selected, the backend runs standard algorithmic logic.
    *   If the **RL Agent** is selected, the backend initializes the custom `CPUSchedulerEnv`. At every time step, the environment passes the current "State" of the CPU to the trained PPO model. The model outputs an "Action" (which process to run next), and the environment steps forward in time.
4.  **Result Compilation**: The backend calculates metrics (Average Waiting Time, Turnaround Time, Context Switches) and generates Gantt chart data.
5.  **Response & Render**: The backend sends JSON back to the frontend, where Recharts renders the Gantt chart and performance metrics.
6.  **Live Training (WebSockets)**: If the user starts a training session, the backend continuously streams loss/reward metrics via a WebSocket connection directly to a live chart on the frontend.

### **Where is the data?**
*   **Transient Data**: The actual process simulation (burst times, remaining times) lives in the RAM/memory of the Python backend during the simulation.
*   **Persistent Data**: Historical benchmark comparisons and saved workload configurations are stored persistently in the `scheduler.db` SQLite database using SQLAlchemy.

---

## 4. 📚 Topics Covered
1.  **Operating Systems**: Process lifecycle, Context Switching, CPU Scheduling Algorithms, Starvation, Aging.
2.  **Reinforcement Learning**: Markov Decision Processes (MDP), State Space, Action Space, Reward Engineering, Proximal Policy Optimization (PPO).
3.  **Full-Stack Web Development**: RESTful API design, WebSocket streaming, React component architecture, Asynchronous Python.

---

## 5. ⏱️ Schedulers Defined (With Easy Examples)

1.  **First-Come, First-Served (FCFS)**
    *   **Definition**: Processes are executed in the exact order they arrive in the ready queue. Non-preemptive.
    *   **Example**: Buying tickets at a movie theater. The first person in line gets their ticket first, regardless of how long it takes.
2.  **Shortest Job First (SJF)**
    *   **Definition**: The process with the smallest total execution (burst) time is selected next. Non-preemptive.
    *   **Example**: Checking out at a grocery store. The cashier lets the person with 1 item check out before the person with a full shopping cart.
3.  **Shortest Remaining Time First (SRTF)**
    *   **Definition**: The preemptive version of SJF. If a new process arrives that requires less time than the currently running process, the CPU switches to the new process.
    *   **Example**: You are reading a long book. You receive a text message (short task). You put the book down, answer the text, and then resume reading.
4.  **Round Robin (RR)**
    *   **Definition**: Each process gets a small, fixed time slice (quantum). Once the time is up, it is moved to the back of the line.
    *   **Example**: A teacher during office hours giving exactly 5 minutes to each student in line, cycling through the line repeatedly until everyone's questions are answered.
5.  **Priority Scheduling (With Aging)**
    *   **Definition**: Processes have a priority score. The highest priority runs first. *Aging* gradually increases the priority of processes that wait too long, preventing them from starving.
    *   **Example**: Boarding an airplane. First-class (high priority) boards first. However, if a regular passenger waits at the gate for 12 hours (aging), the airline might bump them up so they aren't stuck forever.

---

## 6. 🧠 Why use PPO? Why not Predefined Datasets?

**Question: Why did you use Reinforcement Learning (PPO) instead of Supervised Learning with a predefined dataset?**

**Answer / Approach:**
*   **Dynamic and Unpredictable Workloads**: Operating system workloads are highly dynamic. Processes arrive randomly and switch between CPU and I/O bursts unpredictably. In Supervised Learning, you need a massive dataset of "perfectly labeled" schedules. Finding the absolute "perfect" schedule for millions of random scenarios is an NP-Hard problem.
*   **Learning by Interacting (Exploration)**: Instead of telling the model *what* to do (Supervised Learning), RL lets the agent interact with the environment (Gymnasium). It tries actions, gets a reward (or penalty), and learns a policy. It can discover novel scheduling strategies that a human might not have thought to label in a dataset.
*   **Why PPO (Proximal Policy Optimization)?**: PPO is the industry standard for continuous/discrete control tasks. I chose it over algorithms like DQN because PPO is highly stable, less sensitive to hyperparameter tuning, and prevents the model from taking destructively large updates that ruin the policy. 

### **The RL Approach Taken (Step-by-Step)**
1.  **State Space (What the AI sees)**: Created a 252-dimensional vector containing the remaining time, wait time, and priority of up to 50 processes in the ready queue, plus global CPU utilization.
2.  **Action Space (What the AI does)**: A discrete action (0 to 49) representing which process in the queue to run next.
3.  **Reward Function (How the AI learns)**: Designed a composite formula:
    *   **Penalties (-)**: High average waiting time, context switching, and starvation.
    *   **Rewards (+)**: High CPU utilization and completing a process.
4.  **Training**: Used Stable-Baselines3 to train the agent over thousands of episodes to maximize this reward.

---

## 7. 🎤 Interview Q&A Preparation

### **Basic / Warm-up Questions**
> **Q: Can you walk me through this project from a high level?**
> **A:** "I built a full-stack simulator to compare traditional CPU schedulers like Round Robin and SJF against a custom Reinforcement Learning agent. The backend is built with FastAPI and runs the simulation logic and RL training using Stable-Baselines3. The frontend is a React application that lets users configure workloads, run benchmarks, and view the results in real-time via WebSockets and Gantt charts."

> **Q: What was the most challenging part of this project?**
> **A:** "Designing the state space and reward function for the RL agent. If I penalized context switching too heavily, the agent would just mimic FCFS and let long processes hog the CPU. If I didn't penalize starvation, it would mimic SJF and let low-priority tasks wait forever. Tuning the reward weights (`W_WAITING`, `W_CONTEXT_SWITCH`, etc.) to find the perfect balance took significant iteration."

### **Operating Systems Questions**
> **Q: What is a Context Switch and why do we want to minimize it?**
> **A:** A context switch is when the CPU stops executing one process, saves its state (registers, program counter), and loads the state of another process. It is pure overhead—the CPU isn't doing actual work during a switch. Our RL agent receives a penalty `W_CONTEXT_SWITCH` to discourage excessive switching.

> **Q: What is Starvation in OS scheduling, and how did you handle it?**
> **A:** Starvation occurs when a process waits indefinitely for the CPU (common in SJF for long processes, or Priority scheduling for low-priority processes). In the traditional schedulers, I implemented *Aging*. In the RL model, I added a `W_STARVATION` penalty based on the maximum waiting time in the ready queue, forcing the AI to eventually schedule old processes.

### **Machine Learning / RL Questions**
> **Q: How exactly did you formulate the State Space for the Gymnasium environment?**
> **A:** It is a flattened vector. For up to 50 processes in the ready queue, I pass normalized values for: Remaining Burst Time, Waiting Time, Priority, Process Type, and a boolean for if the slot is present. I also pass global stats like overall CPU utilization.

> **Q: What happens if the action space outputs an invalid action (e.g., an empty queue slot)?**
> **A:** I implemented action masking. If the PPO agent outputs an index that points to an empty slot in the ready queue, the environment automatically clamps/redirects the action to the process that has been waiting the longest, effectively preventing the simulation from crashing and guiding the agent.

### **Full-Stack / Web Dev Questions**
> **Q: Why did you use WebSockets for the training metrics instead of standard REST API polling?**
> **A:** Training an RL model generates hundreds of data points per second. Using standard HTTP polling (e.g., `setInterval` requesting data every second) would create immense HTTP overhead (headers, connection setups). WebSockets provide a persistent, low-latency, full-duplex connection, making it vastly more efficient for live streaming data to the React dashboard.

> **Q: How does the FastAPI backend handle multiple users or long simulations without blocking?**
> **A:** FastAPI is built on Starlette and uses asynchronous Python (`async`/`await`). Database calls via Async SQLAlchemy don't block the main thread. However, because CPU simulation is CPU-bound, in a production multi-user scenario, we would offload the heavy simulation tasks to a background worker queue like Celery or Redis Queue (RQ) so the main API thread remains responsive.
