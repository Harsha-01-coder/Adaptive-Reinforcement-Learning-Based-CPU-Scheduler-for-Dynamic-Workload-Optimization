import React, { useEffect, useRef, useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine
} from 'recharts'
import { Brain, Play, Square, RefreshCw, CheckCircle2, XCircle, Loader2 } from 'lucide-react'
import { startTraining, getRLStatus } from '../../api/client'
import toast from 'react-hot-toast'
import clsx from 'clsx'

const STATUS_ICONS = {
  idle:      null,
  training:  <Loader2 size={14} className="animate-spin text-brand-400" />,
  completed: <CheckCircle2 size={14} className="text-emerald-400" />,
  failed:    <XCircle size={14} className="text-rose-400" />,
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="glass px-3 py-2 text-xs">
      <p className="text-slate-400">Step {label?.toLocaleString()}</p>
      <p className="text-brand-300 font-mono font-semibold">
        Reward: {Number(payload[0]?.value).toFixed(4)}
      </p>
    </div>
  )
}

export default function RLTrainingPanel() {
  const [status, setStatus] = useState({ status: 'idle', progress_pct: 0, reward_log: { steps: [], rewards: [] } })
  const [config, setConfig] = useState({ timesteps: 100000, n_envs: 2, workload_mode: 'medium', seed: 42 })
  const [loading, setLoading] = useState(false)
  const wsRef = useRef(null)
  const pollRef = useRef(null)

  // Poll status on mount & while training
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const s = await getRLStatus()
        setStatus(s)
      } catch { /* ignore */ }
    }
    fetchStatus()
    pollRef.current = setInterval(fetchStatus, 3000)
    return () => clearInterval(pollRef.current)
  }, [])

  // WebSocket for live reward updates
  useEffect(() => {
    if (status.status !== 'training') return
    const ws = new WebSocket('ws://127.0.0.1:8000/api/rl/ws/training')
    wsRef.current = ws
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data)
      if (msg.type === 'progress' || msg.type === 'state') {
        setStatus(prev => ({
          ...prev,
          current_timestep: msg.step ?? prev.current_timestep,
          progress_pct: msg.total > 0 ? (msg.step / msg.total * 100) : prev.progress_pct,
          reward_log: msg.data?.reward_log ?? prev.reward_log,
        }))
      }
    }
    return () => ws.close()
  }, [status.status])

  const handleStart = async () => {
    setLoading(true)
    try {
      await startTraining(config)
      toast.success('Training started!')
      setStatus(s => ({ ...s, status: 'training', progress_pct: 0 }))
    } catch (e) {
      toast.error(e.message)
    } finally {
      setLoading(false)
    }
  }

  // Prepare chart data (subsample for performance)
  const chartData = (() => {
    const steps = status.reward_log?.steps ?? []
    const rewards = status.reward_log?.rewards ?? []
    const step = Math.max(1, Math.floor(steps.length / 200))
    return steps
      .filter((_, i) => i % step === 0)
      .map((s, i) => ({ step: s, reward: rewards[i * step] ?? 0 }))
  })()

  const isTraining = status.status === 'training'
  const rewardList = status.reward_log?.rewards ?? []
  const meanReward = rewardList.length
    ? rewardList.slice(-50).reduce((a, b) => a + b, 0) / Math.min(rewardList.length, 50)
    : 0

  return (
    <div className="space-y-5">
      {/* Status bar */}
      <div className="glass p-4 flex items-center gap-4">
        <div className="w-10 h-10 rounded-xl bg-brand-600/20 flex items-center justify-center">
          <Brain size={20} className="text-brand-400" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            {STATUS_ICONS[status.status]}
            <span className="text-sm font-semibold text-white capitalize">{status.status}</span>
            {status.model_available && (
              <span className="badge-green text-[10px]">Model Ready</span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            {isTraining
              ? `Step ${status.current_timestep?.toLocaleString()} / ${status.total_timesteps?.toLocaleString()}`
              : status.status === 'completed'
                ? `Training complete — ${rewardList.length} episodes`
                : 'PPO Agent · Gymnasium Environment'
            }
          </p>
        </div>
        {/* Progress bar */}
        {isTraining && (
          <div className="flex-1 max-w-xs">
            <div className="h-2 bg-surface-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-brand-500 to-accent-violet rounded-full transition-all duration-500"
                style={{ width: `${status.progress_pct}%` }}
              />
            </div>
            <p className="text-[10px] text-slate-500 text-right mt-1">{status.progress_pct?.toFixed(1)}%</p>
          </div>
        )}
      </div>

      {/* Config + stats */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Training config */}
        <div className="glass p-4 space-y-3">
          <p className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Training Config</p>

          <div>
            <label className="label">Total Timesteps</label>
            <select
              className="select"
              value={config.timesteps}
              onChange={e => setConfig(c => ({ ...c, timesteps: +e.target.value }))}
              disabled={isTraining}
            >
              <option value={10000}>10,000 (quick demo)</option>
              <option value={50000}>50,000 (5 min)</option>
              <option value={100000}>100,000 (10 min)</option>
              <option value={500000}>500,000 (30 min)</option>
            </select>
          </div>

          <div>
            <label className="label">Workload Mode</label>
            <select
              className="select"
              value={config.workload_mode}
              onChange={e => setConfig(c => ({ ...c, workload_mode: e.target.value }))}
              disabled={isTraining}
            >
              <option value="small">Small (10 processes)</option>
              <option value="medium">Medium (30 processes)</option>
              <option value="large">Large (100 processes)</option>
            </select>
          </div>

          <div>
            <label className="label">Parallel Envs</label>
            <select
              className="select"
              value={config.n_envs}
              onChange={e => setConfig(c => ({ ...c, n_envs: +e.target.value }))}
              disabled={isTraining}
            >
              {[1, 2, 4, 8].map(n => (
                <option key={n} value={n}>{n} env{n > 1 ? 's' : ''}</option>
              ))}
            </select>
          </div>

          <button
            onClick={handleStart}
            disabled={isTraining || loading}
            className="btn-primary w-full"
            id="btn-start-training"
          >
            {loading ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
            {isTraining ? 'Training...' : 'Start Training'}
          </button>
        </div>

        {/* Live stats */}
        <div className="lg:col-span-2 glass p-4">
          <p className="text-xs font-semibold text-slate-300 mb-3 uppercase tracking-wider">
            Training Reward Curve
          </p>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="step" tickFormatter={v => `${(v/1000).toFixed(0)}k`}
                       tick={{ fontSize: 9 }} />
                <YAxis tick={{ fontSize: 9 }} />
                <Tooltip content={<CustomTooltip />} />
                {rewardList.length > 10 && (
                  <ReferenceLine
                    y={meanReward}
                    stroke="#10b981"
                    strokeDasharray="6 3"
                    label={{ value: 'mean', fill: '#10b981', fontSize: 9 }}
                  />
                )}
                <Line
                  type="monotone" dataKey="reward"
                  stroke="#6366f1" strokeWidth={2}
                  dot={false} activeDot={{ r: 4, fill: '#818cf8' }}
                  name="Episode Reward"
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-44 flex items-center justify-center text-slate-500 text-xs">
              {isTraining ? 'Waiting for first episode...' : 'Start training to see reward curve'}
            </div>
          )}
        </div>
      </div>

      {/* Stats row */}
      {rewardList.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: 'Episodes',       value: rewardList.length },
            { label: 'Mean Reward',    value: meanReward.toFixed(3) },
            { label: 'Best Reward',    value: Math.max(...rewardList).toFixed(3) },
            { label: 'Recent Trend',   value: rewardList.length > 10
                ? ((rewardList.slice(-10).reduce((a,b)=>a+b,0)/10) -
                   (rewardList.slice(-20,-10).reduce((a,b)=>a+b,0)/10)).toFixed(3)
                : '—' },
          ].map(s => (
            <div key={s.label} className="metric-card">
              <p className="metric-label">{s.label}</p>
              <p className="text-lg font-bold text-brand-300 font-mono">{s.value}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
