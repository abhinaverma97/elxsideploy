import React, { useState, useCallback, useEffect } from 'react'
import { buildDesign, generateDesignDetails } from '../api'

import { Button } from '@/components/ui/button'
import { GitBranch, AlertCircle, Maximize2, Cpu, Code, Server, Activity, ShieldAlert, Link, Thermometer, BrainCircuit, ActivitySquare } from 'lucide-react'
import { cn } from "@/lib/utils"

import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
  Handle,
  Position,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import dagre from 'dagre'

// --- 1. Custom Node Component matching ChatGPT Theme ---
const ThemedNode = ({ data }) => {
  const grouped = (data.components || []).reduce((acc, comp) => {
    const cat = comp.category || 'System Core'
    const name = comp.name || comp
    if (!acc[cat]) acc[cat] = []
    acc[cat].push(name)
    return acc
  }, {})

  const categories = Object.keys(grouped)

  return (
    <div className="bg-[#171717] border-2 border-[#38BDF8] rounded-lg shadow-lg min-w-[220px] max-w-[320px] font-sans overflow-hidden">
      <Handle type="target" position={Position.Left} className="w-2 h-2 !bg-[#38BDF8]" />
      <div className="bg-[#2f2f2f] px-3 py-2 border-b border-[#38BDF8]/30">
        <h3 className="text-sm font-semibold text-[#ececec] ">{data.label}</h3>
        {data.type !== 'subsystem' && (
          <span className="text-[10px] text-muted-foreground uppercase">{data.type}</span>
        )}
      </div>
      <div className="p-3 bg-[#171717] flex flex-col gap-3">
        {categories.length > 0 ? categories.map((cat, idx) => (
          <div key={idx} className="flex flex-col gap-1">
            <span className="text-[9px] uppercase font-bold text-[#38BDF8] tracking-widest">{cat}</span>
            <div className="flex flex-col gap-1 pl-1 border-l-2 border-white/10">
              {grouped[cat].map((item, i) => (
                <span key={i} className="text-xs text-[#ececec] truncate">• {item}</span>
              ))}
            </div>
          </div>
        )) : (
          <div className="text-xs text-[#878787] italic">No Components Registered</div>
        )}
      </div>
      <Handle type="source" position={Position.Right} className="w-2 h-2 !bg-[#38BDF8]" />
    </div>
  )
}

const nodeTypes = { customNode: ThemedNode }

// --- 2. Dagre Layout Helper ---
const getLayoutedElements = (nodes, edges, direction = 'LR') => {
  const dagreGraph = new dagre.graphlib.Graph()
  dagreGraph.setDefaultEdgeLabel(() => ({}))
  const isHorizontal = direction === 'LR'
  dagreGraph.setGraph({ rankdir: direction })

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 200, height: 100 })
  })

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target)
  })

  dagre.layout(dagreGraph)

  const newNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id)
    return {
      ...node,
      targetPosition: isHorizontal ? 'left' : 'top',
      sourcePosition: isHorizontal ? 'right' : 'bottom',
      position: {
        x: nodeWithPosition.x - 200 / 2,
        y: nodeWithPosition.y - 100 / 2,
      },
    }
  })

  return { nodes: newNodes, edges }
}

const TABS = [
  { id: 'graph', label: 'Causal Graph', icon: GitBranch },
  { id: 'architecture', label: 'Architecture', icon: Server },
  { id: 'hardware', label: 'Hardware', icon: Cpu },
  { id: 'software', label: 'Software', icon: Code },
  { id: 'interfaces', label: 'Interfaces', icon: ActivitySquare },
  { id: 'risks', label: 'Risks', icon: ShieldAlert },
  { id: 'connections', label: 'Connections', icon: Link },
  { id: 'environment', label: 'Environment', icon: Thermometer },
]

export default function DiagramView({ deviceType }) {
  const [loading, setLoading] = useState(false)
  const [aiLoading, setAiLoading] = useState(false)
  const [error, setError] = useState(null)

  const [activeTab, setActiveTab] = useState('graph')
  const [aiDetails, setAiDetails] = useState(null)

  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [hasGraph, setHasGraph] = useState(false)

  const handleBuild = async () => {
    setLoading(true)
    setError(null)
    setHasGraph(false)
    try {
      const res = await buildDesign(deviceType)
      if (res.data.error) throw new Error(res.data.error)

      const raw = res.data.raw
      if (!raw || !raw.architecture) throw new Error("No raw architecture found")

      const flowNodes = []
      const flowEdges = []

      raw.architecture.forEach(node => {
        flowNodes.push({
          id: node.id,
          type: 'customNode',
          data: { label: node.name, type: node.type, components: node.components || [] },
          position: { x: 0, y: 0 }
        })
      })

      if (raw.interfaces) {
        raw.interfaces.forEach((iface, i) => {
          const sourceExists = flowNodes.some(n => n.id === iface.source)
          const targetExists = flowNodes.some(n => n.id === iface.target)

          if (sourceExists && targetExists) {
            flowEdges.push({
              id: `e-${iface.source}-${iface.target}-${i}`,
              source: iface.source,
              target: iface.target,
              animated: true,
              label: iface.signal || iface.type,
              type: 'default',
              style: { stroke: '#38BDF8', strokeWidth: 1.5 },
              labelStyle: { fill: '#ececec', fontSize: 10, fontWeight: 500 },
              labelBgStyle: { fill: '#171717', stroke: '#2f2f2f' },
              markerEnd: { type: MarkerType.ArrowClosed, color: '#38BDF8' },
            })
          }
        })
      }

      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(flowNodes, flowEdges)
      setNodes(layoutedNodes)
      setEdges(layoutedEdges)
      setHasGraph(true)
      setActiveTab('graph')
    } catch (err) {
      setError(err.message || 'Design build failed. Ensure requirements exist.')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateAI = async () => {
    setAiLoading(true)
    setError(null)
    try {
      const res = await generateDesignDetails(deviceType)
      if (res.data.error) throw new Error(res.data.error)
      setAiDetails(res.data.data)
      setActiveTab('architecture')
    } catch (err) {
      setError(err.message || 'AI Generation failed.')
    } finally {
      setAiLoading(false)
    }
  }

  const RenderTable = ({ headers, data, className }) => (
    <div className={cn("overflow-x-auto rounded-lg border border-white/10", className)}>
      <table className="w-full text-sm text-left">
        <thead className="text-xs uppercase bg-[#212121] text-[#878787] border-b border-white/10">
          <tr>
            {headers.map((h, i) => <th key={i} className="px-4 py-3 font-semibold">{h}</th>)}
          </tr>
        </thead>
        <tbody>
          {data && data.length > 0 ? data.map((row, i) => (
            <tr key={i} className="border-b border-white/5 bg-[#171717] hover:bg-[#212121] transition-colors">
              {Object.values(row).map((val, idx) => (
                <td key={idx} className="px-4 py-3 text-[#ececec]">{val}</td>
              ))}
            </tr>
          )) : (
            <tr><td colSpan={headers.length} className="px-4 py-3 text-center text-[#878787]">No data available</td></tr>
          )}
        </tbody>
      </table>
    </div>
  )

  const renderTabContent = () => {
    if (activeTab === 'graph') {
      return hasGraph ? (
        <div className="flex-1 w-full h-[600px] border border-white/10 rounded-2xl overflow-hidden bg-[#212121] relative shadow-inner">
          <ReactFlow
            nodes={nodes} edges={edges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
            nodeTypes={nodeTypes} fitView className="bg-[#212121]" minZoom={0.2} maxZoom={2}
          >
            <Background gap={16} size={1} color="#2f2f2f" />
            <Controls className="bg-[#171717] fill-white border-[#2f2f2f]" buttonClassName="border-b-[#2f2f2f] hover:bg-[#2f2f2f]" />
            <MiniMap nodeColor="#38BDF8" maskColor="rgba(23, 23, 23, 0.7)" className="bg-[#171717] border border-[#2f2f2f] rounded-lg" />
          </ReactFlow>
        </div>
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center py-32 text-center rounded-2xl border-2 border-dashed border-white/5">
          <Maximize2 className="h-12 w-12 text-muted-foreground/30 mb-4" />
          <p className="text-muted-foreground text-sm font-medium">No architecture matrix synthesized.</p>
        </div>
      )
    }

    if (!aiDetails) {
      return (
        <div className="flex-1 flex flex-col items-center justify-center py-32 text-center rounded-2xl border-2 border-dashed border-white/5">
          <BrainCircuit className="h-12 w-12 text-muted-foreground/30 mb-4" />
          <p className="text-muted-foreground text-sm font-medium">No AI specifications generated yet.</p>
          <p className="text-muted-foreground text-xs mt-1">Click "Generate Groq AI Specs" to compile technical details.</p>
        </div>
      )
    }

    switch (activeTab) {
      case 'architecture':
        return (
          <div className="space-y-6">
            <div className="bg-[#171717] border border-white/10 p-5 rounded-xl text-sm text-[#ececec] leading-relaxed">
              <h4 className="font-semibold text-[#878787] uppercase text-xs tracking-wider mb-2">System Overview</h4>
              {aiDetails.Architecture?.SystemOverview}
            </div>
            <RenderTable headers={['Subsystem Name', 'Components Included']} data={aiDetails.Architecture?.Subsystems?.map(s => ({ n: s.name, c: s.components?.join(', ') }))} />
            <div className="bg-[#171717] border border-white/10 p-5 rounded-xl text-sm text-[#ececec] leading-relaxed">
              <h4 className="font-semibold text-[#878787] uppercase text-xs tracking-wider mb-2">Mechanical Overview</h4>
              {aiDetails.Architecture?.MechanicalOverview}
            </div>
            <RenderTable headers={['Mechanical Assembly', 'Details']} data={aiDetails.Architecture?.MechanicalAssemblies} />
          </div>
        )
      case 'hardware':
        return (
          <div className="space-y-6">
            <h4 className="font-semibold text-[#878787] uppercase text-xs tracking-wider">Components Bill of Materials (BOM)</h4>
            <RenderTable headers={['Part Number', 'Manufacturer', 'Package', 'Specifications', 'Cost']} data={aiDetails.Hardware?.ComponentsTable} />
            <h4 className="font-semibold text-[#878787] uppercase text-xs tracking-wider">Power Tree Distribution</h4>
            <RenderTable headers={['Rail', 'Regulator', 'Load Distribution']} data={aiDetails.Hardware?.PowerTree} />
          </div>
        )
      case 'software':
        return (
          <div className="space-y-6">
            <div className="bg-[#171717] border border-white/10 p-5 rounded-xl text-sm text-[#ececec] leading-relaxed">
              <h4 className="font-semibold text-[#878787] uppercase text-xs tracking-wider mb-2">IPC Mechanisms</h4>
              {aiDetails.Software?.IPCMechanisms}
            </div>
            <h4 className="font-semibold text-[#878787] uppercase text-xs tracking-wider">Software Modules</h4>
            <RenderTable headers={['Module Name', 'Safety Class', 'Language', 'RTOS Dependency', 'I/O']} data={aiDetails.Software?.SoftwareModules} />
            <h4 className="font-semibold text-[#878787] uppercase text-xs tracking-wider">RTOS Task Schedulabilty</h4>
            <RenderTable headers={['Task Name', 'Priority', 'Period', 'Description']} data={aiDetails.Software?.RTOSTasks} />
          </div>
        )
      case 'interfaces':
        return (
          <div className="space-y-6">
            <h4 className="font-semibold text-[#878787] uppercase text-xs tracking-wider">System Interfaces</h4>
            <RenderTable headers={['Interface Name', 'Protocol', 'Speed', 'Voltage']} data={aiDetails.Interfaces?.SystemInterfaces} />
            <h4 className="font-semibold text-[#878787] uppercase text-xs tracking-wider">Signals Mapping</h4>
            <RenderTable headers={['Signal Name', 'Type', 'Range', 'Resolution', 'Rate', 'Unit']} data={aiDetails.Interfaces?.Signals} />
            <h4 className="font-semibold text-[#878787] uppercase text-xs tracking-wider">Data & Power Flows</h4>
            <RenderTable headers={['Flow Path', 'Medium', 'Nominal Value']} data={aiDetails.Interfaces?.DataPowerFlows} />
          </div>
        )
      case 'risks':
        return (
          <div className="space-y-6">
            <h4 className="font-semibold text-[#878787] uppercase text-xs tracking-wider">ISO 14971 Risk Analysis</h4>
            <RenderTable headers={['Hazard', 'Severity', 'Probability', 'Risk Level', 'Mitigation']} data={aiDetails.Risks?.RiskAnalysis} />
            <h4 className="font-semibold text-[#878787] uppercase text-xs tracking-wider">Standards Compliance Matrix</h4>
            <RenderTable headers={['Standard', 'Clause', 'Requirement']} data={aiDetails.Risks?.StandardsCompliance} />
          </div>
        )
      case 'connections':
        return (
          <div className="space-y-6">
            <h4 className="font-semibold text-[#878787] uppercase text-xs tracking-wider">System Graph Topology</h4>
            <RenderTable headers={['Connection Type', 'Source Node', 'Target Node']} data={aiDetails.Connections} />
          </div>
        )
      case 'environment':
        return (
          <div className="space-y-6">
            <h4 className="font-semibold text-[#878787] uppercase text-xs tracking-wider">Operating Environmental Limits</h4>
            <RenderTable headers={['Condition Parameter', 'Specification']} data={aiDetails.Environment?.OperatingConditions} />
          </div>
        )
      default: return null
    }
  }

  return (
    <div className="space-y-6 w-full h-full flex flex-col">
      <div className="flex items-center justify-between pb-4 border-b border-white/5 flex-shrink-0">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Interactive Systems Engineering Dashboard</h2>
          <p className="text-muted-foreground text-sm mt-1">
            Deterministic graph rendering and Groq AI-powered specification decomposition for <strong>{deviceType}</strong>.
          </p>
        </div>
        <div className="flex gap-3">
          <Button onClick={handleBuild} disabled={loading} variant="outline" className="gap-2 border-white/10 bg-[#171717] text-white hover:bg-[#212121]">
            {loading ? 'Synthesizing...' : <><GitBranch className="h-4 w-4 text-[#38BDF8]" /> Generate Deterministic Flow</>}
          </Button>
          <Button onClick={handleGenerateAI} disabled={aiLoading} className="gap-2 bg-[#38BDF8] text-black hover:bg-[#38BDF8]/90 shadow-[0_0_15px_rgba(56,189,248,0.3)]">
            {aiLoading ? 'Compiling AI Specs...' : <><BrainCircuit className="h-4 w-4" /> Generate Groq AI Specs</>}
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-4 border border-destructive/50 bg-destructive/10 rounded-xl flex items-center gap-3 text-sm text-destructive font-medium flex-shrink-0">
          <AlertCircle className="h-5 w-5" />
          {error}
        </div>
      )}

      {/* Segmented Control / Tabs */}
      <div className="flex overflow-x-auto gap-1 bg-[#171717] p-1 rounded-xl border border-white/5 w-fit shrink-0 custom-scrollbar">
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap",
              activeTab === tab.id
                ? "bg-[#2f2f2f] text-white shadow-sm"
                : "text-muted-foreground hover:text-[#ececec] hover:bg-white/5"
            )}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      <div className="flex-1 w-full overflow-y-auto pr-2 custom-scrollbar pb-10">
        {renderTabContent()}
      </div>
    </div>
  )
}