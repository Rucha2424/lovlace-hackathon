import { useEffect, useState } from 'react'
import { getReports } from '../api/client'

export default function Reports() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    getReports()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="text-slate-400">Loading reports...</div>
  if (error) return <div className="text-red-400">Error: {error}</div>
  if (!data) return null

  const { innovations, tech_stack, feasibility } = data

  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-bold text-cyan-400">Reports</h2>
      <p className="text-slate-400">Summary of innovations and technical feasibility for judging.</p>

      <section>
        <h3 className="text-lg font-semibold text-slate-200 mb-2">Innovations</h3>
        <ul className="list-disc list-inside space-y-2 text-slate-300">
          {(innovations || []).map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>
      </section>

      <section>
        <h3 className="text-lg font-semibold text-slate-200 mb-2">Tech Stack</h3>
        <ul className="list-disc list-inside space-y-1 text-slate-300">
          {(tech_stack || []).map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>
      </section>

      <section>
        <h3 className="text-lg font-semibold text-slate-200 mb-2">Technical Feasibility</h3>
        <p className="text-slate-300">{feasibility}</p>
      </section>
    </div>
  )
}
