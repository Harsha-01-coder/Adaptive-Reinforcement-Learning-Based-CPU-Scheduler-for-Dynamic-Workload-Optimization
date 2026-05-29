import React, { useMemo } from 'react'
import { motion } from 'framer-motion'

// Process color palette — indexed by pid
const COLORS = [
  '#6366f1', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b',
  '#f43f5e', '#3b82f6', '#ec4899', '#14b8a6', '#a78bfa',
  '#fb923c', '#22d3ee', '#4ade80', '#fbbf24', '#e879f9',
]

const IDLE_COLOR = '#1e293b'
const BAR_HEIGHT = 36
const ROW_GAP = 10
const LABEL_WIDTH = 70
const HEADER_HEIGHT = 28
const TICK_INTERVAL_MIN = 5

function getColor(pid) {
  if (pid === -1) return IDLE_COLOR
  return COLORS[(pid - 1) % COLORS.length]
}

function formatTime(t) {
  return t % 1 === 0 ? t.toFixed(0) : t.toFixed(1)
}

export default function GanttChart({ gantt = [], processes = [], algorithm = '' }) {
  const { maxTime, minTime, cores, scale, width } = useMemo(() => {
    if (!gantt.length) return { maxTime: 0, minTime: 0, cores: 0, scale: 1, width: 0 }
    const maxTime = Math.max(...gantt.map(e => e.end_time))
    const minTime = Math.min(...gantt.map(e => e.start_time))
    const cores = Math.max(...gantt.map(e => e.core_id ?? 0)) + 1
    const totalDuration = maxTime - minTime
    // Scale: target ~800px width for small workloads, compress for large
    const scale = Math.max(8, Math.min(30, 800 / Math.max(totalDuration, 1)))
    const width = totalDuration * scale
    return { maxTime, minTime, cores, scale, width }
  }, [gantt])

  if (!gantt.length) {
    return (
      <div className="glass p-8 text-center text-slate-500">
        <p className="text-sm">Run a simulation to see the Gantt chart</p>
      </div>
    )
  }

  const chartH = cores * (BAR_HEIGHT + ROW_GAP) + HEADER_HEIGHT + 24
  const totalW = width + LABEL_WIDTH + 40

  // Build tick marks
  const duration = maxTime - minTime
  let tickStep = TICK_INTERVAL_MIN
  while (duration / tickStep > 20) tickStep *= 2
  const ticks = []
  for (let t = 0; t <= maxTime; t += tickStep) ticks.push(t)

  return (
    <div className="glass p-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-sm font-semibold text-white">Gantt Chart</h3>
          <p className="text-xs text-slate-500">{algorithm} · {gantt.length} segments · {cores} core{cores > 1 ? 's' : ''}</p>
        </div>
        {/* Legend */}
        <div className="flex flex-wrap gap-2 max-w-sm justify-end">
          {processes.slice(0, 8).map(p => (
            <div key={p.pid} className="flex items-center gap-1 text-[10px] text-slate-400">
              <div
                className="w-2.5 h-2.5 rounded-sm flex-shrink-0"
                style={{ background: getColor(p.pid) }}
              />
              P{p.pid}
            </div>
          ))}
          {processes.length > 8 && (
            <span className="text-[10px] text-slate-500">+{processes.length - 8} more</span>
          )}
          <div className="flex items-center gap-1 text-[10px] text-slate-400">
            <div className="w-2.5 h-2.5 rounded-sm" style={{ background: IDLE_COLOR, border: '1px solid #334155' }} />
            Idle
          </div>
        </div>
      </div>

      <div className="overflow-x-auto rounded-lg">
        <svg
          width={Math.max(totalW, 400)}
          height={chartH}
          className="font-mono"
        >
          {/* Time axis */}
          {ticks.map(t => {
            const x = LABEL_WIDTH + (t - minTime) * scale
            return (
              <g key={t}>
                <line x1={x} y1={HEADER_HEIGHT - 6} x2={x} y2={chartH - 4}
                      stroke="rgba(255,255,255,0.06)" strokeWidth={1} />
                <text x={x} y={HEADER_HEIGHT - 10} textAnchor="middle"
                      fill="#64748b" fontSize={9}>
                  {formatTime(t)}
                </text>
              </g>
            )
          })}

          {/* Rows per core */}
          {Array.from({ length: cores }, (_, coreId) => {
            const y = HEADER_HEIGHT + coreId * (BAR_HEIGHT + ROW_GAP)
            const coreEntries = gantt.filter(e => (e.core_id ?? 0) === coreId)
            return (
              <g key={coreId}>
                {/* Core label */}
                <text x={LABEL_WIDTH - 8} y={y + BAR_HEIGHT / 2 + 4}
                      textAnchor="end" fill="#64748b" fontSize={10} fontWeight="500">
                  {cores > 1 ? `Core ${coreId}` : 'CPU'}
                </text>
                {/* Row background */}
                <rect x={LABEL_WIDTH} y={y} width={width} height={BAR_HEIGHT}
                      fill="rgba(255,255,255,0.02)" rx={4} />

                {/* Process bars */}
                {coreEntries.map((entry, i) => {
                  const bx = LABEL_WIDTH + (entry.start_time - minTime) * scale
                  const bw = Math.max((entry.end_time - entry.start_time) * scale, 2)
                  const color = getColor(entry.pid)
                  const isIdle = entry.pid === -1
                  return (
                    <g key={i} className="gantt-bar">
                      <rect
                        x={bx} y={y + 3} width={bw} height={BAR_HEIGHT - 6}
                        fill={color}
                        fillOpacity={isIdle ? 0.3 : 0.85}
                        rx={3}
                        stroke={isIdle ? '#334155' : 'rgba(255,255,255,0.2)'}
                        strokeWidth={0.5}
                      />
                      {bw > 24 && (
                        <text
                          x={bx + bw / 2} y={y + BAR_HEIGHT / 2 + 4}
                          textAnchor="middle" fill={isIdle ? '#475569' : 'rgba(255,255,255,0.9)'}
                          fontSize={9} fontWeight="600" pointerEvents="none"
                        >
                          {isIdle ? 'idle' : `P${entry.pid}`}
                        </text>
                      )}
                      <title>
                        {isIdle
                          ? `Idle: ${formatTime(entry.start_time)} → ${formatTime(entry.end_time)}`
                          : `P${entry.pid}: ${formatTime(entry.start_time)} → ${formatTime(entry.end_time)} (${formatTime(entry.duration)})`
                        }
                      </title>
                    </g>
                  )
                })}
              </g>
            )
          })}
        </svg>
      </div>
    </div>
  )
}
