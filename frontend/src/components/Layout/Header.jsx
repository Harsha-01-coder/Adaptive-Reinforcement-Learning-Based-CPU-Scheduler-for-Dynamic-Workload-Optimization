import React from 'react'
import { useLocation } from 'react-router-dom'
import { Moon, Sun, Github } from 'lucide-react'
import { BASE_URL } from '../../api/client'

const PAGE_META = {
  '/':          { title: 'Dashboard',  subtitle: 'System overview and quick stats' },
  '/simulator': { title: 'Simulator',  subtitle: 'Configure and run CPU scheduling simulations' },
  '/benchmark': { title: 'Benchmark',  subtitle: 'Compare all scheduling algorithms head-to-head' },
  '/rl-agent':  { title: 'RL Agent',   subtitle: 'Train and evaluate the PPO-based scheduler' },
  '/docs':      { title: 'Docs',       subtitle: 'API reference, architecture, and resume guide' },
}

export default function Header() {
  const { pathname } = useLocation()
  const meta = PAGE_META[pathname] || PAGE_META['/']

  return (
    <header className="flex items-center justify-between px-6 py-4 border-b border-white/10
                       bg-surface-900/40 backdrop-blur-sm">
      <div>
        <h1 className="text-lg font-bold text-white">{meta.title}</h1>
        <p className="text-xs text-slate-400 mt-0.5">{meta.subtitle}</p>
      </div>

      <div className="flex items-center gap-3">
        {/* API Docs link */}
        <a
          href={`${BASE_URL}/docs`}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-secondary py-1.5 px-3 text-xs"
        >
          API Docs
        </a>

        <a
          href="https://github.com/Harsha-01-coder/Adaptive-Reinforcement-Learning-Based-CPU-Scheduler-for-Dynamic-Workload-Optimization"
          target="_blank"
          rel="noopener noreferrer"
          className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-400
                     hover:text-white hover:bg-white/10 transition-all"
          title="GitHub"
        >
          <Github size={16} />
        </a>
      </div>
    </header>
  )
}
