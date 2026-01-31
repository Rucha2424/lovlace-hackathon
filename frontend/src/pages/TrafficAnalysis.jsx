import { useEffect, useState } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts'
import { getTraffic } from '../api/client'

export default function TrafficAnalysis() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    getTraffic()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="text-slate-400">Loading traffic...</div>
  if (error) return <div className="text-red-400">Error: {error}</div>

  const chartData = Array.isArray(data) ? data : []
  const keys = chartData.length ? Object.keys(chartData[0]).filter(k => k.startsWith('link_') && k.endsWith('_gbps')) : []

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-cyan-400">Traffic Analysis</h2>
      <p className="text-slate-400">Aggregated traffic per link over time (60-second window, Gbps).</p>

      <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
        <ResponsiveContainer width="100%" height={400}>
          <AreaChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="time_sec" stroke="#94a3b8" fontSize={12} />
            <YAxis stroke="#94a3b8" fontSize={12} unit=" Gbps" />
            <Tooltip
              contentStyle={{ background: '#1e293b', border: '1px solid #475569', borderRadius: 8 }}
              labelStyle={{ color: '#e2e8f0' }}
            />
            <Legend />
            {keys.map((k, i) => (
              <Area
                key={k}
                type="monotone"
                dataKey={k}
                name={k.replace('_gbps', '')}
                stroke={['#0ea5e9', '#8b5cf6', '#10b981'][i % 3]}
                fill={['#0ea5e9', '#8b5cf6', '#10b981'][i % 3]}
                fillOpacity={0.2}
                strokeWidth={2}
              />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="text-sm text-slate-500">
        Time normalized: 1 slot = 14 symbols = 500 μs. Data sampled every 2000 slots (~1 s) for visualization.
      </div>
    </div>
  )
}
