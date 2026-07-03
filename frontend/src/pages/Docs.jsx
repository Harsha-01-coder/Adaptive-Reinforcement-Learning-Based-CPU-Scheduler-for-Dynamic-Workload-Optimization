import React, { useState } from 'react'
import {
  BookOpen,
  Code2,
  Cpu,
  Server,
  ExternalLink,
  Zap,
  RefreshCw,
  Clock,
  Activity,
  Layers,
  ArrowRight,
  Database,
  Terminal,
  Copy,
  CheckCircle,
  FileText
} from 'lucide-react'
import toast from 'react-hot-toast'
import { BASE_URL } from '../api/client'

// ─── Sub-Components for Premium Tabs ──────────────────────────────────────────

// 1. PROJECT OVERVIEW TAB
function OverviewTab() {
  const schedulers = [
    { name: 'FCFS', type: 'Non-Preemptive', desc: 'Schedules processes in the exact order they arrive.', key: 'Arrival Order', color: 'border-slate-500/30 text-slate-400 bg-slate-500/5' },
    { name: 'SJF', type: 'Non-Preemptive', desc: 'Selects the ready process with the shortest total execution time.', key: 'Shortest Total Job', color: 'border-blue-500/30 text-blue-400 bg-blue-500/5' },
    { name: 'SRTF', type: 'Preemptive', desc: 'Preempts currently running tasks if a shorter remaining job arrives.', key: 'Shortest Remaining Job', color: 'border-cyan-500/30 text-cyan-400 bg-cyan-500/5' },
    { name: 'Round Robin', type: 'Preemptive', desc: 'Cycles through processes giving each a fixed time quantum.', key: 'Fair Time-Slicing', color: 'border-emerald-500/30 text-emerald-400 bg-emerald-500/5' },
    { name: 'Priority', type: 'Preemptive', desc: 'Schedules by priority; uses aging to prevent low-priority starvation.', key: 'Priority + Aging', color: 'border-amber-500/30 text-amber-400 bg-amber-500/5' },
    { name: 'RL (PPO)', type: 'Adaptive', desc: 'Uses a deep neural network to schedule dynamically based on queue state.', key: 'Learned Policy', color: 'border-brand-500/30 text-brand-300 bg-brand-500/5' },
  ]

  const metrics = [
    { name: 'Avg Waiting Time', desc: 'Average time processes spend idle in the ready queue.', icon: Clock },
    { name: 'Avg Turnaround Time', desc: 'Total time from process arrival to final completion.', icon: Activity },
    { name: 'Avg Response Time', desc: 'Time elapsed between process arrival and its first CPU execution.', icon: Zap },
    { name: 'CPU Utilization', desc: 'Percentage of core cycles spent executing useful workload processes.', icon: Cpu },
    { name: 'Throughput', desc: 'Rate of processes completed per unit of simulation time.', icon: RefreshCw },
    { name: 'Context Switches', desc: 'Count of state saves/loads performed when switching tasks.', icon: Layers },
    { name: 'Fairness Score', desc: 'Jain\'s Fairness Index measuring wait time distribution uniformity.', icon: CheckCircle },
    { name: 'Makespan', desc: 'Total wall-clock duration to clear the entire process workload.', icon: FileText },
  ]

  return (
    <div className="space-y-6">
      <div className="glass p-6 space-y-3 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-brand-500/5 rounded-full blur-3xl" />
        <h1 className="text-2xl font-bold gradient-text">Adaptive RL-Based CPU Scheduler</h1>
        <p className="text-sm text-slate-400 leading-relaxed max-w-3xl">
          This system is a production-quality CPU scheduling simulator. It compares traditional operating system heuristics against a Deep Reinforcement Learning agent trained with Proximal Policy Optimization (PPO) using a custom Gymnasium environment.
        </p>
      </div>

      <div>
        <h2 className="text-sm font-semibold text-white uppercase tracking-wider mb-3">Implemented Schedulers</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {schedulers.map(s => (
            <div key={s.name} className="glass p-4 space-y-3 flex flex-col justify-between hover:border-white/20 transition-colors">
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <h3 className="font-bold text-white text-sm">{s.name}</h3>
                  <span className={`text-[9px] px-2 py-0.5 rounded-full border ${s.color}`}>
                    {s.type}
                  </span>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">{s.desc}</p>
              </div>
              <div className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider pt-2 border-t border-white/5">
                Key metric: {s.key}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-sm font-semibold text-white uppercase tracking-wider mb-3">Tracked Performance Metrics</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {metrics.map(m => (
            <div key={m.name} className="glass p-4 space-y-2 flex flex-col items-start">
              <div className="p-2 bg-brand-600/10 rounded-xl border border-brand-500/20">
                <m.icon size={14} className="text-brand-400" />
              </div>
              <h3 className="font-semibold text-white text-xs pt-1">{m.name}</h3>
              <p className="text-[11px] text-slate-400 leading-normal">{m.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// 2. SYSTEM DESIGN & RL ENVIRONMENT TAB
function RLDesignTab() {
  const states = [
    { label: 'Remaining Burst Time', desc: 'Steps left for process execution (normalized by / 100).' },
    { label: 'Waiting Time', desc: 'Accumulated time slots in ready queue (normalized by / 100).' },
    { label: 'Priority', desc: 'Normalized priority integer (1 to 10 mapped to 0.1 - 1.0).' },
    { label: 'Process Type', desc: 'Binary flag representation: 1 for CPU-bound, 0 for I/O-bound.' },
    { label: 'Slot Presence', desc: 'Boolean indicating whether a process occupies the index.' },
  ]

  const weights = [
    { name: 'Waiting Time Penalty (w1)', pct: 40, color: 'bg-indigo-500', value: '0.4', desc: 'Minimizes overall queuing time.' },
    { name: 'Starvation Penalty (w4)', pct: 20, color: 'bg-rose-500', value: '0.2', desc: 'Penalizes leaving tasks idle for too long.' },
    { name: 'CPU Utilization Reward (w3)', pct: 20, color: 'bg-emerald-500', value: '0.2', desc: 'Encourages keeping cores active.' },
    { name: 'Context Switch Penalty (w2)', pct: 10, color: 'bg-amber-500', value: '0.1', desc: 'Limits swapping CPU registers needlessly.' },
    { name: 'Completion Bonus (w5)', pct: 10, color: 'bg-purple-500', value: '0.1', desc: 'Rewards fully executing a process.' },
  ]

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        
        {/* State Space Card */}
        <div className="glass p-5 space-y-4">
          <div className="flex items-center gap-2">
            <Cpu size={16} className="text-brand-400" />
            <h2 className="text-sm font-semibold text-white uppercase tracking-wider">State Space (Observation)</h2>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            The neural network processes a <strong>252-dimensional observation vector</strong> containing queue state values normalized between 0.0 and 1.0. This prevents exploding gradients and stabilizes PPO convergence:
          </p>
          <div className="space-y-2 pt-2 border-t border-white/5">
            {states.map(s => (
              <div key={s.label} className="text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-1 py-1 border-b border-white/5">
                <span className="font-semibold text-slate-300">{s.label}</span>
                <span className="text-[11px] text-slate-500">{s.desc}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Action Space Card */}
        <div className="glass p-5 space-y-4 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Zap size={16} className="text-brand-400" />
              <h2 className="text-sm font-semibold text-white uppercase tracking-wider">Action Space & Masking</h2>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              The agent outputs a discrete choice mapping to <strong>Discrete(50)</strong> representing ready queue slots.
            </p>
            <div className="p-3 bg-surface-900 rounded-xl border border-white/5 space-y-2">
              <h3 className="text-xs font-semibold text-brand-300">Action Redirection Fallback</h3>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                If the model selects an empty slot index in the process queue (an invalid action), the environment intercepts it and schedules the process with the longest waiting time. This ensures stable simulation cycles and guides learning.
              </p>
            </div>
          </div>
          <div className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold border-t border-white/5 pt-3">
            Algorithm: PPO (Proximal Policy Optimization)
          </div>
        </div>
      </div>

      {/* Rewards Card */}
      <div className="glass p-5 space-y-5">
        <div className="flex items-center gap-2">
          <Activity size={16} className="text-brand-400" />
          <h2 className="text-sm font-semibold text-white uppercase tracking-wider">Reward Signal Engineering</h2>
        </div>
        
        <div className="text-center p-3 bg-surface-900 rounded-xl border border-white/5 font-mono text-xs text-brand-200">
          Reward = - (0.4 * Waiting) - (0.2 * Starvation) - (0.1 * ContextSwitch) + (0.2 * CPUUtil) + (0.1 * Completion)
        </div>

        <div className="space-y-4">
          <h3 className="text-xs text-slate-300 font-semibold">Tuning Weights Config</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {weights.map(w => (
              <div key={w.name} className="space-y-1">
                <div className="flex justify-between text-xs font-semibold text-slate-300">
                  <span>{w.name}</span>
                  <span className="text-brand-400">{w.value}</span>
                </div>
                <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                  <div className={`h-full ${w.color} rounded-full`} style={{ width: `${w.pct}%` }} />
                </div>
                <p className="text-[10px] text-slate-500">{w.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

// 3. ARCHITECTURE & DATA FLOW TAB
function ArchitectureTab() {
  const steps = [
    { title: 'User Setup', desc: 'The client defines process counts, durations, and priorities via the dashboard forms.' },
    { title: 'API Routing', desc: 'Vite client sends REST calls containing the process array payload to the FastAPI router.' },
    { title: 'Env Execution', desc: 'The Gym scheduler processes steps, calculates cores mapping, and records metrics.' },
    { title: 'DB Logging', desc: 'Simulation results are optionally cached in a local SQLite database via SQLAlchemy.' },
    { title: 'Render', desc: 'Dashboard loads response JSON and plots Gantt intervals and benchmarking bars.' }
  ]

  return (
    <div className="space-y-6">
      
      {/* Visual Flow diagram */}
      <div className="glass p-5 space-y-4">
        <h2 className="text-sm font-semibold text-white uppercase tracking-wider">Architecture Flow</h2>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 pt-2">
          {steps.map((s, idx) => (
            <div key={s.title} className="relative flex flex-col items-center text-center p-3 bg-white/5 rounded-xl border border-white/5">
              <div className="w-6 h-6 rounded-full bg-brand-600/20 text-brand-300 flex items-center justify-center text-xs font-bold mb-2">
                {idx + 1}
              </div>
              <h3 className="text-xs font-semibold text-white mb-1">{s.title}</h3>
              <p className="text-[10px] text-slate-400 leading-normal">{s.desc}</p>
              {idx < 4 && (
                <ArrowRight size={14} className="hidden md:block absolute -right-2.5 top-1/2 -translate-y-1/2 text-slate-600 z-10" />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Layer components layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        
        {/* Frontend card */}
        <div className="glass p-5 space-y-3">
          <div className="flex items-center gap-2">
            <Layers size={15} className="text-indigo-400" />
            <h3 className="font-semibold text-sm text-white">Frontend UI Layer</h3>
          </div>
          <ul className="text-xs text-slate-400 space-y-2 list-disc pl-4 leading-relaxed">
            <li><strong>React 18 & Vite</strong>: Instant component rendering and fast production bundling.</li>
            <li><strong>TailwindCSS</strong>: Customized dark mode interfaces with glassmorphic tokens.</li>
            <li><strong>Recharts</strong>: Renders real-time Gantt steps and multi-algorithm benchmark metrics.</li>
          </ul>
        </div>

        {/* Backend Card */}
        <div className="glass p-5 space-y-3">
          <div className="flex items-center gap-2">
            <Server size={15} className="text-cyan-400" />
            <h3 className="font-semibold text-sm text-white">Backend Router Layer</h3>
          </div>
          <ul className="text-xs text-slate-400 space-y-2 list-disc pl-4 leading-relaxed">
            <li><strong>FastAPI</strong>: Asynchronous routes providing rapid simulation and evaluation feeds.</li>
            <li><strong>Pydantic v2</strong>: Validates process payloads coming from the React client.</li>
            <li><strong>SQLAlchemy & SQLite</strong>: Async database transactions logging historical simulator runs.</li>
          </ul>
        </div>

        {/* ML Engine Card */}
        <div className="glass p-5 space-y-3">
          <div className="flex items-center gap-2">
            <Cpu size={15} className="text-brand-300" />
            <h3 className="font-semibold text-sm text-white">ML & Gym Core Engine</h3>
          </div>
          <ul className="text-xs text-slate-400 space-y-2 list-disc pl-4 leading-relaxed">
            <li><strong>Gymnasium</strong>: Models ready queues, cores status, context switching, and wait time states.</li>
            <li><strong>Stable-Baselines3</strong>: High-performance implementation of the PPO algorithm.</li>
            <li><strong>PyTorch</strong>: Provides neural network calculations for actor-critic optimization loops.</li>
          </ul>
        </div>

      </div>
    </div>
  )
}

// 4. API REFERENCE TAB
function ApiTab() {
  const [copiedId, setCopiedId] = useState(null)

  const endpoints = [
    {
      method: 'GET',
      path: '/api/workload/generate',
      desc: 'Generates process workloads based on predefined modes (small, medium, large) and random seeds.',
      color: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
      payload: 'Query params: mode ("small" | "medium" | "large"), n (integer), seed (integer)'
    },
    {
      method: 'POST',
      path: '/api/simulate',
      desc: 'Executes a simulation for a single scheduling algorithm using the processes payload.',
      color: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      payload: `{
  "algorithm": "RL" | "FCFS" | "SJF" | "Round Robin",
  "processes": [{"pid": 1, "arrival_time": 0.0, "burst_time": 5.0}],
  "num_cores": 1
}`
    },
    {
      method: 'POST',
      path: '/api/benchmark/run',
      desc: 'Runs multiple schedulers concurrently against the same workload and returns comparison statistics.',
      color: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      payload: `{
  "processes": [{"pid": 1, "arrival_time": 0.0, "burst_time": 5.0}],
  "num_cores": 1,
  "include_rl": true
}`
    },
    {
      method: 'POST',
      path: '/api/rl/train',
      desc: 'Triggers PPO agent training as a background worker task.',
      color: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      payload: `{
  "timesteps": 100000,
  "workload_mode": "medium",
  "n_envs": 2
}`
    },
    {
      method: 'GET',
      path: '/api/rl/status',
      desc: 'Fetches the current RL training run status, steps, and reward logs.',
      color: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
      payload: null
    },
    {
      method: 'WS',
      path: '/api/rl/ws/training',
      desc: 'WebSocket client connection streaming live reward logs during model training.',
      color: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
      payload: null
    }
  ]

  const handleCopy = (text, id) => {
    navigator.clipboard.writeText(text)
    setCopiedId(id)
    toast.success('Copied path to clipboard')
    setTimeout(() => setCopiedId(null), 2000)
  }

  return (
    <div className="space-y-4">
      <div className="glass p-4 flex items-center justify-between border-brand-500/20 bg-brand-500/5">
        <div className="flex items-center gap-2">
          <Terminal size={15} className="text-brand-400" />
          <p className="text-xs text-slate-300 font-semibold">Swagger UI Interactive Docs: {BASE_URL}/docs</p>
        </div>
        <a href={`${BASE_URL}/docs`} target="_blank" rel="noopener noreferrer" className="btn-secondary text-[11px] py-1 px-3">
          Open Swagger <ExternalLink size={10} className="inline ml-1" />
        </a>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {endpoints.map((e, idx) => (
          <div key={idx} className="glass p-4 space-y-3 hover:border-white/20 transition-colors">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${e.color}`}>
                  {e.method}
                </span>
                <span className="font-mono text-xs text-white select-all">{e.path}</span>
              </div>
              <button onClick={() => handleCopy(e.path, idx)} className="text-slate-500 hover:text-white p-1 rounded transition-colors self-end sm:self-auto">
                {copiedId === idx ? <CheckCircle size={12} className="text-emerald-400" /> : <Copy size={12} />}
              </button>
            </div>
            <p className="text-xs text-slate-400 leading-normal">{e.desc}</p>
            {e.payload && (
              <div className="space-y-1">
                <p className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">Payload / Specs:</p>
                <pre className="bg-surface-900 p-2.5 rounded-xl border border-white/5 font-mono text-[10px] text-slate-300 overflow-x-auto leading-relaxed">
                  {e.payload}
                </pre>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Main Docs Component ───────────────────────────────────────────────────────

export default function Docs() {
  const [activeSection, setActiveSection] = useState('overview')

  const sections = [
    { id: 'overview', title: 'Project Overview', icon: BookOpen },
    { id: 'architecture', title: 'Architecture', icon: Server },
    { id: 'api', title: 'API Reference', icon: Code2 },
    { id: 'system-design', title: 'System Design & RL', icon: Cpu },
  ]

  return (
    <div className="p-6 space-y-5 animate-fade-in">
      
      {/* Navigation tabs */}
      <div className="flex gap-2 flex-wrap pb-2 border-b border-white/5">
        {sections.map(s => (
          <button
            key={s.id}
            onClick={() => setActiveSection(s.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all border ${
              activeSection === s.id
                ? 'bg-brand-600 border-brand-500 text-white shadow-lg shadow-brand-900/30'
                : 'glass border-transparent text-slate-400 hover:text-white hover:border-white/10'
            }`}
          >
            <s.icon size={13} />
            {s.title}
          </button>
        ))}
        <a
          href={`${BASE_URL}/docs`}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold glass border-transparent text-slate-400 hover:text-white hover:border-white/10"
        >
          <ExternalLink size={13} /> Swagger UI
        </a>
      </div>

      {/* Render the Active Tab Content */}
      <div className="mt-2">
        {activeSection === 'overview' && <OverviewTab />}
        {activeSection === 'architecture' && <ArchitectureTab />}
        {activeSection === 'api' && <ApiTab />}
        {activeSection === 'system-design' && <RLDesignTab />}
      </div>
    </div>
  )
}
