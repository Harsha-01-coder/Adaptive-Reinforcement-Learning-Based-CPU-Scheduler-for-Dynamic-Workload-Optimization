import React, { useState } from 'react'
import WorkloadConfig from '../components/WorkloadConfig/WorkloadConfig'
import BenchmarkChart from '../components/BenchmarkComparison/BenchmarkChart'
import { runBenchmark, exportInlineCSV, downloadBlob } from '../api/client'
import { BarChart3, Loader2, Download, Trophy } from 'lucide-react'
import toast from 'react-hot-toast'
import clsx from 'clsx'

export default function Benchmark() {
  const [processes, setProcesses] = useState([])
  const [numCores, setNumCores] = useState(1)
  const [timeQuantum, setTimeQuantum] = useState(4)
  const [includeRL, setIncludeRL] = useState(false)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleRun = async () => {
    if (!processes.length) { toast.error('Load a workload first'); return }
    setLoading(true)
    try {
      const res = await runBenchmark({
        processes,
        num_cores: numCores,
        include_rl: includeRL,
        time_quantum: timeQuantum,
      })
      setResult(res)
      toast.success(`Benchmark complete! Best: ${res.best_algorithm}`)
    } catch (e) {
      toast.error(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleExportCSV = async () => {
    if (!result?.results?.length) return
    const bestResult = result.results.find(r => r.algorithm === result.best_algorithm)
    if (!bestResult) return
    try {
      const blob = await exportInlineCSV(bestResult)
      downloadBlob(blob, `benchmark_${result.benchmark_id?.slice(0, 8)}.csv`)
      toast.success('Benchmark CSV exported')
    } catch (e) {
      toast.error('Export failed')
    }
  }

  return (
    <div className="p-6 space-y-5 animate-fade-in">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-5">
        {/* Config panel */}
        <div className="space-y-4">
          <WorkloadConfig onWorkloadLoad={setProcesses} />

          <div className="glass p-4 space-y-3">
            <p className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Benchmark Config</p>

            <div>
              <label className="label">CPU Cores</label>
              <input className="input" type="number" min={1} max={8}
                     value={numCores} onChange={e => setNumCores(+e.target.value)} />
            </div>

            <div>
              <label className="label">RR Time Quantum</label>
              <input className="input" type="number" min={0.5} step={0.5}
                     value={timeQuantum} onChange={e => setTimeQuantum(+e.target.value)} />
            </div>

            <label className="flex items-center gap-2.5 cursor-pointer group">
              <div
                onClick={() => setIncludeRL(v => !v)}
                className={clsx(
                  'w-9 h-5 rounded-full transition-all relative',
                  includeRL ? 'bg-brand-600' : 'bg-surface-700'
                )}
              >
                <div className={clsx(
                  'absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all',
                  includeRL ? 'left-4' : 'left-0.5'
                )} />
              </div>
              <span className="text-xs text-slate-400 group-hover:text-slate-200 transition-colors">
                Include RL (PPO) scheduler
              </span>
            </label>

            <button
              onClick={handleRun}
              disabled={loading || !processes.length}
              className="btn-primary w-full"
              id="btn-run-benchmark"
            >
              {loading
                ? <><Loader2 size={14} className="animate-spin" /> Benchmarking...</>
                : <><BarChart3 size={14} /> Run Benchmark</>
              }
            </button>
          </div>
        </div>

        {/* Results */}
        <div className="lg:col-span-3 space-y-4">
          {result && (
            <>
              <div className="glass p-4 flex items-center justify-between flex-wrap gap-3">
                <div className="flex items-center gap-3">
                  <Trophy size={18} className="text-amber-400" />
                  <div>
                    <p className="text-sm font-bold text-white">
                      Winner: <span className="gradient-text">{result.best_algorithm}</span>
                    </p>
                    <p className="text-xs text-slate-500">
                      {result.n_processes} processes · {result.results?.filter(r => !r.error).length} algorithms compared
                    </p>
                  </div>
                </div>
                <button onClick={handleExportCSV} className="btn-secondary py-1.5 px-3 text-xs">
                  <Download size={12} /> Export CSV
                </button>
              </div>

              {/* Stats table */}
              <div className="table-wrapper">
                <table className="w-full text-left">
                  <thead>
                    <tr className="table-head">
                      {['Rank', 'Algorithm', 'Avg Wait', 'Avg TAT', 'CPU %', 'Throughput', 'Ctx Sw', 'Fairness'].map(h => (
                        <th key={h} className="px-4 py-3">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {result.results
                      .filter(r => !r.error)
                      .sort((a, b) => (result.rankings[a.algorithm] ?? 99) - (result.rankings[b.algorithm] ?? 99))
                      .map(r => (
                        <tr key={r.algorithm} className={clsx(
                          'table-row',
                          r.algorithm === result.best_algorithm && 'bg-brand-900/20'
                        )}>
                          <td className="table-cell font-mono text-amber-400 font-bold">
                            #{result.rankings[r.algorithm]}
                          </td>
                          <td className="table-cell font-semibold text-white">{r.algorithm}</td>
                          <td className="table-cell font-mono text-emerald-300">{r.metrics?.avg_waiting_time?.toFixed(2)}</td>
                          <td className="table-cell font-mono text-cyan-300">{r.metrics?.avg_turnaround_time?.toFixed(2)}</td>
                          <td className="table-cell font-mono">{r.metrics?.cpu_utilization?.toFixed(1)}%</td>
                          <td className="table-cell font-mono">{r.metrics?.throughput?.toFixed(3)}</td>
                          <td className="table-cell font-mono">{r.metrics?.total_context_switches}</td>
                          <td className="table-cell font-mono">{r.metrics?.fairness_score?.toFixed(3)}</td>
                        </tr>
                      ))
                    }
                  </tbody>
                </table>
              </div>

              <BenchmarkChart
                results={result.results.filter(r => !r.error)}
                rankings={result.rankings}
                bestAlgorithm={result.best_algorithm}
              />
            </>
          )}

          {!result && !loading && (
            <div className="glass p-16 text-center text-slate-500">
              <BarChart3 size={32} className="mx-auto mb-3 opacity-30" />
              <p className="text-sm">Load a workload and run the benchmark to see comparisons</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
