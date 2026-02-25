import React, { useState, useEffect, useRef } from 'react';
import { AlertTriangle, Zap, ShieldCheck, Activity, Database, ExternalLink, Info, Bell, RotateCcw } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { HW_CONFIGS, BUS_COLORS, POWER_COLORS } from './HardwareTwinConfig';

// ─── Helpers ─────────────────────────────────────────────────────────────────

const deviceKey = (dt) =>
    dt === 'ventilator' ? 'ventilator' : dt === 'dialysis' ? 'dialysis' : 'pulse_oximeter';

// ─── SVG: Power Domain Rails ──────────────────────────────────────────────────

function PowerRails({ domains }) {
    return (
        <>
            {domains.map((d) => (
                <g key={d.id}>
                    <rect x={d.x} y={d.y} width={d.w} height={d.h} rx="2" fill={d.color} opacity={d.opacity} />
                    <text x={d.x + 6} y={d.y + d.h - 3} fill={d.color} fontSize="12" fontWeight="bold" fontFamily="sans-serif" opacity="0.65">
                        {d.label}
                    </text>
                </g>
            ))}
        </>
    );
}

// ─── SVG: Signal Buses ────────────────────────────────────────────────────────

function SignalBuses({ buses, activeFault, simRunning }) {
    return (
        <>
            {buses.map((bus) => {
                const color = BUS_COLORS[bus.type] || '#fff';
                const isFaulted = activeFault === bus.type;
                const opacity = isFaulted ? 1 : 0.35;
                return (
                    <g key={bus.id}>
                        <path
                            d={`M ${bus.x1} ${bus.y1} L ${bus.x2} ${bus.y2}`}
                            fill="none"
                            stroke={isFaulted ? '#ef4444' : color}
                            strokeWidth={bus.type === 'EMERGENCY' || bus.type === 'INTERLOCK' ? 2 : 1.5}
                            strokeDasharray={bus.dashed ? '5 3' : undefined}
                            opacity={opacity}
                        />
                        {/* Flow animation dot */}
                        {simRunning && !bus.dashed && (
                            <circle r="3" fill={color} opacity="0.9">
                                <animateMotion
                                    dur={bus.type === 'PWM' ? '1.5s' : '3s'}
                                    repeatCount="indefinite"
                                    path={`M ${bus.x1} ${bus.y1} L ${bus.x2} ${bus.y2}`}
                                />
                            </circle>
                        )}
                        <text
                            x={(bus.x1 + bus.x2) / 2}
                            y={(bus.y1 + bus.y2) / 2 - 6}
                            textAnchor="middle"
                            fill={color}
                            fontSize="12"
                            fontFamily="monospace"
                            fontWeight="bold"
                            opacity={0.6}
                        >
                            {bus.label}
                        </text>
                    </g>
                );
            })}
        </>
    );
}

// ─── SVG: Electronics Block ────────────────────────────────────────────────────

function ElectronicsBlock({ block, faultedTargets, selectedComponent, modes }) {
    // Layer-1 coupling: highlight if this block's layer1Component is Noisy/Failed
    const linkedMode = block.layer1Component ? (modes[block.layer1Component] || 'Ideal') : 'Ideal';
    const isFaulted = faultedTargets.includes(block.id) || linkedMode === 'Failed';
    const isNoisy = linkedMode === 'Noisy';
    const isSelected = selectedComponent && block.layer1Component === selectedComponent;

    const borderColor = isFaulted ? '#ef4444' : isNoisy ? '#f59e0b' : isSelected ? '#38bdf8' : 'rgba(255,255,255,0.12)';
    const bgColor = isFaulted ? 'rgba(239,68,68,0.08)' : isSelected ? 'rgba(56,189,248,0.07)' : '#0e1c28';
    const ledColor = isFaulted ? '#ef4444' : isNoisy ? '#f59e0b' : '#10b981';

    return (
        <g transform={`translate(${block.x},${block.y})`}>
            {/* Block body */}
            <rect width={block.w} height={block.h} rx="6" fill={bgColor} stroke={borderColor} strokeWidth={isFaulted || isSelected ? 1.5 : 1} />

            {/* Fault / Selection glow */}
            {(isFaulted || isSelected) && (
                <rect width={block.w} height={block.h} rx="6" fill="none"
                    stroke={isFaulted ? '#ef4444' : '#38bdf8'} strokeWidth="4" opacity="0.08" />
            )}

            {/* Status LED */}
            <circle cx={block.w - 9} cy="9" r="4" fill={ledColor} opacity="0.9" />
            {isFaulted && (
                <circle cx={block.w - 9} cy="9" r="7" fill="#ef4444" opacity="0.2">
                    <animate attributeName="r" values="6;9;6" dur="1s" repeatCount="indefinite" />
                </circle>
            )}

            {/* Fault icon */}
            {isFaulted && (
                <text x="7" y="15" fill="#ef4444" fontSize="10">⚠</text>
            )}

            {/* Label */}
            <text x={block.w / 2} y={block.h / 2 - 4} textAnchor="middle"
                fill={isFaulted ? '#fca5a5' : 'rgba(255,255,255,0.95)'}
                fontSize="12" fontFamily="sans-serif" fontWeight="bold">
                {block.label.toUpperCase()}
            </text>

            {/* Sub-label */}
            <text x={block.w / 2} y={block.h / 2 + 11} textAnchor="middle"
                fill="rgba(255,255,255,0.5)" fontSize="10" fontFamily="sans-serif" fontWeight="medium">
                {block.sublabel}
            </text>

            {/* Layer-1 link badge */}
            {block.layer1Component && (
                <text x={block.w / 2} y={block.h - 6} textAnchor="middle"
                    fill="rgba(56,189,248,0.6)" fontSize="9" fontFamily="sans-serif" fontWeight="bold">
                    ↑ {block.layer1Component}
                </text>
            )}
        </g>
    );
}

// ─── Main HardwareTwin Component ─────────────────────────────────────────────

export default function HardwareTwin({ deviceType, modes = {}, selectedComponent, onInjectFault, simRunning }) {
    const cfg = HW_CONFIGS[deviceKey(deviceType)];
    const [faultedTargets, setFaultedTargets] = useState([]);
    const [activeHWFault, setActiveHWFault] = useState(null);
    const [hwEventLog, setHwEventLog] = useState([]);

    const injectHWFault = (fault) => {
        setFaultedTargets([fault.target]);
        setActiveHWFault(fault.label);
        setHwEventLog(prev => [
            `T+0.0s — HW FAULT: ${fault.label} (${fault.type.toUpperCase()}) → ${fault.target}`,
            ...prev.slice(0, 9),
        ]);
        if (onInjectFault) onInjectFault(fault.param, fault.bias);
    };

    const clearFaults = () => {
        setFaultedTargets([]);
        setActiveHWFault(null);
        setHwEventLog([]);
    };

    // Auto-reflect Layer-1 component failures into HW faults
    useEffect(() => {
        const failedComps = Object.entries(modes)
            .filter(([, v]) => v === 'Failed')
            .map(([k]) => k);
        const linked = cfg.blocks
            .filter(b => b.layer1Component && failedComps.includes(b.layer1Component))
            .map(b => b.id);
        setFaultedTargets(prev => [...new Set([...prev.filter(f => !cfg.blocks.map(b => b.id).includes(f)), ...linked])]);
    }, [modes, cfg.blocks]);

    return (
        <div className="w-full h-full flex flex-col bg-[#070f17] font-sans text-white overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-2.5 border-b border-white/5 shrink-0 bg-[#0a1520]">
                <div className="flex items-center gap-3">
                    <div className="flex flex-col">
                        <span className="text-[13px] font-bold text-white">{cfg.label}</span>
                        <span className="text-[10px] text-white/40 uppercase tracking-widest font-medium">{cfg.classLabel} · Layer-2 Hardware Twin</span>
                    </div>
                    <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-sky-500/5 border border-sky-500/15 hover:border-sky-500/35 transition-colors cursor-pointer" title={cfg.description}>
                        <Database className="h-3 w-3 text-sky-400 shrink-0" />
                        <span className="text-[10px] font-bold text-sky-400/80 whitespace-nowrap">Design Graph v{cfg.designVersion}</span>
                        <ExternalLink className="h-2 w-2 text-sky-400/30" />
                    </div>
                    <div className="flex items-center gap-1.5 group relative">
                        <Info className="h-4 w-4 text-white/20 hover:text-white/50 cursor-help transition-colors" />
                        <div className="absolute left-5 top-0 hidden group-hover:block w-64 p-3 bg-[#0e1c28] border border-white/10 rounded-lg text-[11px] text-white/70 z-50 leading-relaxed shadow-xl">
                            {cfg.description}
                        </div>
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    {/* Bus Legend */}
                    <div className="flex items-center gap-3">
                        {Object.entries(BUS_COLORS).slice(0, 5).map(([type, color]) => (
                            <div key={type} className="flex items-center gap-1">
                                <div className="h-1 w-5 rounded" style={{ backgroundColor: color, opacity: 0.6 }} />
                                <span className="text-[9px] font-bold text-white/30 uppercase">{type}</span>
                            </div>
                        ))}
                    </div>
                    {activeHWFault && (
                        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-red-500/10 border border-red-500/25">
                            <div className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />
                            <span className="text-[10px] font-bold text-red-300 uppercase tracking-wide">{activeHWFault}</span>
                        </div>
                    )}
                </div>
            </div>

            {/* Main content: SVG + Fault panel */}
            <div className="flex-1 flex overflow-hidden min-h-0">
                {/* SVG Canvas */}
                <div className="flex-1 relative bg-[#070f17] overflow-hidden min-w-0">
                    <svg viewBox="0 0 790 430" className="w-full h-full" style={{ maxHeight: '100%' }}>
                        <defs>
                            <filter id="hwglow">
                                <feGaussianBlur stdDeviation="3" result="b" />
                                <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
                            </filter>
                            {/* Hatching for power domains */}
                            <pattern id="hatch" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(45)">
                                <line x1="0" y1="0" x2="0" y2="6" stroke="rgba(255,255,255,0.03)" strokeWidth="1" />
                            </pattern>
                        </defs>

                        {/* Background grid */}
                        <rect width="790" height="430" fill="url(#hatch)" />

                        {/* Power rails */}
                        <PowerRails domains={cfg.powerDomains} />

                        {/* Signal buses */}
                        <SignalBuses buses={cfg.buses} activeFault={activeHWFault} simRunning={simRunning} />

                        {/* Electronics blocks */}
                        {cfg.blocks.map((block) => (
                            <ElectronicsBlock
                                key={block.id}
                                block={block}
                                faultedTargets={faultedTargets}
                                selectedComponent={selectedComponent}
                                modes={modes}
                            />
                        ))}

                        {/* Feedback return path (generic) */}
                        <text x="395" y="420" textAnchor="middle" fill="rgba(255,255,255,0.25)"
                            fontSize="12" fontFamily="sans-serif" fontStyle="italic" fontWeight="bold">
                            ← Feedback / Return Path
                        </text>
                    </svg>

                    {/* Power domain legend overlay */}
                    <div className="absolute bottom-3 left-4 flex gap-4">
                        {cfg.powerDomains.slice(0, 4).map((d) => (
                            <div key={d.id} className="flex items-center gap-1.5">
                                <div className="h-2 w-2 rounded-sm" style={{ backgroundColor: d.color, opacity: 0.7 }} />
                                <span className="text-[7px] font-bold text-white/25 uppercase">{d.label}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Right: Fault Injection Panel */}
                <div className="w-[260px] bg-[#0e1c28] border-l border-white/5 flex flex-col shrink-0">
                    <div className="px-4 pt-4 pb-3 border-b border-white/5">
                        <div className="flex items-center gap-2">
                            <Zap className="h-4 w-4 text-amber-500" />
                            <span className="text-[11px] font-bold uppercase tracking-widest text-white/60">HW Fault Injection</span>
                        </div>
                        <p className="text-[10px] text-white/30 mt-1.5 leading-relaxed">Hardware-domain faults propagate to Layer-1 behavior</p>
                    </div>

                    {/* Fault type legend */}
                    <div className="px-4 py-2 border-b border-white/5 flex flex-wrap gap-x-3 gap-y-1">
                        {[['power', '⚡', 'red'], ['bus', '≈', 'amber'], ['timing', '⏱', 'amber'], ['sensor', '📡', 'amber']].map(([t, icon, c]) => (
                            <div key={t} className="flex items-center gap-1">
                                <span className="text-[8px]">{icon}</span>
                                <span className={cn('text-[7px] font-bold uppercase', c === 'red' ? 'text-red-400/60' : 'text-amber-400/60')}>{t}</span>
                            </div>
                        ))}
                    </div>

                    <div className="flex-1 overflow-y-auto px-4 py-4 space-y-2" style={{ scrollbarWidth: 'thin', scrollbarColor: '#1e3245 transparent' }}>
                        {cfg.faultMatrix.map((fault) => (
                            <button
                                key={fault.label}
                                onClick={() => injectHWFault(fault)}
                                className={cn(
                                    'w-full flex items-start gap-3 px-3.5 py-3 rounded-xl border text-left transition-all',
                                    activeHWFault === fault.label
                                        ? fault.color === 'red'
                                            ? 'bg-red-500/20 border-red-500/50 text-red-200'
                                            : 'bg-amber-500/20 border-amber-500/50 text-amber-200'
                                        : fault.color === 'red'
                                            ? 'bg-red-500/5 border-red-500/10 text-white/50 hover:border-red-500/35 hover:bg-red-500/10'
                                            : 'bg-amber-500/5 border-amber-500/10 text-white/50 hover:border-amber-500/30 hover:bg-amber-500/10'
                                )}
                            >
                                <div className={cn('h-2 w-2 rounded-full shrink-0 mt-1', fault.color === 'red' ? 'bg-red-500' : 'bg-amber-400')} />
                                <div className="min-w-0">
                                    <div className="text-[11px] font-bold leading-tight">{fault.label}</div>
                                    <div className="text-[9px] text-white/30 uppercase tracking-tight mt-1">{fault.type} fault · {fault.target}</div>
                                </div>
                            </button>
                        ))}
                        <button onClick={clearFaults}
                            className="w-full flex items-center gap-2 px-3 py-2 rounded-xl border border-white/5 text-white/25 hover:border-white/15 hover:text-white/50 transition-all text-[9px] font-bold">
                            <RotateCcw className="h-3 w-3" />Clear Faults
                        </button>
                    </div>

                    {/* HW Event Log */}
                    <div className="px-3 pb-4 border-t border-white/5 pt-3">
                        <div className="flex items-center gap-2 mb-2">
                            <Bell className="h-3 w-3 text-white/25" />
                            <span className="text-[8px] font-bold uppercase text-white/25">HW Event Log</span>
                            {hwEventLog.length > 0 && (
                                <span className="ml-auto h-4 w-4 rounded-full bg-red-500 flex items-center justify-center text-[7px] font-bold">{hwEventLog.length}</span>
                            )}
                        </div>
                        <div className="min-h-[60px] max-h-[100px] overflow-y-auto bg-black/20 border border-white/5 rounded-xl p-2 space-y-1.5"
                            style={{ scrollbarWidth: 'thin', scrollbarColor: '#1e3245 transparent' }}>
                            {hwEventLog.length === 0 ? (
                                <div className="flex items-center justify-center h-8">
                                    <span className="text-[7px] text-white/15 italic uppercase tracking-widest">No HW events</span>
                                </div>
                            ) : hwEventLog.map((e, i) => (
                                <div key={i} className="text-[7px] text-white/40 font-mono leading-tight border-b border-white/5 pb-1 last:border-0 last:pb-0">{e}</div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
