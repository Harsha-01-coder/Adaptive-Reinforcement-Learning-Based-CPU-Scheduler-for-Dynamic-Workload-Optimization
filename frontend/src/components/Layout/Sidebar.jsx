import React, { useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, Play, BarChart3, Brain, BookOpen,
  Cpu, ChevronLeft, ChevronRight, Zap
} from 'lucide-react'
import clsx from 'clsx'

const NAV_ITEMS = [
  { to: '/',          icon: LayoutDashboard, label: 'Dashboard',  desc: 'Overview' },
  { to: '/simulator', icon: Play,            label: 'Simulator',  desc: 'Run schedules' },
  { to: '/benchmark', icon: BarChart3,       label: 'Benchmark',  desc: 'Compare all' },
  { to: '/rl-agent',  icon: Brain,           label: 'RL Agent',   desc: 'Train & evaluate' },
  { to: '/docs',      icon: BookOpen,        label: 'Docs',       desc: 'Reference' },
]

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()

  return (
    <aside
      className={clsx(
        'relative flex flex-col h-full bg-surface-900/80 backdrop-blur-sm',
        'border-r border-white/10 transition-all duration-300 ease-in-out',
        collapsed ? 'w-16' : 'w-60'
      )}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-white/10">
        <div className="flex-shrink-0 w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-accent-violet flex items-center justify-center shadow-lg shadow-brand-900/50">
          <Cpu size={18} className="text-white" />
        </div>
        {!collapsed && (
          <div className="min-w-0 animate-fade-in">
            <p className="text-sm font-bold text-white truncate">RL CPU Scheduler</p>
            <p className="text-[10px] text-brand-400 font-medium tracking-wide">ADAPTIVE AI</p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map(({ to, icon: Icon, label, desc }) => {
          const isActive = to === '/'
            ? location.pathname === '/'
            : location.pathname.startsWith(to)

          return (
            <NavLink
              key={to}
              to={to}
              className={clsx(
                'group flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200',
                isActive
                  ? 'bg-brand-600/20 border border-brand-500/30 text-brand-300'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
              )}
              title={collapsed ? label : undefined}
            >
              <Icon
                size={18}
                className={clsx(
                  'flex-shrink-0 transition-colors',
                  isActive ? 'text-brand-400' : 'text-slate-500 group-hover:text-slate-300'
                )}
              />
              {!collapsed && (
                <div className="min-w-0 animate-fade-in">
                  <p className={clsx('text-sm font-medium truncate', isActive && 'text-brand-200')}>
                    {label}
                  </p>
                  <p className="text-[10px] text-slate-500 truncate">{desc}</p>
                </div>
              )}
              {isActive && !collapsed && (
                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-brand-400 flex-shrink-0" />
              )}
            </NavLink>
          )
        })}
      </nav>

      {/* Status dot */}
      {!collapsed && (
        <div className="px-4 py-3 border-t border-white/10">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Zap size={12} className="text-emerald-400" />
            <span>Backend connected</span>
            <div className="ml-auto w-2 h-2 rounded-full bg-emerald-500 animate-pulse-slow" />
          </div>
        </div>
      )}

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(c => !c)}
        className="absolute -right-3 top-20 w-6 h-6 rounded-full bg-surface-800 border border-white/20
                   flex items-center justify-center text-slate-400 hover:text-white
                   hover:bg-brand-600 transition-all duration-200 shadow-lg z-10"
      >
        {collapsed ? <ChevronRight size={12} /> : <ChevronLeft size={12} />}
      </button>
    </aside>
  )
}
