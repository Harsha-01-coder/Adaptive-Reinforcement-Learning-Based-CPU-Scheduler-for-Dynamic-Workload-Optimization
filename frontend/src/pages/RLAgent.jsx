import React, { useEffect, useState } from 'react'
import RLTrainingPanel from '../components/RLTraining/RLTrainingPanel'
import { evaluateModel, getRLStatus } from '../api/client'
import { Brain, CheckCircle2, Info, Loader2, BarChart3 } from 'lucide-react'
import toast from 'react-hot-toast'

export default function RLAgent() {
  const [modelStatus, setModelStatus] = useState(null)
  const [evalResult, setEvalResult] = useState(null)
  const [evalLoading, setEvalLoading] = useState(false)

  useEffect(() => {
    getRLStatus().then(setModelStatus).catch(() => {})
    const poll = setInterval(() => {
      getRLStatus().then(setModelStatus).catch(() => {})
    }, 5000)
    return () => clearInterval(poll)
  }, [])

  const handleEvaluate = async () => {
    setEvalLoading(true)
    try {
      const result = await evaluateModel({ n_episodes: 10, workload_mode: 'medium', seed: 100 })
      setEvalResult(result)
      toast.success('Evaluation complete!')
    } catch (e) {
      toast.error(e.message)
    } finally {
      setEvalLoading(false)
    }
  }

  return (
    <div className="p-6 space-y-5 animate-fade-in">
      {/* Info banner */}
      <div className="glass p-4 border-l-4 border-brand-500 flex items-start gap-3">
        <Info size={16} className="text-brand-400 mt-0.5 flex-shrink-0" />
        <div className="text-xs text-slate-400 space-y-1">
          <p className="font-semibold text-slate-200">About the RL Scheduler</p>
          <p>
            Uses <strong className="text-brand-300">PPO (Proximal Policy Optimization)</strong> from Stable-Baselines3
            on a custom <strong className="text-brand-300">Gymnasium</strong> environment. The agent observes the ready
            queue state and learns to minimize avg. waiting time, context switches, and starvation while maximizing CPU utilization.
          </p>
          <p className="text-slate-500">
            Training 10k steps ≈ 2 min · 100k steps ≈ 10 min · 500k steps ≈ 30 min
          </p>
        </div>
      </div>

      {/* Training panel */}
      <RLTrainingPanel />

      {/* Evaluation section */}
      {modelStatus?.model_available && (
        <div className="glass p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                <BarChart3 size={14} className="text-brand-400" />
                Model Evaluation
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">Run 10 evaluation episodes on medium workload</p>
            </div>
            <button
              onClick={handleEvaluate}
              disabled={evalLoading}
              className="btn-primary"
              id="btn-evaluate-model"
            >
              {evalLoading
                ? <><Loader2 size={14} className="animate-spin" /> Evaluating...</>
                : <><Brain size={14} /> Evaluate Model</>
              }
            </button>
          </div>

          {evalResult && !evalResult.error && (
            <div className="space-y-4">
              {/* Summary stats */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[
                  { label: 'Episodes',       value: evalResult.n_episodes },
                  { label: 'Mean Reward',    value: evalResult.mean_reward?.toFixed(3) },
                  { label: 'Avg Wait',       value: evalResult.mean_waiting_time?.toFixed(2) },
                  { label: 'Avg TAT',        value: evalResult.mean_turnaround_time?.toFixed(2) },
                ].map(s => (
                  <div key={s.label} className="metric-card">
                    <p className="metric-label">{s.label}</p>
                    <p className="text-xl font-bold text-brand-300 font-mono">{s.value}</p>
                  </div>
                ))}
              </div>

              {/* Episode table */}
              <div className="table-wrapper">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="table-head">
                      {['Episode', 'Reward', 'Avg Wait', 'Avg TAT', 'CPU %', 'CTX SW', 'Completion'].map(h => (
                        <th key={h} className="px-4 py-3">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {evalResult.episode_stats?.map(ep => (
                      <tr key={ep.episode} className="table-row">
                        <td className="table-cell font-mono text-brand-300">#{ep.episode}</td>
                        <td className="table-cell font-mono text-emerald-300">{ep.total_reward?.toFixed(3)}</td>
                        <td className="table-cell font-mono">{ep.avg_waiting_time?.toFixed(2)}</td>
                        <td className="table-cell font-mono">{ep.avg_turnaround_time?.toFixed(2)}</td>
                        <td className="table-cell font-mono">{ep.cpu_utilization?.toFixed(1)}%</td>
                        <td className="table-cell font-mono">{ep.context_switches}</td>
                        <td className="table-cell">
                          <span className={ep.completion_rate >= 0.9 ? 'text-emerald-400' : 'text-amber-400'}>
                            {(ep.completion_rate * 100).toFixed(0)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {evalResult?.error && (
            <p className="text-sm text-rose-400">{evalResult.error}</p>
          )}
        </div>
      )}

      {/* Architecture info */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          {
            title: 'Observation Space',
            items: ['Ready queue status (padded to 50)', 'Remaining burst times', 'Waiting times', 'Priority levels', 'Process type flags', 'CPU utilization', 'Queue length ratio'],
          },
          {
            title: 'Action Space',
            items: ['Discrete(50)', 'Select index of next process to run', 'Invalid actions auto-masked', 'Runs in TIME_STEP = 1 unit intervals'],
          },
          {
            title: 'Reward Function',
            items: ['−0.4 × Δavg_waiting_time', '−0.1 × context_switch', '+0.2 × cpu_utilization', '−0.2 × starvation_penalty', '+0.1 × completion_bonus'],
          },
        ].map(section => (
          <div key={section.title} className="glass p-4">
            <p className="text-xs font-semibold text-brand-400 uppercase tracking-wider mb-3">
              {section.title}
            </p>
            <ul className="space-y-1.5">
              {section.items.map(item => (
                <li key={item} className="flex items-start gap-2 text-xs text-slate-400">
                  <div className="w-1 h-1 rounded-full bg-brand-500 mt-1.5 flex-shrink-0" />
                  <span className="font-mono">{item}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  )
}
