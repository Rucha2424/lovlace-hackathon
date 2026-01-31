import { useEffect, useState } from 'react'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { getTopology } from '../api/client'

const typeColors = {
  du: '#0ea5e9',
  link: '#8b5cf6',
  ru: '#06b6d4',
  cell: '#10b981',
}

function topologyToFlow(topology) {
  if (!topology?.nodes?.length) return { nodes: [], edges: [] }
  const nodes = []
  const typeOrder = { du: 0, link: 1, ru: 2, cell: 3 }
  const byType = { du: [], link: [], ru: [], cell: [] }
  topology.nodes.forEach(n => {
    byType[n.type] = byType[n.type] || []
    byType[n.type].push(n)
  })
  const DU_Y = 0, LINK_Y = 80, RU_Y = 160, CELL_Y = 280
  const width = 800
  byType.du.forEach((n, i) => {
    nodes.push({
      id: n.id,
      type: 'default',
      data: { label: n.label },
      position: { x: width / 2 - 40, y: DU_Y },
      style: {
        background: typeColors.du,
        color: '#fff', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 8, padding: '8px 16px', fontSize: 14,
      },
    })
  })
  byType.link.forEach((n, i) => {
    nodes.push({
      id: n.id,
      type: 'default',
      data: { label: n.label },
      position: { x: 80 + (i * (width - 160)) / Math.max(1, byType.link.length - 1), y: LINK_Y },
      style: {
        background: typeColors.link,
        color: '#fff', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 8, padding: '6px 12px', fontSize: 12,
      },
    })
  })
  byType.ru.forEach((n, i) => {
    nodes.push({
      id: n.id,
      type: 'default',
      data: { label: n.label },
      position: { x: 80 + (i * (width - 160)) / Math.max(1, byType.ru.length - 1), y: RU_Y },
      style: {
        background: typeColors.ru,
        color: '#fff', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 8, padding: '6px 12px', fontSize: 12,
      },
    })
  })
    const cellsByRu = { RU_1: [], RU_2: [], RU_3: [] }
    topology.edges.forEach(e => {
      const arr = cellsByRu[e.source]
      if (e.target.startsWith('Cell_') && arr) arr.push(e.target)
    })
  const ruOrder = ['RU_1', 'RU_2', 'RU_3']
  ruOrder.forEach((ruId, ruIdx) => {
    const list = cellsByRu[ruId] || []
    list.forEach((cellId, i) => {
      const node = topology.nodes.find(n => n.id === cellId)
      if (!node) return
      const col = i % 8
      const row = Math.floor(i / 8)
      nodes.push({
        id: node.id,
        type: 'default',
        data: { label: node.label },
        position: { x: 40 + ruIdx * (width / 3) + col * 32, y: CELL_Y + row * 32 },
        style: {
          background: typeColors.cell,
          color: '#fff', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 6, padding: '4px 8px', fontSize: 10,
        },
      })
    })
  })

  const edges = (topology.edges || []).map(e => ({
    id: `${e.source}-${e.target}`,
    source: e.source,
    target: e.target,
    type: 'smoothstep',
    markerEnd: { type: MarkerType.ArrowClosed },
    style: { stroke: '#64748b' },
  }))
  return { nodes, edges }
}

export default function TopologyMap() {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    getTopology()
      .then((topology) => {
        const { nodes: n, edges: e } = topologyToFlow(topology)
        setNodes(n)
        setEdges(e)
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [setNodes, setEdges])

  if (loading) return <div className="text-slate-400">Loading topology...</div>
  if (error) return <div className="text-red-400">Error: {error}</div>

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold text-cyan-400">Topology Map</h2>
      <p className="text-slate-400">DU → Link → RU → Cell hierarchy. Cells are grouped by inferred link (correlated packet loss).</p>
      <div className="h-[600px] rounded-lg border border-slate-700 bg-slate-900/50">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          fitView
          attributionPosition="bottom-left"
        >
          <Background color="#334155" gap={16} />
          <Controls />
          <MiniMap nodeColor={(n) => n.style?.background || '#475569'} />
        </ReactFlow>
      </div>
    </div>
  )
}
