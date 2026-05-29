import React, { useState } from 'react'
import { BookOpen, Code2, Cpu, Server, ExternalLink } from 'lucide-react'

const SECTIONS = [
  {
    id: 'overview',
    title: 'Project Overview',
    icon: BookOpen,
    content: `
# Adaptive RL-Based CPU Scheduler

A production-quality CPU scheduling simulator that benchmarks traditional OS scheduling algorithms
against a Reinforcement Learning-based scheduler trained with PPO.

## Algorithms Implemented

| Algorithm | Type | Key Property |
|-----------|------|--------------|
| FCFS | Non-Preemptive | Arrival order |
| SJF | Non-Preemptive | Shortest burst first |
| SRTF | Preemptive | Shortest remaining time |
| Round Robin | Preemptive | Fair time-slicing |
| Priority | Non-Preemptive | Priority + aging |
| RL (PPO) | Adaptive | Learned policy |

## Performance Metrics

- Average Waiting Time
- Average Turnaround Time
- Average Response Time
- CPU Utilization (%)
- Throughput (processes/time unit)
- Context Switch Count
- Fairness Score (Jain's Index)
- Makespan
    `,
  },
  {
    id: 'architecture',
    title: 'Architecture',
    icon: Server,
    content: `
# System Architecture

\`\`\`
┌─────────────────────────────────────────────────┐
│                   Frontend                       │
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
\`\`\`

## Data Flow
1. Frontend generates/uploads workload
2. Backend validates via Pydantic
3. Scheduler runs simulation, returns Gantt + metrics
4. Frontend renders Gantt chart, metrics table, export options
    `,
  },
  {
    id: 'api',
    title: 'API Reference',
    icon: Code2,
    content: `
# REST API Reference

Base URL: \`http://127.0.0.1:8000\`
Docs: \`http://127.0.0.1:8000/docs\`

## Workload

\`\`\`
GET /api/workload/generate?mode=medium&n=30&seed=42
POST /api/workload/upload          (CSV file)
GET  /api/workload/template        (download CSV template)
\`\`\`

## Simulation

\`\`\`
POST /api/simulate
Body: {
  algorithm: "FCFS" | "SJF" | "SRTF" | "Round Robin" | "Priority" | "RL",
  processes: [{ pid, arrival_time, burst_time, priority, process_type }],
  num_cores: 1,
  time_quantum: 4.0,
  aging_interval: 10.0
}
\`\`\`

## Benchmark

\`\`\`
POST /api/benchmark/run
Body: { processes, num_cores, include_rl, time_quantum }
\`\`\`

## RL Agent

\`\`\`
POST /api/rl/train   — start PPO training (background)
GET  /api/rl/status  — training status + reward log
POST /api/rl/evaluate — evaluate trained model
WS   /api/rl/ws/training — live reward updates
\`\`\`

## Export

\`\`\`
GET  /api/export/{simulation_id}/csv
GET  /api/export/{simulation_id}/pdf
POST /api/export/inline/csv    (body = simulation result JSON)
POST /api/export/inline/pdf
\`\`\`
    `,
  },
  {
    id: 'resume',
    title: 'Resume & Interview',
    icon: Cpu,
    content: `
# Resume Talking Points

## ATS-Optimized Project Description

*Adaptive Reinforcement Learning-Based CPU Scheduler for Dynamic Workload Optimization*

Designed and implemented a production-quality CPU scheduling simulator in Python/React that benchmarks
traditional OS scheduling algorithms (FCFS, SJF, Round Robin, Priority) against a custom Reinforcement
Learning scheduler trained with Proximal Policy Optimization (PPO) via Stable-Baselines3.

## Quantifiable Achievements

- Implemented **6 scheduling algorithms** with O(n log n) complexity and multi-core support (1–8 cores)
- Built a custom **Gymnasium environment** with 252-dimensional observation space and composite reward signal
- Achieved **X% lower average waiting time** compared to FCFS baseline using trained PPO agent (replace X after training)
- Exposed **15+ REST API endpoints** via FastAPI with async SQLAlchemy persistence and WebSocket live updates
- Created an interactive **React dashboard** with real-time Gantt chart, benchmark charts, and CSV/PDF export

## System Design Interview Points

**Q: How does the RL scheduler work?**
The agent observes a padded fixed-size vector representing the ready queue: remaining burst time,
waiting time, priority, process type per slot, plus global CPU utilization. It takes a discrete
action selecting which process to run next for one time unit, then receives a reward combining
negative waiting time delta, context switch penalty, CPU utilization bonus, starvation penalty,
and completion bonus. PPO's clipped objective ensures stable convergence.

**Q: Why PPO over DQN?**
Scheduling has a large discrete action space (50 slots). PPO's on-policy nature handles the
non-stationary environment (different workloads each episode) better than off-policy DQN.
PPO also has fewer hyperparameters and more stable training.

**Q: How did you evaluate the RL agent?**
By running the trained model on fixed evaluation workloads (different from training) for N episodes
and comparing avg. waiting time, turnaround time, CPU utilization, and context switches to
traditional schedulers on identical process lists.

## Technical Skills Demonstrated

Python · FastAPI · Gymnasium · Stable-Baselines3 · PyTorch · NumPy · SQLAlchemy ·
React · TailwindCSS · Recharts · Docker · REST API Design · WebSocket · Algorithm Design
    `,
  },
]

function Section({ section }) {
  return (
    <div className="glass p-5">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-8 h-8 rounded-lg bg-brand-600/20 flex items-center justify-center">
          <section.icon size={15} className="text-brand-400" />
        </div>
        <h2 className="text-sm font-bold text-white">{section.title}</h2>
      </div>
      <div className="prose prose-sm prose-invert max-w-none">
        {section.content.trim().split('\n').map((line, i) => {
          if (line.startsWith('# ')) return <h1 key={i} className="text-xl font-bold gradient-text mt-0 mb-3">{line.slice(2)}</h1>
          if (line.startsWith('## ')) return <h2 key={i} className="text-base font-bold text-white mt-4 mb-2">{line.slice(3)}</h2>
          if (line.startsWith('**Q:')) return (
            <p key={i} className="font-semibold text-brand-300 mt-3 text-sm">{line.replace(/\*\*/g, '')}</p>
          )
          if (line.startsWith('```')) return null
          if (line.startsWith('|')) {
            // simple table row
            const cells = line.split('|').filter(c => c.trim() && c.trim() !== '---')
            return cells.length > 0 ? (
              <div key={i} className="flex gap-4 font-mono text-xs py-1 border-b border-white/5">
                {cells.map((c, j) => (
                  <span key={j} className="flex-1 text-slate-400">{c.trim()}</span>
                ))}
              </div>
            ) : null
          }
          if (line.startsWith('- ') || line.startsWith('* ')) {
            return (
              <div key={i} className="flex gap-2 text-xs text-slate-400 py-0.5">
                <span className="text-brand-500 flex-shrink-0">•</span>
                <span>{line.slice(2)}</span>
              </div>
            )
          }
          if (line.trim().startsWith('GET ') || line.trim().startsWith('POST ') || line.trim().startsWith('WS ')) {
            return <code key={i} className="block text-xs font-mono text-emerald-300 py-0.5">{line}</code>
          }
          if (line.trim() && !line.trim().startsWith('Body:') && !line.trim().startsWith('{') && !line.trim().startsWith('}')) {
            return <p key={i} className="text-sm text-slate-400 leading-relaxed">{line}</p>
          }
          if (line.trim()) {
            return <code key={i} className="block text-xs font-mono text-slate-500 pl-4">{line}</code>
          }
          return <br key={i} />
        })}
      </div>
    </div>
  )
}

export default function Docs() {
  const [activeSection, setActiveSection] = useState('overview')

  return (
    <div className="p-6 space-y-5 animate-fade-in">
      {/* Section nav */}
      <div className="flex gap-2 flex-wrap">
        {SECTIONS.map(s => (
          <button
            key={s.id}
            onClick={() => setActiveSection(s.id)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-medium transition-all ${
              activeSection === s.id
                ? 'bg-brand-600 text-white'
                : 'glass text-slate-400 hover:text-white'
            }`}
          >
            <s.icon size={12} />
            {s.title}
          </button>
        ))}
        <a
          href="http://127.0.0.1:8000/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-medium glass text-slate-400 hover:text-white"
        >
          <ExternalLink size={12} /> Swagger UI
        </a>
      </div>

      {/* Content */}
      {SECTIONS.filter(s => s.id === activeSection).map(s => (
        <Section key={s.id} section={s} />
      ))}
    </div>
  )
}
