import axios from 'axios'

export const BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

export const getWebSocketUrl = (path) => {
  const base = import.meta.env.VITE_API_URL || (window.location.origin.includes('localhost') ? 'http://127.0.0.1:8000' : window.location.origin)
  const url = new URL(path, base)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  return url.toString()
}

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

// Response interceptor for error normalization
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail || err.message || 'Unknown error'
    return Promise.reject(new Error(msg))
  }
)

// ── Workload ──────────────────────────────────────────────────────────────────
export const generateWorkload = (mode = 'medium', n = null, seed = null) =>
  api.get('/api/workload/generate', { params: { mode, n, seed } }).then(r => r.data)

export const uploadWorkload = (file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/api/workload/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data)
}

// ── Algorithms ────────────────────────────────────────────────────────────────
export const getAlgorithms = () =>
  api.get('/api/algorithms').then(r => r.data)

// ── Simulation ────────────────────────────────────────────────────────────────
export const runSimulation = (payload) =>
  api.post('/api/simulate', payload).then(r => r.data)

// ── Benchmark ─────────────────────────────────────────────────────────────────
export const runBenchmark = (payload) =>
  api.post('/api/benchmark/run', payload).then(r => r.data)

// ── RL Agent ──────────────────────────────────────────────────────────────────
export const getRLStatus = () =>
  api.get('/api/rl/status').then(r => r.data)

export const startTraining = (payload) =>
  api.post('/api/rl/train', payload).then(r => r.data)

export const evaluateModel = (params = {}) =>
  api.post('/api/rl/evaluate', null, { params }).then(r => r.data)

// ── Export ────────────────────────────────────────────────────────────────────
export const exportSimulationCSV = (simulationId) =>
  api.get(`/api/export/${simulationId}/csv`, { responseType: 'blob' })

export const exportSimulationPDF = (simulationId) =>
  api.get(`/api/export/${simulationId}/pdf`, { responseType: 'blob' })

export const exportInlineCSV = (simulationResult) =>
  api.post('/api/export/inline/csv', simulationResult, { responseType: 'blob' })

export const exportInlinePDF = (simulationResult) =>
  api.post('/api/export/inline/pdf', simulationResult, { responseType: 'blob' })

// ── Health ────────────────────────────────────────────────────────────────────
export const getHealth = () =>
  api.get('/api/health').then(r => r.data)

// ── Helpers ───────────────────────────────────────────────────────────────────
export const downloadBlob = (blobResponse, filename) => {
  const url = window.URL.createObjectURL(blobResponse.data)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

export default api
