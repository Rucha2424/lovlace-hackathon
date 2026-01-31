import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import TopologyMap from './pages/TopologyMap'
import TrafficAnalysis from './pages/TrafficAnalysis'
import CapacityEstimator from './pages/CapacityEstimator'
import Reports from './pages/Reports'

const nav = [
  { to: '/', label: 'Dashboard' },
  { to: '/topology', label: 'Topology Map' },
  { to: '/traffic', label: 'Traffic Analysis' },
  { to: '/capacity', label: 'Capacity Estimator' },
  { to: '/reports', label: 'Reports' },
]

function Layout({ children }) {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-slate-700 bg-slate-900/80 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <h1 className="text-lg font-semibold text-cyan-400">Fronthaul Network Optimization</h1>
          <nav className="flex gap-1">
            {nav.map(({ to, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `px-3 py-2 rounded text-sm font-medium transition-colors ${
                    isActive ? 'bg-cyan-500/20 text-cyan-400' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'
                  }`
                }
              >
                {label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-6">
        {children}
      </main>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/topology" element={<TopologyMap />} />
          <Route path="/traffic" element={<TrafficAnalysis />} />
          <Route path="/capacity" element={<CapacityEstimator />} />
          <Route path="/reports" element={<Reports />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}
