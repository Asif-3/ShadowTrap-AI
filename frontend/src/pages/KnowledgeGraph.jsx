import { useState, useEffect, useMemo } from 'react'
import ReactFlow, { Background, Controls, MiniMap, useNodesState, useEdgesState } from 'reactflow'
import 'reactflow/dist/style.css'
import { knowledgeGraphAPI } from '../api/client'
import { GlassCard, LoadingSpinner, EmptyState, SentinelButton, PageHeader, SectionHeader } from '../components/common'
import { Network, RefreshCw, Search, Filter, Maximize2 } from 'lucide-react'

// Column X offsets for layered topological layout: IP -> Session -> Command/File -> Stage/MITRE
const LAYER_X = {
  ip: 40,
  session: 280,
  command: 540,
  file: 540,
  stage: 800,
  mitre: 800,
}

const TYPE_COLORS = {
  ip: { bg: 'rgba(77, 184, 255, 0.1)', border: '#4DB8FF', text: '#4DB8FF' },
  session: { bg: 'rgba(255, 77, 103, 0.1)', border: '#FF4D67', text: '#FF4D67' },
  command: { bg: 'rgba(155, 108, 255, 0.1)', border: '#9B6CFF', text: '#9B6CFF' },
  file: { bg: 'rgba(245, 196, 81, 0.1)', border: '#F5C451', text: '#F5C451' },
  stage: { bg: 'rgba(32, 230, 122, 0.1)', border: '#20E67A', text: '#20E67A' },
  mitre: { bg: 'rgba(0, 245, 160, 0.1)', border: '#00F5A0', text: '#00F5A0' },
}

export default function KnowledgeGraphPage() {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [loading, setLoading] = useState(true)
  const [selectedNode, setSelectedNode] = useState(null)
  const [searchFilter, setSearchFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('all')
  const [rfInstance, setRfInstance] = useState(null)

  const fetchGraph = () => {
    setLoading(true)
    knowledgeGraphAPI.getGraph()
      .then((res) => {
        const rawData = res.data.data || { nodes: [], edges: [] }
        const rawNodes = rawData.nodes || []
        const rawEdges = rawData.edges || []

        const typeCounters = { ip: 0, session: 0, command: 0, file: 0, stage: 0, mitre: 0 }

        const flowNodes = rawNodes.map((n) => {
          const nType = n.type || 'command'
          const colX = LAYER_X[nType] || 540
          const rowIdx = typeCounters[nType] || 0
          typeCounters[nType] = (typeCounters[nType] || 0) + 1

          const colY = rowIdx * 90 + 40
          const colors = TYPE_COLORS[nType] || TYPE_COLORS.command

          return {
            id: n.id,
            type: 'default',
            data: { label: n.label, ...n.data, nodeType: nType },
            position: { x: colX, y: colY },
            style: {
              background: '#08110F',
              color: '#E8FFF6',
              border: `1.5px solid ${colors.border}`,
              borderRadius: 8,
              padding: '8px 12px',
              fontSize: 11,
              fontFamily: 'Inter, sans-serif',
              fontWeight: 500,
              maxWidth: 200,
              wordBreak: 'break-word',
              boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
            },
          }
        })

        const flowEdges = rawEdges.map((e) => ({
          id: e.id,
          source: e.source,
          target: e.target,
          label: e.label,
          type: 'smoothstep',
          animated: e.animated,
          style: { stroke: '#00F5A0', strokeWidth: 1.5, opacity: 0.65 },
          labelStyle: { fill: '#9BB7AD', fontSize: 9, fontWeight: 500, fontFamily: 'Inter' },
          labelBgStyle: { fill: '#0B1412', fillOpacity: 0.9, rx: 4, ry: 4 },
        }))

        setNodes(flowNodes)
        setEdges(flowEdges)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchGraph()
  }, [])

  const filteredNodes = useMemo(() => {
    return nodes.filter((n) => {
      const matchType = typeFilter === 'all' || n.data?.nodeType === typeFilter
      const searchLower = searchFilter.toLowerCase()
      const matchSearch = !searchFilter ||
        n.id.toLowerCase().includes(searchLower) ||
        (n.data?.label && String(n.data.label).toLowerCase().includes(searchLower)) ||
        (n.data?.command && String(n.data.command).toLowerCase().includes(searchLower)) ||
        (n.data?.ip && String(n.data.ip).toLowerCase().includes(searchLower))
      return matchType && matchSearch
    })
  }, [nodes, searchFilter, typeFilter])

  const filteredNodeIds = useMemo(() => new Set(filteredNodes.map(n => n.id)), [filteredNodes])

  const filteredEdges = useMemo(() => {
    return edges.filter(e => filteredNodeIds.has(e.source) && filteredNodeIds.has(e.target))
  }, [edges, filteredNodeIds])

  if (loading) return <LoadingSpinner size="lg" text="Loading knowledge topology..." />

  const hasData = nodes.length > 0

  return (
    <div className="space-y-5">
      {/* Page Header */}
      <PageHeader
        icon={Network}
        title="Knowledge Graph"
        badge={`${nodes.length} nodes`}
        subtitle="Topological graph visualization correlating attack IPs, sessions, commands, stages, and MITRE techniques"
        actions={
          <SentinelButton onClick={fetchGraph} variant="secondary" size="sm">
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </SentinelButton>
        }
      />

      {!hasData ? (
        <GlassCard className="p-8">
          <EmptyState preset="graph" />
        </GlassCard>
      ) : (
        <div className="space-y-4">
          {/* Controls Bar */}
          <GlassCard className="p-3 flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-3">
              {/* Search */}
              <div className="relative">
                <Search size={13} className="absolute left-3 top-2.5 text-[#607A71]" />
                <input
                  type="text"
                  value={searchFilter}
                  onChange={(e) => setSearchFilter(e.target.value)}
                  placeholder="Filter nodes by ID/label..."
                  className="pl-8 pr-3 py-1.5 rounded-lg bg-[#08110F] border border-[rgba(0,245,160,0.16)] text-xs text-[#E8FFF6] outline-none focus:border-[#00F5A0] w-52 font-mono"
                />
              </div>

              {/* Type Filter */}
              <div className="flex items-center gap-1">
                <Filter size={13} className="text-[#607A71] mr-1" />
                {['all', 'ip', 'session', 'command', 'stage'].map((t) => (
                  <button
                    key={t}
                    onClick={() => setTypeFilter(t)}
                    className={`px-2.5 py-1 rounded text-[10px] font-mono font-semibold uppercase transition cursor-pointer border ${
                      typeFilter === t
                        ? 'bg-[#00F5A0] text-[#050908] border-[#00F5A0]'
                        : 'bg-[#08110F] text-[#9BB7AD] hover:text-[#E8FFF6] border-[rgba(255,255,255,0.06)]'
                    }`}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={() => rfInstance?.fitView({ padding: 0.2 })}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-[#08110F] border border-[rgba(0,245,160,0.16)] text-[#9BB7AD] hover:text-[#E8FFF6] cursor-pointer"
            >
              <Maximize2 size={12} /> Fit Graph
            </button>
          </GlassCard>

          {/* Graph View + Inspector Panel */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
            <div className="lg:col-span-3 h-[600px] rounded-lg overflow-hidden border border-[rgba(0,245,160,0.14)] bg-[#050908] relative">
              <ReactFlow
                nodes={filteredNodes}
                edges={filteredEdges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onNodeClick={(_, node) => setSelectedNode(node)}
                onInit={setRfInstance}
                fitView
              >
                <Background color="rgba(0, 245, 160, 0.04)" gap={20} size={1} />
                <Controls className="!bg-[#0B1412] !border-[rgba(0,245,160,0.14)] !fill-[#E8FFF6]" />
                <MiniMap
                  nodeColor={(node) => TYPE_COLORS[node.data?.nodeType]?.border || '#00F5A0'}
                  maskColor="rgba(5, 9, 8, 0.8)"
                  className="!bg-[#08110F] !border-[rgba(0,245,160,0.14)] !rounded-lg"
                />
              </ReactFlow>
            </div>

            {/* Node Inspector Panel */}
            <GlassCard className="p-4 flex flex-col justify-between max-h-[600px] overflow-y-auto">
              <div>
                <div className="flex items-center justify-between pb-2 mb-3 border-b border-[rgba(0,245,160,0.12)]">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#E8FFF6] font-sans">
                    Entity Inspector
                  </span>
                  {selectedNode && (
                    <span
                      className="px-2 py-0.5 rounded text-[9px] uppercase font-mono font-semibold"
                      style={{
                        background: TYPE_COLORS[selectedNode.data?.nodeType]?.bg,
                        color: TYPE_COLORS[selectedNode.data?.nodeType]?.text,
                      }}
                    >
                      {selectedNode.data?.nodeType}
                    </span>
                  )}
                </div>

                {selectedNode ? (
                  <div className="space-y-2.5 text-xs">
                    <div>
                      <p className="text-[10px] text-[#607A71] uppercase font-mono">Node ID</p>
                      <code className="font-semibold text-[#00F5A0] font-mono text-[11px] block mt-0.5">{selectedNode.id}</code>
                    </div>
                    <div>
                      <p className="text-[10px] text-[#607A71] uppercase font-mono">Label</p>
                      <p className="font-medium text-[#E8FFF6] mt-0.5">{selectedNode.data.label}</p>
                    </div>
                    {Object.entries(selectedNode.data).map(([key, val]) => (
                      key !== 'label' && key !== 'nodeType' && (
                        <div key={key} className="pt-1">
                          <p className="text-[10px] text-[#607A71] uppercase font-mono">{key.replace('_', ' ')}</p>
                          <p className="text-[#9BB7AD] font-mono text-[11px] break-all mt-0.5">
                            {typeof val === 'object' ? JSON.stringify(val) : String(val)}
                          </p>
                        </div>
                      )
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-[#607A71] py-12 text-center font-sans">
                    Click any graph node to inspect entity attributes & relationships.
                  </p>
                )}
              </div>

              {selectedNode && (
                <div className="pt-3 border-t border-[rgba(0,245,160,0.12)]">
                  <button
                    onClick={() => setSelectedNode(null)}
                    className="w-full py-1.5 rounded-lg text-xs font-medium bg-[#08110F] text-[#9BB7AD] hover:text-[#E8FFF6] border border-[rgba(255,255,255,0.06)] cursor-pointer"
                  >
                    Clear Selection
                  </button>
                </div>
              )}
            </GlassCard>
          </div>
        </div>
      )}
    </div>
  )
}
