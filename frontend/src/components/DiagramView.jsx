import React, { useState, useCallback, useEffect } from 'react'
import { buildDesign, generateDesignDetails, getDetailedDesign, getVerificationMatrix } from '../api'

import { Button } from '@/components/ui/button'
import { GitBranch, AlertCircle, Maximize2, Cpu, Code, Server, Activity, ShieldAlert, Link, Thermometer, ActivitySquare, BrainCircuit } from 'lucide-react'
import { cn } from "@/lib/utils"

import { RenderTable, SectionHeader, InfoBox } from './DiagramViewHelper'

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
  dagreGraph.setGraph({
    rankdir: direction,
    nodesep: 50,
    ranksep: 100
  })

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 280, height: 180 })
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
        x: nodeWithPosition.x - 280 / 2,
        y: nodeWithPosition.y - 180 / 2,
      },
    }
  })

  return { nodes: newNodes, edges }
}

const TABS = [
  { id: 'graph', label: 'System Architecture', icon: GitBranch, iec: '§5.3' },
  { id: 'subsystem', label: 'Subsystem Design', icon: Server, iec: '§5.4' },
  { id: 'detailed', label: 'Detailed Design', icon: Cpu, iec: '§5.5' },
  { id: 'verification', label: 'Verification Matrix', icon: ShieldAlert, iec: 'FDA 820.30(g)' },
]

export default function DiagramView({ deviceType, onDesignReady }) {
  const [loading, setLoading] = useState(false)
  const [loadingStatus, setLoadingStatus] = useState('')
  const [error, setError] = useState(null)

  const [activeTab, setActiveTab] = useState('graph')
  const [aiDetails, setAiDetails] = useState(null)
  const [detailedDesign, setDetailedDesign] = useState(null)
  const [verificationMatrix, setVerificationMatrix] = useState(null)

  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [hasGraph, setHasGraph] = useState(false)

  const handleGenerate = async () => {
    setLoading(true)
    setError(null)
    setHasGraph(false)
    setAiDetails(null)

    try {
      // Step 1: Build deterministic graph
      setLoadingStatus('Building design graph...')
      const res = await buildDesign(deviceType)
      if (res.data.error) throw new Error(res.data.error)

      const raw = res.data.raw
      if (!raw || !raw.architecture) throw new Error('No raw architecture found')

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

      // Step 2: Generate AI specs
      setLoadingStatus('Generating specifications...')
      const aiRes = await generateDesignDetails(deviceType)
      if (aiRes.data.error) throw new Error(aiRes.data.error)
      setAiDetails(aiRes.data.data)

      // Step 3: Fetch detailed design (IEC 62304 §5.5)
      setLoadingStatus('Loading detailed design...')
      const detailRes = await getDetailedDesign(deviceType)
      if (detailRes.data.error) throw new Error(detailRes.data.error)
      setDetailedDesign(detailRes.data)

      // Step 4: Fetch verification matrix (FDA 21 CFR 820.30(g))
      setLoadingStatus('Building verification matrix...')
      const verifyRes = await getVerificationMatrix(deviceType)
      if (verifyRes.data.error) throw new Error(verifyRes.data.error)
      setVerificationMatrix(verifyRes.data)

    } catch (err) {
      setError(err.message || 'Generation failed. Ensure requirements exist.')
    } finally {
      setLoading(false)
      setLoadingStatus('')
    }
  }

  const renderTabContent = () => {
    if (activeTab === 'graph') {
      return hasGraph ? (
        <div className="flex-1 w-full min-h-[600px] h-full border border-white/10 rounded-2xl overflow-hidden bg-[#212121] relative shadow-inner">
          <ReactFlow
            nodes={nodes} edges={edges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
            nodeTypes={nodeTypes} fitView fitViewOptions={{ padding: 0.05 }} minZoom={0.2} maxZoom={2} className="bg-[#212121]"
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
          <p className="text-muted-foreground text-xs mt-1">Click "Generate Design Specs" to compile technical details.</p>
        </div>
      )
    }

    switch (activeTab) {
      case 'subsystem':
        // IEC 62304 §5.4: Subsystem/Module Design
        return (
          <div className="space-y-6">
            <div className="bg-[#171717] border border-white/10 p-5 rounded-xl text-sm text-[#ececec] leading-relaxed">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold text-[#878787] uppercase text-xs tracking-wider">System Overview</h4>
                <span className="text-[10px] text-[#38BDF8] font-mono">IEC 62304 §5.4</span>
              </div>
              {aiDetails.Architecture?.SystemOverview}
            </div>
            <RenderTable headers={['Subsystem Name', 'Components Included']} data={aiDetails.Architecture?.Subsystems?.map(s => ({ n: s.name, c: s.components?.join(', ') }))} />
            <div className="bg-[#171717] border border-white/10 p-5 rounded-xl text-sm text-[#ececec] leading-relaxed">
              <h4 className="font-semibold text-[#878787] uppercase text-xs tracking-wider mb-2">Software Modules</h4>
            </div>
            <RenderTable headers={['Module Name', 'Safety Class', 'Language', 'RTOS Dependency']} data={aiDetails.Software?.SoftwareModules} />
          </div>
        )
      
      case 'detailed':
        // IEC 62304 §5.5: Detailed Design
        if (!detailedDesign) {
          return (
            <div className="flex-1 flex flex-col items-center justify-center py-32 text-center rounded-2xl border-2 border-dashed border-white/5">
              <Cpu className="h-12 w-12 text-muted-foreground/30 mb-4" />
              <p className="text-muted-foreground text-sm font-medium">Detailed design loading...</p>
            </div>
          )
        }
        return (
          <div className="space-y-6">
            {/* BOM Section */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h4 className="font-semibold text-[#878787] uppercase text-xs tracking-wider">Bill of Materials (BOM)</h4>
                <span className="text-[10px] text-[#38BDF8] font-mono">IEC 62304 §5.5 / FDA DHF</span>
              </div>
              <RenderTable 
                headers={['Item', 'Part Number', 'Description', 'Manufacturer', 'Qty', 'Cost', 'Subsystem']} 
                data={detailedDesign.bom?.map(b => ({ 
                  item: b.item, 
                  part_number: b.part_number, 
                  description: b.description, 
                  manufacturer: b.manufacturer, 
                  quantity: b.quantity, 
                  unit_cost: b.unit_cost,
                  subsystem: b.subsystem 
                }))} 
              />
            </div>

            {/* PCB Components Section */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h4 className="font-semibold text-[#878787] uppercase text-xs tracking-wider">PCB Component Placement</h4>
                <span className="text-[10px] text-[#38BDF8] font-mono">Schematic Reference</span>
              </div>
              {detailedDesign.pcb_components && Object.entries(detailedDesign.pcb_components).map(([subsystem, components]) => (
                <div key={subsystem} className="mb-4">
                  <h5 className="text-xs font-semibold text-[#ececec] mb-2">{subsystem}</h5>
                  <RenderTable 
                    headers={['Reference', 'Part', 'Footprint', 'Value']} 
                    data={components?.map(c => ({ 
                      reference: c.reference, 
                      part: c.part, 
                      footprint: c.footprint, 
                      value: c.value 
                    }))} 
                  />
                </div>
              ))}
            </div>

            {/* Firmware Architecture */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h4 className="font-semibold text-[#878787] uppercase text-xs tracking-wider">Firmware Architecture</h4>
                <span className="text-[10px] text-[#38BDF8] font-mono">IEC 62304 §5.4.4</span>
              </div>
              <div className="bg-[#171717] border border-white/10 p-5 rounded-xl mb-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-[#878787] text-xs">RTOS:</span>
                    <p className="text-[#ececec] font-semibold">{detailedDesign.firmware_architecture?.rtos}</p>
                  </div>
                  <div>
                    <span className="text-[#878787] text-xs">HAL Layer:</span>
                    <p className="text-[#ececec] font-semibold">{detailedDesign.firmware_architecture?.hal_layer}</p>
                  </div>
                </div>
              </div>
              <h5 className="text-xs font-semibold text-[#ececec] mb-2">RTOS Tasks</h5>
              <RenderTable 
                headers={['Task Name', 'Priority', 'Stack', 'Period', 'Description']} 
                data={detailedDesign.firmware_architecture?.tasks?.map(t => ({ 
                  name: t.name, 
                  priority: t.priority, 
                  stack: t.stack, 
                  period: t.period, 
                  description: t.description 
                }))} 
              />
              <h5 className="text-xs font-semibold text-[#ececec] mb-2 mt-4">Software Modules</h5>
              <RenderTable 
                headers={['Module', 'LOC', 'Safety Class', 'Unit Tests']} 
                data={detailedDesign.firmware_architecture?.modules?.map(m => ({ 
                  name: m.name, 
                  loc: m.loc, 
                  safety_class: m.safety_class, 
                  unit_tests: m.unit_tests 
                }))} 
              />
            </div>
          </div>
        )

      case 'verification':
        // FDA 21 CFR 820.30(g): Design Verification Matrix
        if (!verificationMatrix) {
          return (
            <div className="flex-1 flex flex-col items-center justify-center py-32 text-center rounded-2xl border-2 border-dashed border-white/5">
              <ShieldAlert className="h-12 w-12 text-muted-foreground/30 mb-4" />
              <p className="text-muted-foreground text-sm font-medium">Verification matrix loading...</p>
            </div>
          )
        }
        return (
          <div className="space-y-6">
            <div className="bg-[#171717] border border-white/10 p-5 rounded-xl">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-semibold text-[#ececec] text-sm">Design Verification Matrix</h4>
                  <p className="text-xs text-[#878787] mt-1">Total Verification Items: {verificationMatrix.total_verification_items}</p>
                </div>
                <span className="text-[10px] text-[#38BDF8] font-mono">FDA 21 CFR 820.30(g)</span>
              </div>
            </div>
            <RenderTable 
              headers={['Req ID', 'Title', 'Subsystem', 'Design Element', 'Verification Method', 'Acceptance Criteria', 'Status']} 
              data={verificationMatrix.matrix?.map(m => ({ 
                id: m.requirement_id, 
                title: m.requirement_title, 
                subsystem: m.subsystem, 
                design: m.design_element, 
                method: m.verification_method, 
                criteria: m.verification_description, 
                status: m.status 
              }))} 
            />
          </div>
        )

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
        </div>
        <div className="flex gap-3">
          <Button onClick={handleGenerate} disabled={loading} className="gap-2 bg-white text-black hover:bg-white/90">
            {loading
              ? <><span className="animate-pulse">{loadingStatus || 'Working...'}</span></>
              : <><GitBranch className="h-4 w-4" /> Generate Design</>}
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
              "flex flex-col items-start gap-1 px-4 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap",
              activeTab === tab.id
                ? "bg-[#2f2f2f] text-white shadow-sm"
                : "text-muted-foreground hover:text-[#ececec] hover:bg-white/5"
            )}
          >
            <div className="flex items-center gap-2">
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </div>
            {tab.iec && (
              <span className="text-[9px] text-[#38BDF8] font-mono">{tab.iec}</span>
            )}
          </button>
        ))}
      </div>

      <div className="flex-1 w-full overflow-y-auto pr-2 custom-scrollbar pb-10 flex flex-col">
        {renderTabContent()}
      </div>
    </div>
  )
}