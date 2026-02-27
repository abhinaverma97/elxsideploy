import React, { useState } from 'react'
import {
  SquarePen,
  GitBranch,
  MonitorPlay,
  FileSearch,
  Settings,
  User,
  MoreHorizontal,
  ClipboardList,
  PanelLeftClose,
  PanelLeftOpen
} from 'lucide-react'

import RequirementsForm from './components/RequirementsForm'
import DiagramView from './components/DiagramView'
import ProfessionalSimulator from './components/ProfessionalSimulator'
import TraceabilityTable from './components/TraceabilityTable'


import { cn } from "@/lib/utils"

const DEVICES = [
  { id: 'ventilator', name: 'Ventilator', class: 'Class II' },
  { id: 'pulse_ox', name: 'Pulse Oximeter', class: 'Class I' },
  { id: 'dialysis', name: 'Hemodialysis', class: 'Class III' },
]

export default function App() {
  const [view, setView] = useState('requirements')
  const [deviceType, setDeviceType] = useState('ventilator')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  const navItems = [
    { id: 'requirements', label: 'Requirements', icon: ClipboardList },
    { id: 'design', label: 'Graph', icon: GitBranch },
    { id: 'simulation', label: 'Digital Twin', icon: MonitorPlay },
    { id: 'trace', label: 'Traceability', icon: FileSearch },
  ]

  return (
    <div className="dark flex h-screen bg-background text-foreground overflow-hidden font-sans">
      {/* SIDEBAR - ChatGPT Style - Collapsible */}
      <aside className={cn(
        "flex-shrink-0 bg-[#171717] flex flex-col justify-between hidden md:flex h-full transition-all duration-200",
        sidebarCollapsed ? "w-[60px]" : "w-[260px]"
      )}>
        <div className="flex flex-col h-full p-3 gap-2">
          {/* Top Actions: Logo/Select & New Chat */}
          <div className={cn("flex items-center mb-2", sidebarCollapsed ? "justify-center" : "justify-between")}>
            {/* ChatGPT style top left dropdown */}
            <div className={cn(
              "flex items-center gap-2 hover:bg-[#2f2f2f] rounded-lg cursor-pointer transition-colors duration-200",
              sidebarCollapsed ? "px-1.5 py-1.5 justify-center" : "px-2 py-1.5"
            )} onClick={() => sidebarCollapsed && setSidebarCollapsed(false)}>
              <div className="h-6 w-6 rounded bg-white text-black flex items-center justify-center font-bold text-xs shrink-0">V</div>
              {!sidebarCollapsed && <span className="text-sm font-medium text-white">VitaBlueprint</span>}
            </div>
            {/* ChatGPT style New Chat button */}
            {!sidebarCollapsed && (
              <button onClick={() => setView('requirements')} className="p-1.5 hover:bg-[#2f2f2f] rounded-lg text-[#ececec] transition-colors duration-200">
                <SquarePen className="w-5 h-5" />
              </button>
            )}
          </div>

          {/* Navigation/History List */}
          <div className="flex-1 overflow-y-auto">
            {/* "Today" section header equivalent */}
            {!sidebarCollapsed && (
              <div className="px-2 pb-2 pt-4">
                <p className="text-xs font-semibold text-[#878787] mb-2">Workspace Views</p>
              </div>
            )}
            {sidebarCollapsed && <div className="pt-3" />}
            <nav className="space-y-0.5">
              {navItems.map((item) => {
                const Icon = item.icon
                const isActive = view === item.id
                return (
                  <button
                    key={item.id}
                    onClick={() => setView(item.id)}
                    title={sidebarCollapsed ? item.label : undefined}
                    className={cn(
                      "w-full flex items-center gap-2.5 text-sm rounded-lg transition-colors group",
                      sidebarCollapsed ? "justify-center px-0 py-2" : "px-2 py-2",
                      isActive
                        ? "bg-[#2f2f2f] text-white font-medium"
                        : "text-[#ececec] hover:bg-[#2f2f2f] font-normal"
                    )}
                  >
                    <Icon className="w-4 h-4 opacity-70 group-hover:opacity-100 shrink-0" />
                    {!sidebarCollapsed && <span className="truncate">{item.label}</span>}
                  </button>
                )
              })}
            </nav>

            {/* Device Selection */}
            {!sidebarCollapsed && (
              <div className="px-2 pb-2 pt-6">
                <p className="text-xs font-semibold text-[#878787] mb-2">Target Device</p>
              </div>
            )}
            {sidebarCollapsed && <div className="pt-4 border-t border-white/10 mt-3" />}
            <div className="space-y-0.5">
              {DEVICES.map((d) => {
                const isSelected = deviceType === d.id
                return (
                  <button
                    key={d.id}
                    onClick={() => setDeviceType(d.id)}
                    title={sidebarCollapsed ? d.name : undefined}
                    className={cn(
                      "w-full flex items-center gap-2.5 text-sm rounded-lg transition-colors group",
                      sidebarCollapsed ? "justify-center px-0 py-2" : "px-2 py-2",
                      isSelected
                        ? "bg-[#2f2f2f] text-white font-medium"
                        : "text-[#ececec] hover:bg-[#2f2f2f] font-normal"
                    )}
                  >
                    <div className="w-4 h-4 flex items-center justify-center opacity-70 group-hover:opacity-100 shrink-0">
                      <div className={cn("w-2 h-2 rounded-full", isSelected ? "bg-white" : "bg-transparent border border-[#ececec]")}></div>
                    </div>
                    {!sidebarCollapsed && <span className="truncate">{d.name}</span>}
                  </button>
                )
              })}
            </div>

          </div>
        </div>

        {/* Bottom: Collapse toggle + User Area */}
        <div className="p-3 space-y-1">
          <button
            onClick={() => setSidebarCollapsed(c => !c)}
            className={cn(
              "w-full flex items-center gap-2 py-2 text-sm rounded-lg hover:bg-[#2f2f2f] transition-colors text-[#878787] hover:text-white",
              sidebarCollapsed ? "justify-center px-0" : "px-2"
            )}
            title={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {sidebarCollapsed ? <PanelLeftOpen className="w-4 h-4 shrink-0" /> : <PanelLeftClose className="w-4 h-4 shrink-0" />}
            {!sidebarCollapsed && <span className="text-xs">Collapse</span>}
          </button>
          <button className={cn(
            "w-full flex items-center gap-2 py-3 text-sm font-medium rounded-lg hover:bg-[#2f2f2f] transition-colors text-white",
            sidebarCollapsed ? "justify-center px-0" : "justify-between px-2"
          )}>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-sky-500 to-teal-400 flex items-center justify-center shrink-0">
                <User className="w-4 h-4 text-white" />
              </div>
              {!sidebarCollapsed && 'Admin User'}
            </div>
            {!sidebarCollapsed && <MoreHorizontal className="w-4 h-4 text-[#878787]" />}
          </button>
        </div>
      </aside>

      {/* MAIN CONTENT AREA - ChatGPT style (#212121 background) */}
      <main className="flex-1 flex flex-col h-full overflow-hidden bg-[#212121]">
        {/* Mobile Header */}
        <header className="h-12 border-b border-[#2f2f2f] flex items-center justify-between px-4 md:hidden bg-[#212121] sticky top-0 z-10">
          <div className="flex items-center gap-2">
            <div className="h-6 w-6 rounded bg-white text-black flex items-center justify-center font-bold text-xs">V</div>
            <h1 className="text-sm font-medium text-white">VitaBlueprint</h1>
          </div>
          <select
            value={deviceType}
            onChange={(e) => setDeviceType(e.target.value)}
            className="text-sm bg-transparent border-none outline-none text-white font-medium"
          >
            {DEVICES.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
        </header>

        {/* Dynamic View Area */}
        {view === 'simulation' ? (
          <div className="flex-1 overflow-hidden flex flex-col">
            <ProfessionalSimulator deviceType={deviceType} />
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto">
            <div className="w-full h-full min-h-[600px] p-4 md:p-6 lg:p-10 pt-6 md:pt-10">
              {view === 'requirements' && <RequirementsForm deviceType={deviceType} setView={setView} />}
              {view === 'design' && <DiagramView deviceType={deviceType} />}
              {view === 'trace' && <TraceabilityTable deviceType={deviceType} />}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
