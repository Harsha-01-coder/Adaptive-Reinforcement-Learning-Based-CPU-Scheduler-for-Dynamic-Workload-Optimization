import React from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, RadarChart, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts'
import { Trophy, Medal } from 'lucide-react'
import clsx from 'clsx'

const ALGO_COLORS = {
  'FCFS':         '#6366f1',
  'SJF':          '#06b6d4',
  'SRTF':         '#10b981',
  'Round Robin':  '#f59e0b',
  'Priority':     '#a78bfa',
  'RL (PPO)':     '#f43f5e',
}

const METRICS_CONFIG = [
  { key: 'avg_waiting_time',    label: 'Avg Waiting Time',    unit: 'tu',  lowerBetter: true  },
  { key: 'avg_turnaround_time', label: 'Avg Turnaround',      unit: 'tu',  lowerBetter: true  },
  { key: 'avg_response_time',   label: 'Avg Response Time',   unit: 'tu',  lowerBetter: true  },
  { key: 'cpu_utilization',     label: 'CPU Utilization',     unit: '%',   lowerBetter: false },
  { key: 'throughput',          label: 'Throughput',          unit: '/tu', lowerBetter: false },
  { key: 'total_context_switches', label: 'Context Switches', unit: '',    lowerBetter: true  },
  { key: 'fairness_score',      label: 'Fairness (Jain\'s)',  unit: '',    lowerBetter: false },
]

function RankBadge({ rank }) {
  if (rank === 1) return <Trophy size={16} className="text-amber-400" />
  if (rank === 2) return <Medal size={16} className="text-slate-300" />
  if (rank === 3) return <Medal size={16} className="text-amber-600" />
  return <span className="text-xs text-slate-500 font-mono">#{rank}</span>
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="glass px-3 py-2 text-xs space-y-1 min-w-[140px]">
      <p className="font-semibold text-white mb-1">{label}</p>
      {payload.map((entry, i) => (
        <div key={i} className="flex justify-between gap-4">
          <span style={{ color: entry.color }}>{entry.name}</span>
          <span className="font-mono text-white">{Number(entry.value).toFixed(2)}</span>
        </div>
      ))}
    </div>
  )
}

export default function BenchmarkChart({ results = [], rankings = {}, bestAlgorithm = '' }) {
  if (!results.length) {
    return (
      <div className="glass p-8 text-center text-slate-500">
        <p className="text-sm">Run a benchmark to see comparisons</p>
      </div>
    )
  }

  // Prepare bar chart data per metric
  const barData = METRICS_CONFIG.map(({ key, label, unit }) => {
    const entry = { metric: label }
    results.forEach(r => {
      if (r.metrics) entry[r.algorithm] = Number(r.metrics[key] ?? 0)
    })
    return entry
  })

  // Radar chart — normalized scores (0-100, higher = better)
  const radarMetrics = ['avg_waiting_time', 'avg_turnaround_time', 'cpu_utilization', 'throughput', 'fairness_score']
  const radarLabels  = ['Wait↓', 'TAT↓', 'CPU%↑', 'Thru↑', 'Fair↑']
  const maxVals = radarMetrics.map(key =>
    Math.max(...results.map(r => r.metrics?.[key] ?? 0), 1)
  )
  const radarData = radarLabels.map((label, i) => {
    const key = radarMetrics[i]
    const isLower = ['avg_waiting_time', 'avg_turnaround_time'].includes(key)
    const entry = { metric: label }
    results.forEach(r => {
      const v = r.metrics?.[key] ?? 0
      entry[r.algorithm] = isLower
        ? Math.max(0, 100 - (v / maxVals[i]) * 100)
        : (v / maxVals[i]) * 100
    })
    return entry
  })

  const algorithms = results.map(r => r.algorithm)

  return (
    <div className="space-y-6">
      {/* Rankings summary */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {results.map(r => {
          const rank = rankings[r.algorithm] ?? 99
          return (
            <div
              key={r.algorithm}
              className={clsx(
                'glass p-3 text-center transition-all',
                r.algorithm === bestAlgorithm && 'border-brand-500/50 bg-brand-900/20'
              )}
            >
              <div className="flex justify-center mb-1">
                <RankBadge rank={rank} />
              </div>
              <p className="text-xs font-semibold text-white">{r.algorithm}</p>
              <p className="text-[10px] text-slate-500 mt-0.5">
                Wait: {r.metrics?.avg_waiting_time?.toFixed(1)}
              </p>
              {r.algorithm === bestAlgorithm && (
                <span className="badge-green text-[9px] mt-1">Best</span>
              )}
            </div>
          )
        })}
      </div>

      {/* Bar charts for each metric */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Main bar chart — waiting + TAT */}
        <div className="glass p-4">
          <p className="text-xs font-semibold text-slate-300 mb-3">Time Metrics Comparison</p>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={barData.slice(0, 3)} barGap={2} barCategoryGap="30%">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="metric" tick={{ fontSize: 9 }} />
              <YAxis tick={{ fontSize: 9 }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend iconSize={10} wrapperStyle={{ fontSize: 10 }} />
              {algorithms.map(algo => (
                <Bar key={algo} dataKey={algo}
                     fill={ALGO_COLORS[algo] || '#6366f1'}
                     radius={[3, 3, 0, 0]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Radar chart */}
        <div className="glass p-4">
          <p className="text-xs font-semibold text-slate-300 mb-3">Multi-Metric Radar (Higher = Better)</p>
          <ResponsiveContainer width="100%" height={220}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="rgba(255,255,255,0.1)" />
              <PolarAngleAxis dataKey="metric" tick={{ fontSize: 10, fill: '#94a3b8' }} />
              <PolarRadiusAxis tick={{ fontSize: 8, fill: '#64748b' }} domain={[0, 100]} />
              {algorithms.map(algo => (
                <Radar key={algo} name={algo} dataKey={algo}
                       stroke={ALGO_COLORS[algo] || '#6366f1'}
                       fill={ALGO_COLORS[algo] || '#6366f1'}
                       fillOpacity={0.1} />
              ))}
              <Legend iconSize={10} wrapperStyle={{ fontSize: 10 }} />
              <Tooltip content={<CustomTooltip />} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* CPU Utilization & Throughput */}
        <div className="glass p-4">
          <p className="text-xs font-semibold text-slate-300 mb-3">CPU Utilization & Throughput</p>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={[
              { metric: 'CPU Util (%)', ...Object.fromEntries(results.map(r => [r.algorithm, r.metrics?.cpu_utilization ?? 0])) },
              { metric: 'Throughput ×10', ...Object.fromEntries(results.map(r => [r.algorithm, (r.metrics?.throughput ?? 0) * 10])) },
            ]} barGap={2}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="metric" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 9 }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend iconSize={10} wrapperStyle={{ fontSize: 10 }} />
              {algorithms.map(algo => (
                <Bar key={algo} dataKey={algo}
                     fill={ALGO_COLORS[algo] || '#6366f1'}
                     radius={[3, 3, 0, 0]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Context switches & Fairness */}
        <div className="glass p-4">
          <p className="text-xs font-semibold text-slate-300 mb-3">Context Switches & Fairness</p>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={[
              { metric: 'Context Switches', ...Object.fromEntries(results.map(r => [r.algorithm, r.metrics?.total_context_switches ?? 0])) },
              { metric: 'Fairness ×100', ...Object.fromEntries(results.map(r => [r.algorithm, (r.metrics?.fairness_score ?? 0) * 100])) },
            ]} barGap={2}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="metric" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 9 }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend iconSize={10} wrapperStyle={{ fontSize: 10 }} />
              {algorithms.map(algo => (
                <Bar key={algo} dataKey={algo}
                     fill={ALGO_COLORS[algo] || '#6366f1'}
                     radius={[3, 3, 0, 0]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
