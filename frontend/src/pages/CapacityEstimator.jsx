import { useEffect, useState } from 'react'
import { getCapacity } from '../api/client'

export default function CapacityEstimator() {
  const [withBuffer, setWithBuffer] = useState(true)
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    getCapacity(withBuffer)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [withBuffer])

  if (loading && !data) return <div className="text-slate-400">Loading capacity...</div>
  if (error) return <div className="text-red-400">Error: {error}</div>

  const estimates = data?.estimates ?? {}
  const linkCapacities = data?.link_capacities ?? {}

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-cyan-400">Capacity Estimator</h2>
      <p className="text-slate-400">
        Required FH link capacity with 1% permissible packet loss. Toggle buffer (4 symbols / 143 μs) to compare.
      </p>

      <div className="flex items-center gap-4">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={withBuffer}
            onChange={(e) => setWithBuffer(e.target.checked)}
            className="rounded border-slate-600 bg-slate-800 text-cyan-500"
          />
          <span className="text-slate-300">With Buffer (4 symbols / 143 μs)</span>
        </label>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {Object.entries(estimates).map(([linkName, est]) => (
          <div key={linkName} className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
            <h3 className="text-cyan-400 font-semibold mb-3 capitalize">{linkName.replace('_', ' ')}</h3>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-400">Peak throughput</span>
                <span className="font-mono text-slate-200">{(est.peak_throughput_gbps ?? 0).toFixed(2)} Gbps</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">With buffer</span>
                <span className="font-mono text-emerald-400">{(est.with_buffer_gbps ?? 0).toFixed(2)} Gbps</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Without buffer</span>
                <span className="font-mono text-amber-400">{(est.without_buffer_gbps ?? 0).toFixed(2)} Gbps</span>
              </div>
              <div className="flex justify-between text-slate-500">
                <span>Loss budget</span>
                <span>{est.packet_loss_budget_percent ?? 1}%</span>
              </div>
            </dl>
          </div>
        ))}
      </div>

      <div className="text-sm text-slate-500">
        Buffer reduces required capacity by smoothing short bursts. Without buffer, capacity must meet peak to avoid loss.
      </div>
    </div>
  )
}
