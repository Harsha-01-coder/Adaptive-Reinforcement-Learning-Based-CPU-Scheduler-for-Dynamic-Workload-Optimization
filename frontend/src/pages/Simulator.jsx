import React, { useState } from 'react'
import WorkloadConfig from '../components/WorkloadConfig/WorkloadConfig'
import GanttChart from '../components/GanttChart/GanttChart'
import MetricsTable from '../components/MetricsTable/MetricsTable'
import { runSimulation, exportInlineCSV, exportInlinePDF, downloadBlob } from '../api/client'
import { Play, Download, FileText, Settings2, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'

const ALGORITHMS = [
  { id: 'FCFS',        label: 'FCFS',               type: 'Non-Preemptive', color: 'bg-brand-500/20 text-brand-300' },
  { id: 'SJF',         label: 'SJF',                type: 'Non-Preemptive', color: 'bg-cyan-500/20 text-cyan-300' },
  { id: 'SRTF',        label: 'SRTF',               type: 'Preemptive',     color: 'bg-emerald-500/20 text-emerald-300' },
  { id: 'Round Robin', label: 'Round Robin',        type: 'Preemptive',     color: 'bg-amber-500/20 text-amber-300' },
  { id: 'Priority',    label: 'Priority',           type: 'Non-Preemptive', color: 'bg-violet-500/20 text-violet-300' },
  { id: 'RL',          label: 'RL (PPO)',            type: 'Adaptive',       color: 'bg-rose-500/20 text-rose-300' },
]

export default function Simulator() {
  const [processes, setProcesses] = useState([])
  const [algorithm, setAlgorithm] = useState('FCFS')
  const [timeQuantum, setTimeQuantum] = useState(4)
  const [numCores, setNumCores] = useState(1)
  const [agingInterval, setAgingInterval] = useState(10)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('gantt')

  const handleRun = async () => {
    if (!processes.length) { toast.error('Generate or load a workload first'); return }
    setLoading(true)
    try {
      const res = await runSimulation({
        algorithm,
        processes,
        num_cores: numCores,
        time_quantum: timeQuantum,
        aging_interval: agingInterval,
      })
      setResult(res)
      setActiveTab('gantt')
      toast.success(`${res.algorithm} simulation complete!`)
    } catch (e) {
      toast.error(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleExport = async (fmt) => {
    if (!result) return
    try {
      const blob = fmt === 'csv'
        ? await exportInlineCSV(result)
        : await exportInlinePDF(result)
      downloadBlob(blob, `simulation_${result.algorithm.replace(' ', '_')}.${fmt}`)
      toast.success(`Exported as ${fmt.toUpperCase()}`)
    } catch (e) {
      toast.error('Export failed: ' + e.message)
    }
  }

  return (
    <div className="p-6 space-y-5 animate-fade-in">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-5">
        {/* Left sidebar — config */}
        <div className="space-y-4">
          <WorkloadConfig onWorkloadLoad={setProcesses} />

          {/* Algorithm picker */}
          <div className="glass p-4 space-y-3">
            <p className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              <Settings2 size={12} className="inline mr-1" />Algorithm
            </p>
            <div className="space-y-1.5">
              {ALGORITHMS.map(a => (
                <button
                  key={a.id}
                  onClick={() => setAlgorithm(a.id)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-all
                    border ${algorithm === a.id
                      ? 'border-brand-500/40 bg-brand-900/30'
                      : 'border-transparent hover:border-white/10'
                    }`}
                >
                  <div className="flex items-center justify-between">
                    <span className={`font-semibold ${algorithm === a.id ? 'text-brand-200' : 'text-slate-300'}`}>
                      {a.label}
                    </span>
                    <span className={`text-[9px] px-1.5 py-0.5 rounded-full ${a.color}`}>{a.type}</span>
                  </div>
                </button>
              ))}
            </div>

            {/* Algorithm parameters */}
            <div className="space-y-2 pt-1 border-t border-white/10">
              <div>
                <label className="label">Cores (1–8)</label>
                <input className="input" type="number" min={1} max={8}
                       value={numCores} onChange={e => setNumCores(+e.target.value)} />
              </div>
              {algorithm === 'Round Robin' && (
                <div>
                  <label className="label">Time Quantum</label>
                  <input className="input" type="number" min={0.5} step={0.5}
                         value={timeQuantum} onChange={e => setTimeQuantum(+e.target.value)} />
                </div>
              )}
              {algorithm === 'Priority' && (
                <div>
                  <label className="label">Aging Interval</label>
                  <input className="input" type="number" min={0} step={1}
                         value={agingInterval} onChange={e => setAgingInterval(+e.target.value)} />
                </div>
              )}
            </div>

            <button
              onClick={handleRun}
              disabled={loading || !processes.length}
              className="btn-primary w-full"
              id="btn-run-simulation"
            >
              {loading
                ? <><Loader2 size={14} className="animate-spin" /> Simulating...</>
                : <><Play size={14} /> Run Simulation</>
              }
            </button>
          </div>
        </div>

        {/* Main content */}
        <div className="lg:col-span-3 space-y-4">
          {/* Result header */}
          {result && (
            <div className="glass p-4 flex items-center justify-between flex-wrap gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold gradient-text">{result.algorithm}</span>
                  <span className="badge-brand text-[10px]">{result.processes?.length} processes</span>
                  <span className="badge-green text-[10px]">{result.execution_time_ms?.toFixed(1)}ms</span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5">
                  Makespan: {result.metrics?.makespan?.toFixed(2)} tu ·
                  CPU: {result.metrics?.cpu_utilization?.toFixed(1)}%
                </p>
              </div>
              <div className="flex gap-2">
                <button onClick={() => handleExport('csv')} className="btn-secondary py-1.5 px-3 text-xs">
                  <Download size={12} /> CSV
                </button>
                <button onClick={() => handleExport('pdf')} className="btn-secondary py-1.5 px-3 text-xs">
                  <FileText size={12} /> PDF
                </button>
              </div>
            </div>
          )}

          {/* Tab strip */}
          <div className="flex gap-1 p-1 bg-surface-900/60 rounded-xl w-fit">
            {['gantt', 'metrics', 'processes'].map(t => (
              <button key={t} onClick={() => setActiveTab(t)}
                className={`px-4 py-1.5 text-xs font-medium rounded-lg capitalize transition-all ${
                  activeTab === t ? 'bg-brand-600 text-white' : 'text-slate-400 hover:text-white'
                }`}>
                {t === 'gantt' ? 'Gantt Chart' : t === 'metrics' ? 'Metrics' : 'Process Table'}
              </button>
            ))}
          </div>

          {/* Tab content */}
          {activeTab === 'gantt' && (
            <GanttChart
              gantt={result?.gantt ?? []}
              processes={result?.processes ?? []}
              algorithm={result?.algorithm ?? ''}
            />
          )}
          {activeTab === 'metrics' && result && (
            <MetricsTable processes={[]} metrics={result.metrics} />
          )}
          {activeTab === 'processes' && result && (
            <MetricsTable processes={result.processes ?? []} metrics={result.metrics} />
          )}

          {!result && !loading && (
            <div className="glass p-16 text-center text-slate-500">
              <Play size={32} className="mx-auto mb-3 opacity-30" />
              <p className="text-sm">Configure a workload and algorithm, then click Run Simulation</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
