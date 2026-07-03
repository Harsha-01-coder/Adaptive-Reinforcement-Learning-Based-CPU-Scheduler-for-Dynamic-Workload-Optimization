import React, { useState } from 'react'
import { Upload, Shuffle, Database, Plus, Trash2, Download } from 'lucide-react'
import { generateWorkload, uploadWorkload } from '../../api/client'
import toast from 'react-hot-toast'

const MODES = [
  { id: 'small',  label: 'Small',  count: '10 procs' },
  { id: 'medium', label: 'Medium', count: '30 procs' },
  { id: 'large',  label: 'Large',  count: '100 procs' },
  { id: 'random', label: 'Random', count: 'varies' },
]

export default function WorkloadConfig({ onWorkloadLoad }) {
  const [mode, setMode] = useState('medium')
  const [n, setN] = useState('')
  const [seed, setSeed] = useState('')
  const [loading, setLoading] = useState(false)
  const [processes, setProcesses] = useState([])
  const [customProcs, setCustomProcs] = useState([])
  const [tab, setTab] = useState('generate') // 'generate' | 'manual' | 'upload'

  const handleGenerate = async () => {
    setLoading(true)
    try {
      const data = await generateWorkload(
        mode,
        n ? parseInt(n) : null,
        seed ? parseInt(seed) : null
      )
      setProcesses(data.processes)
      onWorkloadLoad(data.processes)
      toast.success(`Generated ${data.n_processes} processes (${mode})`)
    } catch (e) {
      toast.error(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setLoading(true)
    try {
      const data = await uploadWorkload(file)
      setProcesses(data.processes)
      onWorkloadLoad(data.processes)
      toast.success(`Loaded ${data.n_processes} processes from ${file.name}`)
    } catch (e) {
      toast.error(e.message)
    } finally {
      setLoading(false)
    }
  }

  const addManualProcess = () => {
    setCustomProcs(p => [...p, {
      pid: p.length + 1,
      arrival_time: 0,
      burst_time: 5,
      priority: 5,
      process_type: 'cpu_bound',
    }])
  }

  const updateProc = (idx, field, value) => {
    setCustomProcs(prev => {
      const copy = [...prev]
      copy[idx] = { ...copy[idx], [field]: isNaN(+value) ? value : +value }
      return copy
    })
  }

  const removeProc = (idx) => setCustomProcs(p => p.filter((_, i) => i !== idx))

  const applyManual = () => {
    if (!customProcs.length) { toast.error('Add at least one process'); return }
    setProcesses(customProcs)
    onWorkloadLoad(customProcs)
    toast.success(`Loaded ${customProcs.length} custom processes`)
  }

  return (
    <div className="glass p-4 space-y-4">
      <p className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Workload</p>

      {/* Tab switcher */}
      <div className="flex gap-1 p-1 bg-surface-900 rounded-xl">
        {[
          { id: 'generate', label: 'Generate' },
          { id: 'manual',   label: 'Manual' },
          { id: 'upload',   label: 'Upload CSV' },
        ].map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex-1 py-1.5 text-xs font-medium rounded-lg transition-all ${
              tab === t.id
                ? 'bg-brand-600 text-white'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Generate tab */}
      {tab === 'generate' && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2">
            {MODES.map(m => (
              <button
                key={m.id}
                onClick={() => setMode(m.id)}
                className={`p-2.5 rounded-xl text-left text-xs transition-all border ${
                  mode === m.id
                    ? 'border-brand-500/50 bg-brand-900/30 text-brand-300'
                    : 'border-white/10 text-slate-400 hover:border-white/20'
                }`}
              >
                <p className="font-semibold">{m.label}</p>
                <p className="text-[10px] text-slate-500">{m.count}</p>
              </button>
            ))}
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="label">Count override</label>
              <input className="input" type="number" placeholder="auto"
                     value={n} onChange={e => setN(e.target.value)} min={2} max={200} />
            </div>
            <div>
              <label className="label">Seed</label>
              <input className="input" type="number" placeholder="random"
                     value={seed} onChange={e => setSeed(e.target.value)} />
            </div>
          </div>

          <button onClick={handleGenerate} disabled={loading} className="btn-primary w-full" id="btn-generate-workload">
            <Shuffle size={14} />
            {loading ? 'Generating...' : 'Generate Workload'}
          </button>
        </div>
      )}

      {/* Manual tab */}
      {tab === 'manual' && (
        <div className="space-y-3">
          {customProcs.length > 0 && (
            <div className="grid grid-cols-5 gap-1.5 px-1 text-[10px] font-semibold text-slate-400 uppercase tracking-wider text-center">
              <span>Arrival</span>
              <span>Burst</span>
              <span>Priority</span>
              <span>Type</span>
              <span></span>
            </div>
          )}
          <div className="max-h-64 overflow-y-auto space-y-2 pr-1">
            {customProcs.map((p, i) => (
              <div key={i} className="grid grid-cols-5 gap-1.5 items-center">
                <input
                  className="input px-1.5 py-1 text-xs text-center h-8"
                  type="number"
                  value={p.arrival_time}
                  onChange={e => updateProc(i, 'arrival_time', e.target.value)}
                  min={0}
                />
                <input
                  className="input px-1.5 py-1 text-xs text-center h-8"
                  type="number"
                  value={p.burst_time}
                  onChange={e => updateProc(i, 'burst_time', e.target.value)}
                  min={1}
                />
                <input
                  className="input px-1.5 py-1 text-xs text-center h-8"
                  type="number"
                  value={p.priority}
                  onChange={e => updateProc(i, 'priority', e.target.value)}
                  min={1}
                  max={10}
                />
                <select
                  className="select px-1.5 py-1 text-xs text-center h-8"
                  value={p.process_type}
                  onChange={e => updateProc(i, 'process_type', e.target.value)}
                >
                  <option value="cpu_bound" className="bg-slate-900 text-slate-200">CPU</option>
                  <option value="io_bound" className="bg-slate-900 text-slate-200">I/O</option>
                </select>
                <button
                  onClick={() => removeProc(i)}
                  className="btn-danger p-1.5 flex items-center justify-center h-8 w-full"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            ))}
          </div>
          <button onClick={addManualProcess} className="btn-secondary w-full text-xs">
            <Plus size={12} /> Add Process
          </button>
          <button onClick={applyManual} className="btn-primary w-full" disabled={!customProcs.length}>
            <Database size={14} /> Apply {customProcs.length} Processes
          </button>
        </div>
      )}

      {/* Upload tab */}
      {tab === 'upload' && (
        <div className="space-y-3">
          <label className="block border-2 border-dashed border-white/20 rounded-xl p-6
                            text-center cursor-pointer hover:border-brand-500/50 transition-colors">
            <Upload size={20} className="mx-auto text-slate-500 mb-2" />
            <p className="text-xs text-slate-400">Drop a CSV file or click to browse</p>
            <p className="text-[10px] text-slate-600 mt-1">
              Columns: pid, arrival_time, burst_time, priority, process_type
            </p>
            <input type="file" accept=".csv" className="hidden" onChange={handleUpload} />
          </label>
          <a href="http://127.0.0.1:8000/api/workload/template" download
             className="btn-secondary w-full text-xs flex items-center justify-center gap-2">
            <Download size={12} /> Download Template CSV
          </a>
        </div>
      )}

      {/* Current workload summary */}
      {processes.length > 0 && (
        <div className="border-t border-white/10 pt-3">
          <p className="text-[10px] text-slate-500 mb-2">
            Current workload — {processes.length} processes
          </p>
          <div className="grid grid-cols-3 gap-2">
            {[
              { label: 'CPU-bound', value: processes.filter(p => p.process_type === 'cpu_bound').length },
              { label: 'I/O-bound', value: processes.filter(p => p.process_type === 'io_bound').length },
              { label: 'Max burst',  value: Math.max(...processes.map(p => p.burst_time)).toFixed(1) },
            ].map(s => (
              <div key={s.label} className="text-center">
                <p className="text-sm font-bold text-brand-300">{s.value}</p>
                <p className="text-[9px] text-slate-500">{s.label}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
