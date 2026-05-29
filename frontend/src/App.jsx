import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Sidebar from './components/Layout/Sidebar'
import Header from './components/Layout/Header'
import Dashboard from './pages/Dashboard'
import Simulator from './pages/Simulator'
import Benchmark from './pages/Benchmark'
import RLAgent from './pages/RLAgent'
import Docs from './pages/Docs'

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen overflow-hidden bg-surface-950">
        {/* Sidebar */}
        <Sidebar />

        {/* Main area */}
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
          <Header />
          <main className="flex-1 overflow-y-auto">
            <Routes>
              <Route path="/"          element={<Dashboard />} />
              <Route path="/simulator" element={<Simulator />} />
              <Route path="/benchmark" element={<Benchmark />} />
              <Route path="/rl-agent"  element={<RLAgent />} />
              <Route path="/docs"      element={<Docs />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  )
}
