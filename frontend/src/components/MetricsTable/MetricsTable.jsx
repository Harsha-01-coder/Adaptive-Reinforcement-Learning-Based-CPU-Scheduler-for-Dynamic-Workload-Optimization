import React, { useState } from 'react'
import { ArrowUpDown, ChevronUp, ChevronDown } from 'lucide-react'
import clsx from 'clsx'

const COLUMNS = [
  { key: 'pid',             label: 'PID',        align: 'center' },
  { key: 'arrival_time',    label: 'Arrival',    align: 'right' },
  { key: 'burst_time',      label: 'Burst',      align: 'right' },
  { key: 'priority',        label: 'Priority',   align: 'center' },
  { key: 'process_type',    label: 'Type',       align: 'center' },
  { key: 'start_time',      label: 'Start',      align: 'right' },
  { key: 'completion_time', label: 'Completion', align: 'right' },
  { key: 'waiting_time',    label: 'Wait',       align: 'right', highlight: true },
  { key: 'turnaround_time', label: 'TAT',        align: 'right', highlight: true },
  { key: 'response_time',   label: 'Response',   align: 'right' },
  { key: 'context_switches',label: 'CTX SW',     align: 'center' },
]

function SortIcon({ col, sortKey, sortDir }) {
  if (col !== sortKey) return <ArrowUpDown size={10} className="text-slate-600" />
  return sortDir === 'asc'
    ? <ChevronUp size={10} className="text-brand-400" />
    : <ChevronDown size={10} className="text-brand-400" />
}

function TypeBadge({ type }) {
  return type === 'cpu_bound'
    ? <span className="badge-brand text-[10px]">CPU</span>
    : <span className="badge-yellow text-[10px]">I/O</span>
}

export default function MetricsTable({ processes = [], metrics = null }) {
  const [sortKey, setSortKey] = useState('pid')
  const [sortDir, setSortDir] = useState('asc')

  const sorted = [...processes].sort((a, b) => {
    const va = a[sortKey] ?? 0
    const vb = b[sortKey] ?? 0
    return sortDir === 'asc' ? (va > vb ? 1 : -1) : (va < vb ? 1 : -1)
  })

  const handleSort = (key) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('asc') }
  }

  const fmt = (v) => typeof v === 'number' ? v.toFixed(2) : v

  return (
    <div className="space-y-4">
      {/* Summary metrics */}
      {metrics && (
        <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-7 gap-3">
          {[
            { label: 'Avg Wait',    value: metrics.avg_waiting_time?.toFixed(2),    unit: 'tu' },
            { label: 'Avg TAT',     value: metrics.avg_turnaround_time?.toFixed(2), unit: 'tu' },
            { label: 'Avg RT',      value: metrics.avg_response_time?.toFixed(2),   unit: 'tu' },
            { label: 'CPU Util',    value: metrics.cpu_utilization?.toFixed(1),      unit: '%'  },
            { label: 'Throughput',  value: metrics.throughput?.toFixed(3),           unit: '/tu' },
            { label: 'CTX Switches',value: metrics.total_context_switches,           unit: ''   },
            { label: 'Fairness',    value: metrics.fairness_score?.toFixed(3),       unit: ''   },
          ].map(m => (
            <div key={m.label} className="metric-card">
              <p className="metric-label">{m.label}</p>
              <p className="text-xl font-bold text-brand-300">
                {m.value}<span className="text-xs text-slate-500 ml-0.5">{m.unit}</span>
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Process table */}
      <div className="table-wrapper">
        <table className="w-full text-left min-w-[800px]">
          <thead>
            <tr className="table-head">
              {COLUMNS.map(col => (
                <th
                  key={col.key}
                  onClick={() => handleSort(col.key)}
                  className={clsx(
                    'px-4 py-3 cursor-pointer select-none',
                    'hover:text-slate-200 transition-colors',
                    col.align === 'right' && 'text-right',
                    col.align === 'center' && 'text-center',
                    col.highlight && 'text-brand-400',
                  )}
                >
                  <span className="inline-flex items-center gap-1">
                    {col.label}
                    <SortIcon col={col.key} sortKey={sortKey} sortDir={sortDir} />
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((p, i) => (
              <tr key={p.pid} className="table-row">
                <td className="table-cell text-center font-mono text-brand-300 font-semibold">
                  P{p.pid}
                </td>
                <td className="table-cell text-right font-mono">{fmt(p.arrival_time)}</td>
                <td className="table-cell text-right font-mono">{fmt(p.burst_time)}</td>
                <td className="table-cell text-center">
                  <span className="font-mono text-amber-300">{p.priority}</span>
                </td>
                <td className="table-cell text-center">
                  <TypeBadge type={p.process_type} />
                </td>
                <td className="table-cell text-right font-mono">{fmt(p.start_time)}</td>
                <td className="table-cell text-right font-mono">{fmt(p.completion_time)}</td>
                <td className="table-cell text-right font-mono font-semibold text-emerald-300">
                  {fmt(p.waiting_time)}
                </td>
                <td className="table-cell text-right font-mono font-semibold text-cyan-300">
                  {fmt(p.turnaround_time)}
                </td>
                <td className="table-cell text-right font-mono">{fmt(p.response_time)}</td>
                <td className="table-cell text-center">
                  <span className={clsx('font-mono', p.context_switches > 3 && 'text-rose-400')}>
                    {p.context_switches}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {sorted.length === 0 && (
          <div className="py-12 text-center text-slate-500 text-sm">
            No process data — run a simulation first
          </div>
        )}
      </div>
    </div>
  )
}
