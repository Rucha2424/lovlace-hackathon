import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getDashboard } from '../api/client'

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    getDashboard()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="text-slate-400">Loading dashboard...</div>
  if (error) return <div className="text-red-400">Error: {error}</div>
  if (!data) return null

  const { congestion, link_capacities, cell_ids, cell_to_link } = data
  const cells = cell_ids?.length ?? 24
  const totalCapacity = Object.values(link_capacities || {}).reduce((a, b) => a + (typeof b === 'number' ? b : 0), 0)

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-cyan-400">Dashboard</h2>
      <p className="text-slate-400">High-level view: 24 cells, congestion status, and estimated link capacities.</p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
          <div className="text-slate-400 text-sm">Total Cells</div>
          <div className="text-2xl font-bold text-cyan-400">{cells}</div>
        </div>
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
          <div className="text-slate-400 text-sm">Total Estimated Link Capacity</div>
          <div className="text-2xl font-bold text-emerald-400">{totalCapacity.toFixed(2)} Gbps</div>
        </div>
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
          <div className="text-slate-400 text-sm">Links</div>
          <div className="text-2xl font-bold text-violet-400">3</div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold text-slate-200 mb-2">Link capacities (peak Gbps)</h3>
        <div className="flex flex-wrap gap-3">
          {Object.entries(link_capacities || {}).map(([key, val]) => (
            <div key={key} className="bg-slate-800/50 border border-slate-600 rounded-lg px-4 py-2">
              <span className="text-slate-400">{key.replace('_gbps', '')}:</span>{' '}
              <span className="font-mono text-cyan-400">{typeof val === 'number' ? val.toFixed(2) : val} Gbps</span>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold text-slate-200 mb-2">Cells by link</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[0, 1, 2].map((linkId) => {
            const cellsOnLink = Object.entries(cell_to_link || {})
              .filter(([, lid]) => Number(lid) === linkId)
              .map(([cid]) => cid)
            return (
              <div key={linkId} className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
                <div className="text-cyan-400 font-medium mb-2">Link {linkId + 1}</div>
                <div className="flex flex-wrap gap-1">
                  {cellsOnLink.map((cid) => (
                    <span
                      key={cid}
                      className="inline-flex items-center px-2 py-0.5 rounded bg-slate-700 text-slate-300 text-xs"
                    >
                      Cell {cid}
                    </span>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold text-slate-200 mb-2">Congestion (p95 Gbps per cell)</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-2">
          {Object.entries(congestion || {}).slice(0, 24).map(([cellId, info]) => (
            <div
              key={cellId}
              className="bg-slate-800/50 border border-slate-600 rounded p-2 text-center"
            >
              <div className="text-xs text-slate-400">Cell {cellId}</div>
              <div className="font-mono text-cyan-400">{(info.p95_gbps ?? 0).toFixed(2)}</div>
              <div className="text-xs text-slate-500">L{Number(info.link_id) + 1}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="flex gap-3 pt-4">
        <Link
          to="/topology"
          className="px-4 py-2 bg-cyan-500/20 text-cyan-400 rounded-lg hover:bg-cyan-500/30 transition-colors"
        >
          View Topology Map →
        </Link>
        <Link
          to="/traffic"
          className="px-4 py-2 bg-slate-700 text-slate-300 rounded-lg hover:bg-slate-600 transition-colors"
        >
          Traffic Analysis
        </Link>
      </div>
    </div>
  )
}
