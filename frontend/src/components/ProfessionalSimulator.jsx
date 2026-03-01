import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
    Play, Pause, RotateCcw, Activity, Zap, AlertTriangle,
    Save, Cpu, ShieldCheck, Database, FastForward, Clock,
    Sliders, Bell, CheckCircle2, ChevronDown, ChevronRight, ChevronLeft,
    ExternalLink, Info, BookOpen, SkipForward
} from 'lucide-react';
import {
    AreaChart, Area, LineChart, Line, XAxis, YAxis,
    CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine
} from 'recharts';
import { runSimulation, runFaultySimulation, buildDesign } from '../api';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { DEVICE_CONFIGS, FIDELITY_DESCRIPTIONS, FIDELITY_FAULT_LOCK } from './SimulatorConfig';
import HardwareTwin from './HardwareTwin';
import { buildSimConfigFromDesign } from './designToSimConfig';

// ─── Helpers ─────────────────────────────────────────────────────────────────

const deviceKey = (deviceType) =>
    deviceType === 'ventilator' ? 'ventilator' : 'dialysis';

const STATUS_COLORS = {
    Ideal: { border: 'rgba(56,189,248,0.4)', led: '#10b981', badge: 'text-sky-400' },
    Noisy: { border: 'rgba(245,158,11,0.6)', led: '#f59e0b', badge: 'text-amber-400' },
    Failed: { border: 'rgba(239,68,68,0.8)', led: '#ef4444', badge: 'text-red-400' },
};

// ─── Top Control Bar ──────────────────────────────────────────────────────────

function TopBar({ simState, time, speed, setSpeed, fidelity, setFidelity, onRun, onStep, onReset, deviceConfig }) {
    return (
        <div className="h-14 bg-[#212121] border-b border-white/10 flex items-center justify-between px-4 shrink-0">
            {/* Left: identity */}
            <div className="flex items-center gap-3 min-w-0">
                <div className="flex flex-col leading-none min-w-0">
                    <span className="text-[14px] font-bold text-[#ececec] truncate">{deviceConfig.label}</span>
                    <span className="text-[11px] text-[#878787] uppercase tracking-widest font-semibold">Digital Twin</span>
                </div>
            </div>

            {/* Center: Time controls */}
            <div className="flex items-center gap-2">
                <Button onClick={onRun} size="sm" className={cn('h-8 px-4 gap-1.5 text-[10px] font-bold uppercase tracking-wider',
                    simState === 'RUNNING' ? 'bg-amber-500 hover:bg-amber-600 text-black' : 'bg-white hover:bg-white/90 text-black')}>
                    {simState === 'RUNNING' ? <Pause className="h-3 w-3 fill-current" /> : <Play className="h-3 w-3 fill-current" />}
                    {simState === 'RUNNING' ? 'Pause' : 'Run'}
                </Button>
                <button onClick={onStep} title="Single step (Δt = 0.1s)"
                    className="h-8 w-8 flex items-center justify-center rounded bg-[#171717] hover:bg-[#2f2f2f] text-[#878787] hover:text-white transition-colors">
                    <SkipForward className="h-3.5 w-3.5" />
                </button>
                <button onClick={onReset} title="Reset simulation"
                    className="h-8 w-8 flex items-center justify-center rounded bg-[#171717] hover:bg-[#2f2f2f] text-[#878787] hover:text-white transition-colors">
                    <RotateCcw className="h-3.5 w-3.5" />
                </button>

                {/* Speed */}
                <div className="flex gap-px bg-[#171717] rounded border border-white/10 overflow-hidden ml-1">
                    {['1×', '2×', '10×'].map((s) => (
                        <button key={s} onClick={() => setSpeed(s)}
                            className={cn('px-2.5 py-1 text-[9px] font-bold transition-colors', speed === s ? 'bg-[#2f2f2f] text-white' : 'text-[#878787] hover:text-white')}>
                            {s}
                        </button>
                    ))}
                </div>

                {/* Clock */}
                <div className="flex items-center gap-1.5 ml-2 px-3 py-1 rounded bg-[#171717] border border-white/10">
                    <Clock className="h-3 w-3 text-[#38BDF8]/60 shrink-0" />
                    <span className="font-mono text-sm font-bold tracking-tighter text-[#ececec]">T={time.toFixed(1)}s</span>
                </div>

                {/* Status pill */}
                <div className="flex items-center gap-1.5">
                    <div className={cn('h-2 w-2 rounded-full', simState === 'RUNNING' ? 'bg-[#38BDF8] animate-pulse shadow-[0_0_6px_#38bdf8]' : simState === 'PAUSED' ? 'bg-amber-400' : 'bg-white/20')} />
                    <span className="text-[9px] font-bold uppercase tracking-widest text-[#878787]">{simState}</span>
                </div>
            </div>

            {/* Right: Fidelity */}
            <div className="flex items-center gap-2">
                <div className="flex p-0.5 bg-[#171717] rounded-lg border border-white/10 gap-px" title={FIDELITY_DESCRIPTIONS[fidelity]}>
                    {['L1', 'L2', 'L3'].map((l) => (
                        <button key={l} onClick={() => setFidelity(l)} className={cn('h-7 px-3 rounded text-[10px] font-bold transition-all',
                            fidelity === l ? 'bg-white text-black shadow-lg' : 'text-[#878787] hover:text-white')}>
                            {l}
                        </button>
                    ))}
                </div>
                {fidelity && (
                    <div className="group relative">
                        <Info className="h-3.5 w-3.5 text-[#878787] hover:text-white/50 cursor-help transition-colors" />
                        <div className="absolute right-0 top-5 hidden group-hover:block w-52 p-2 bg-[#171717] border border-white/10 rounded-lg text-[9px] text-[#878787] z-50">
                            {FIDELITY_DESCRIPTIONS[fidelity]}
                        </div>
                    </div>
                )}
                {simState !== 'RUNNING' && <div className="flex items-center gap-1 text-emerald-400 text-[9px] font-bold ml-1"><CheckCircle2 className="h-3 w-3" />NOMINAL</div>}
            </div>
        </div>
    );
}

// ─── Left: Components Panel ───────────────────────────────────────────────────

function ComponentsPanel({ modes, setMode, deviceConfig, fidelity, panelCollapsed, onTogglePanel }) {
    const [collapsed, setCollapsed] = useState({});
    const toggleCollapse = (id) => setCollapsed(p => ({ ...p, [id]: !p[id] }));

    if (panelCollapsed) {
        return (
            <div className="w-[40px] bg-[#171717] border-r border-white/10 flex flex-col items-center shrink-0 py-2 gap-2">
                <button onClick={onTogglePanel} className="p-1.5 rounded hover:bg-[#2f2f2f] text-[#878787] hover:text-white transition-colors" title="Expand inventory">
                    <ChevronRight className="h-4 w-4" />
                </button>
                <Cpu className="h-3.5 w-3.5 text-[#878787] mt-1" />
            </div>
        );
    }

    return (
        <div className="w-[228px] bg-[#171717] border-r border-white/10 flex flex-col shrink-0 overflow-hidden transition-all duration-200">
            <div className="px-4 py-2.5 flex items-center justify-between border-b border-white/10 shrink-0 bg-[#212121]/50">
                <div className="flex items-center gap-2">
                    <Cpu className="h-4 w-4 text-[#38BDF8]" />
                    <span className="text-[11px] font-bold uppercase tracking-widest text-[#878787]">Inventory</span>
                </div>
                <button onClick={onTogglePanel} className="p-1 rounded hover:bg-[#2f2f2f] text-[#878787] hover:text-white transition-colors" title="Collapse">
                    <ChevronLeft className="h-3.5 w-3.5" />
                </button>
            </div>

            <div className="flex-1 overflow-y-auto py-0" style={{ scrollbarWidth: 'none' }}>
                {deviceConfig.subsystems.map((sub) => {
                    const isCollapsed = collapsed[sub.id];
                    return (
                        <div key={sub.id} className="px-2 mb-0.5">
                            <button onClick={() => toggleCollapse(sub.id)}
                                className="w-full flex items-center gap-1.5 py-1 text-left group">
                                {isCollapsed ? <ChevronRight className="h-3 w-3 text-[#878787] group-hover:text-white/50" /> : <ChevronDown className="h-3 w-3 text-[#878787] group-hover:text-white/50" />}
                                <span className="text-xs font-bold uppercase tracking-wider text-[#878787] group-hover:text-[#ececec]">{sub.label}</span>
                            </button>

                            {!isCollapsed && sub.components.map((comp) => {
                                const mode = modes[comp] || 'Ideal';
                                const colors = STATUS_COLORS[mode];
                                return (
                                    <div key={comp} className="mb-0.5 bg-[#212121] border rounded-lg px-2.5 py-1.5 transition-all"
                                        style={{ borderColor: colors.border }}>
                                        <div className="flex items-center justify-between mb-1">
                                            <span className="text-xs font-bold text-[#ececec] leading-tight truncate pr-1" title={comp}>{comp}</span>
                                            <span className={cn('text-[10px] font-bold italic opacity-70', colors.badge)}>{mode}</span>
                                        </div>
                                        <div className="grid grid-cols-3 gap-1">
                                            {(['Ideal', 'Noisy', 'Failed']).map((m) => (
                                                <button key={m} onClick={() => setMode(comp, m)}
                                                    className={cn('py-1 rounded text-[9px] font-bold border transition-all',
                                                        mode === m
                                                            ? m === 'Failed' ? 'bg-red-500 text-white border-transparent'
                                                                : m === 'Noisy' ? 'bg-amber-500 text-black border-transparent'
                                                                    : 'bg-white text-black border-transparent'
                                                            : 'bg-[#171717] text-[#878787] border-white/10 hover:border-white/30 hover:text-[#ececec]'
                                                    )}>
                                                    {m[0]}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

// ─── Center: Architecture View ─────────────────────────────────────────────────

function ArchitectureView({ deviceConfig, simState, modes }) {
    const isRunning = simState === 'RUNNING';

    const getSubsystemMode = (sub) => {
        if (!sub.components) return 'Ideal';
        for (const comp of sub.components) {
            if (modes[comp] === 'Failed') return 'Failed';
            if (modes[comp] === 'Noisy') return 'Noisy';
        }
        return 'Ideal';
    };

    return (
        <div className="flex-1 flex flex-col min-h-0 border-b border-white/10 bg-[#212121]">

            <div className="flex-1 relative overflow-hidden">
                <svg viewBox="0 0 800 370" className="w-full h-full">
                    <defs>
                        <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto">
                            <path d="M0 1 L10 5 L0 9 z" fill="rgba(255,255,255,0.15)" />
                        </marker>
                        <filter id="glow"><feGaussianBlur stdDeviation="3" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
                    </defs>

                    {/* Links */}
                    {deviceConfig.links.map((lk, i) => (
                        <g key={i}>
                            <path d={`M ${lk.x1} ${lk.y1} L ${lk.x2} ${lk.y2}`}
                                fill="none" stroke={isRunning && !lk.dashed ? 'rgba(56,189,248,0.3)' : 'rgba(255,255,255,0.07)'}
                                strokeWidth="1.5" strokeDasharray={lk.dashed ? '4 3' : undefined}
                                markerEnd="url(#arr)" />
                            {isRunning && !lk.dashed && (
                                <circle r="3" fill="#38bdf8" opacity="0.9" filter="url(#glow)">
                                    <animateMotion dur="3s" repeatCount="indefinite" path={`M ${lk.x1} ${lk.y1} L ${lk.x2} ${lk.y2}`} />
                                </circle>
                            )}
                            <text x={(lk.x1 + lk.x2) / 2} y={(lk.y1 + lk.y2) / 2 - 5} textAnchor="middle"
                                fill="rgba(255,255,255,0.2)" fontSize="7" fontFamily="monospace">{lk.label}</text>
                        </g>
                    ))}

                    {/* Blocks */}
                    {deviceConfig.subsystems.map((sub) => {
                        const mode = getSubsystemMode(sub);
                        const col = STATUS_COLORS[mode];
                        return (
                            <g key={sub.id} transform={`translate(${sub.x},${sub.y})`}>
                                <rect width={sub.w} height={sub.h} rx="6" fill="#171717"
                                    stroke={col.border} strokeWidth={mode !== 'Ideal' ? 1.5 : 1}
                                    filter={mode === 'Failed' ? 'url(#glow)' : undefined} />
                                {/* Status LED */}
                                <circle cx={sub.w - 11} cy="11" r="4" fill={col.led} filter={isRunning ? 'url(#glow)' : undefined}>
                                    {isRunning && <animate attributeName="opacity" values="1;0.4;1" dur="2s" repeatCount="indefinite" />}
                                </circle>
                                {/* Fault badge */}
                                {mode === 'Failed' && (
                                    <text x="8" y="14" fill="#ef4444" fontSize="9" fontWeight="bold">⚠</text>
                                )}
                                <text x={sub.w / 2} y={sub.h / 2 + 3} textAnchor="middle" fill={mode === 'Failed' ? '#ef9999' : 'rgba(255,255,255,0.55)'}
                                    fontSize="9.5" fontFamily="monospace" fontWeight="bold">
                                    {sub.label.toUpperCase()}
                                </text>
                                {sub.components.slice(0, 2).map((c, ci) => (
                                    <text key={ci} x="8" y={sub.h - 12 + ci * 10} fill="rgba(255,255,255,0.2)" fontSize="7" fontFamily="monospace">• {c}</text>
                                ))}
                            </g>
                        );
                    })}
                </svg>
            </div>
        </div>
    );
}

// ─── Center Bottom: Signal Telemetry ─────────────────────────────────────────

const CustomDot = (props) => {
    const { cx, cy, value, dataKey } = props;
    if (value === undefined) return null;
    return <circle cx={cx} cy={cy} r={2.5} fill={props.stroke} fillOpacity={0.8} />;
};

function TelemetryPanel({ simData, deviceConfig, fidelity, frozen, setFrozen, onSnap }) {
    const signals = fidelity === 'L1'
        ? deviceConfig.signals.slice(0, 1)
        : fidelity === 'L2'
            ? deviceConfig.signals.slice(0, 2)
            : deviceConfig.signals;

    const chartData = (frozen ? simData.frozen : simData.live) || [];

    return (
        <div className="h-72 shrink-0 border-t border-white/10 flex flex-col bg-[#212121]">
            <div className="flex items-center justify-between px-4 py-1.5 shrink-0 border-b border-white/10">
                <div className="flex items-center gap-2">
                    <Activity className="h-3 w-3 text-[#38BDF8]/60" />
                    <span className="text-[9px] font-bold uppercase tracking-widest text-[#878787]">Signal Telemetry</span>
                    {!frozen && chartData.length > 0 && <div className="h-1.5 w-1.5 rounded-full bg-[#38BDF8] animate-pulse" />}
                    {frozen && <span className="text-[8px] text-amber-400 font-bold uppercase tracking-wider ml-1">FROZEN</span>}
                </div>
                <div className="flex gap-2">
                    <button onClick={() => setFrozen(f => !f)}
                        className={cn('h-7 px-3 rounded text-[9px] font-bold border uppercase tracking-wider transition-all gap-1.5 flex items-center',
                            frozen ? 'bg-amber-500/20 border-amber-500/40 text-amber-300' : 'bg-[#171717] border-white/10 text-[#878787] hover:text-white')}>
                        <Pause className="h-2.5 w-2.5" />{frozen ? 'Resume' : 'Freeze'}
                    </button>
                    <button onClick={onSnap}
                        className="h-7 px-3 rounded text-[9px] font-bold border uppercase tracking-wider bg-[#171717] border-white/10 text-[#878787] hover:text-white transition-all flex items-center gap-1.5">
                        <Save className="h-2.5 w-2.5" />Snap
                    </button>
                </div>
            </div>

            <div className="flex-1 flex min-h-0">
                {chartData.length === 0 ? (
                    <div className="flex-1 flex flex-col items-center justify-center opacity-20 gap-2">
                        <RotateCcw className="h-5 w-5 animate-spin" style={{ animationDuration: '4s' }} />
                        <span className="text-[9px] uppercase tracking-widest font-bold">Run simulation to populate telemetry</span>
                    </div>
                ) : (
                    signals.map((sig) => (
                        <div key={sig.key} className="flex-1 flex flex-col min-w-0 border-r border-white/10 last:border-r-0 px-1 py-1">
                            <div className="flex justify-between px-2 mb-0.5">
                                <span className="text-[8px] font-bold uppercase tracking-tighter" style={{ color: sig.color }}>{sig.label}</span>
                                <span className="text-[8px] text-[#878787] font-mono">{sig.unit}</span>
                            </div>
                            <div className="flex-1 min-h-0">
                                <ResponsiveContainer width="100%" height="100%" minWidth={1} minHeight={1}>
                                    <AreaChart data={chartData} margin={{ top: 2, right: 2, left: -24, bottom: 0 }}>
                                        <defs>
                                            <linearGradient id={`g${sig.key}`} x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="10%" stopColor={sig.color} stopOpacity={0.3} />
                                                <stop offset="95%" stopColor={sig.color} stopOpacity={0} />
                                            </linearGradient>
                                        </defs>
                                        <CartesianGrid strokeDasharray="2 4" stroke="rgba(255,255,255,0.04)" vertical={false} />
                                        <YAxis domain={sig.domain} fontSize={7} stroke="rgba(255,255,255,0.1)" tickLine={false} axisLine={false} />
                                        <XAxis dataKey="t" hide />
                                        <Tooltip contentStyle={{ backgroundColor: '#171717', border: '1px solid rgba(255,255,255,0.08)', fontSize: 9 }} cursor={{ stroke: 'rgba(255,255,255,0.1)' }} />
                                        <Area type="monotone" dataKey={sig.key} stroke={sig.color} strokeWidth={1.5} fill={`url(#g${sig.key})`} isAnimationActive={false} dot={false} />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}

// ─── Right: Analysis Panel ────────────────────────────────────────────────────

function AnalysisPanel({ deviceConfig, fidelity, onInjectFault, safetyLog, scenarios, activeScenario, setActiveScenario, onLoadScenario, onResetBaseline }) {
    const faultsEnabled = FIDELITY_FAULT_LOCK[fidelity];

    return (
        <div className="w-[320px] bg-[#171717] border-l border-white/10 flex flex-col shrink-0 overflow-y-auto"
            style={{ scrollbarWidth: 'thin', scrollbarColor: '#2f2f2f transparent' }}>

            {/* Fidelity summary */}
            <div className="px-5 pt-4 pb-3 border-b border-white/10 shrink-0">
                <div className="flex items-center gap-2 mb-1.5">
                    <Sliders className="h-4 w-4 text-[#38BDF8]" />
                    <span className="text-[11px] font-bold uppercase tracking-widest text-[#878787]">What-if Analysis</span>
                </div>
                <p className="text-[10px] text-[#878787] leading-relaxed font-medium">{FIDELITY_DESCRIPTIONS[fidelity]}</p>
            </div>

            {/* Scenario Manager */}
            <section className="px-5 pt-4 pb-4 border-b border-white/10">
                <div className="flex items-center gap-2 mb-2.5">
                    <BookOpen className="h-3.5 w-3.5 text-[#878787]" />
                    <span className="text-[10px] font-bold uppercase tracking-tight text-[#878787]">Scenarios</span>
                </div>
                <div className="space-y-2">
                    {scenarios.map((s) => (
                        <button key={s.name} onClick={() => { setActiveScenario(s.name); onLoadScenario(s.params); }}
                            className={cn('w-full text-left px-3 py-2.5 rounded-xl text-[11px] font-bold border transition-all',
                                activeScenario === s.name ? 'bg-[#2f2f2f] border-white/20 text-white' : 'bg-[#212121] border-white/10 text-[#878787] hover:border-white/20 hover:text-[#ececec]')}>
                            {s.name}
                        </button>
                    ))}
                    <button onClick={onResetBaseline}
                        className="w-full flex items-center gap-2 px-3 py-2.5 rounded-xl text-[10px] font-bold border bg-[#212121] border-white/10 text-[#878787] hover:text-[#ececec] transition-all">
                        <RotateCcw className="h-3 w-3" />Reset to Baseline
                    </button>
                </div>
            </section>

            {/* Fault Injection Matrix */}
            <section className="px-5 pt-4 pb-4 border-b border-white/10">
                <div className="flex items-center gap-2 mb-3">
                    <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
                    <span className="text-[10px] font-bold uppercase tracking-tight text-amber-500/80">Fault Injection</span>
                    {!faultsEnabled && (
                        <span className="ml-auto text-[8px] text-[#878787] italic">Requires L3</span>
                    )}
                </div>
                <div className="grid grid-cols-1 gap-2">
                    {deviceConfig.faultMatrix.map(({ label, param, bias, color }) => (
                        <button key={label} disabled={!faultsEnabled}
                            onClick={() => onInjectFault(param, bias)}
                            className={cn('flex items-center gap-2.5 px-3.5 py-3 rounded-xl border text-left transition-all',
                                !faultsEnabled ? 'opacity-30 cursor-not-allowed bg-[#212121] border-white/10 text-[#878787]'
                                    : color === 'red' ? 'bg-red-500/5 border-red-500/15 hover:border-red-500/40 hover:bg-red-500/10 text-[#ececec]'
                                        : 'bg-amber-500/5 border-amber-500/15 hover:border-amber-500/35 hover:bg-amber-500/10 text-[#ececec]')}>
                            <div className={cn('h-2 w-2 rounded-full shrink-0', color === 'red' ? 'bg-red-500' : 'bg-amber-400')} />
                            <span className="text-[11px] font-bold leading-tight">{label}</span>
                        </button>
                    ))}
                </div>
            </section>

            {/* Safety Event Log */}
            <section className="px-5 pt-4 pb-5 flex-1">
                <div className="flex items-center gap-2 mb-3">
                    <Bell className="h-3.5 w-3.5 text-[#878787]" />
                    <span className="text-[10px] font-bold uppercase tracking-tight text-[#878787]">Safety Event Log</span>
                    {safetyLog.length > 0 && (
                        <span className="ml-auto h-5 w-5 rounded-full bg-red-500 text-[10px] font-bold text-white flex items-center justify-center shadow-lg shadow-red-500/20">{safetyLog.length}</span>
                    )}
                </div>

                {/* Safety rules reference */}
                <div className="mb-3 space-y-2">
                    {deviceConfig.safetyRules.map((rule, i) => (
                        <div key={i} className="px-3 py-2 bg-[#212121] border border-white/10 rounded-xl">
                            <div className="flex items-center gap-1.5 mb-1">
                                <ShieldCheck className="h-3 w-3 text-[#38BDF8]/60 shrink-0" />
                                <span className="text-[10px] font-bold text-[#ececec]">{rule.rule}</span>
                            </div>
                            <span className="text-[9px] text-[#878787] font-mono block">{rule.param} {rule.threshold}</span>
                            <span className="text-[9px] text-[#38BDF8]/50 font-mono block italic">{rule.iso}</span>
                        </div>
                    ))}
                </div>

                {/* Active events */}
                <div className="min-h-[80px] bg-[#212121] border border-white/10 rounded-xl p-3 space-y-2">
                    {safetyLog.length === 0 ? (
                        <div className="flex items-center justify-center h-12">
                            <span className="text-[10px] text-[#878787] italic uppercase tracking-widest font-bold">No active events</span>
                        </div>
                    ) : safetyLog.map((evt, i) => (
                        <div key={i} className="flex items-start gap-2 pb-2 border-b border-white/10 last:border-0 last:pb-0">
                            <AlertTriangle className="h-3 w-3 text-red-400 shrink-0 mt-0.5" />
                            <span className="text-[10px] text-[#ececec] leading-normal">{evt}</span>
                        </div>
                    ))}
                </div>
            </section>
        </div>
    );
}

// ─── Root Component ───────────────────────────────────────────────────────────

export default function ProfessionalSimulator({ deviceType, designData }) {
    const key = deviceKey(deviceType);
    const cfg = useMemo(() => {
        if (designData) return buildSimConfigFromDesign(key, designData);
        return DEVICE_CONFIGS[key] || DEVICE_CONFIGS.dialysis;
    }, [key, designData]);

    const [simState, setSimState] = useState('IDLE');
    const [fidelity, setFidelity] = useState('L2');
    const [speed, setSpeed] = useState('1×');
    const [modes, setModes] = useState({});
    const [fullData, setFullData] = useState([]);
    const [animIdx, setAnimIdx] = useState(0);
    const [liveData, setLiveData] = useState([]);
    const [frozenData, setFrozenData] = useState([]);
    const [frozen, setFrozen] = useState(false);
    const [safetyLog, setSafetyLog] = useState([]);
    const [activeScenario, setActiveScenario] = useState('Baseline');
    const [loading, setLoading] = useState(false);
    const [activeLayer, setActiveLayer] = useState('system'); // 'system' | 'hardware'
    const [panelCollapsed, setPanelCollapsed] = useState(false);
    const animRef = useRef(null);

    // speed multiplier
    const delay = speed === '10×' ? 6 : speed === '2×' ? 30 : 60;

    // Animation loop
    useEffect(() => {
        if (simState !== 'RUNNING' || fullData.length === 0 || animIdx >= fullData.length) {
            if (simState === 'RUNNING' && animIdx >= fullData.length && fullData.length > 0) setSimState('IDLE');
            return;
        }
        animRef.current = setTimeout(() => {
            const snap = fullData[animIdx];
            if (!frozen) {
                setLiveData(prev => {
                    const row = { t: snap.t, ...snap.values };
                    return [...prev.slice(-90), row];
                });
            }
            // Safety event detection — thresholds parsed from design-aware cfg.safetyRules
            const vals = snap.values || {};
            const events = [];

            // Helper: parse a numeric threshold from a rule threshold string like "> 37 cmH₂O" or "< 5 L/min"
            const parseThreshold = (ruleRef, direction = '>') => {
                const rule = cfg.safetyRules.find(r => r.rule.includes(ruleRef));
                if (!rule) return { rule: null, val: null };
                const match = rule.threshold.match(/[\d.]+/);
                return { rule, val: match ? parseFloat(match[0]) : null };
            };

            if (vals.ReliefValve === 'OPEN') {
                const rule = cfg.safetyRules.find(r => r.rule.includes('Relief'));
                if (rule) events.push(`T=${snap.t.toFixed(1)}s — ${rule.rule} (${rule.iso})`);
            }
            // High pressure detection (ventilator) — dynamic threshold from cfg
            if (vals.Pressure !== undefined) {
                const { rule, val } = parseThreshold('High Pressure');
                if (rule && val !== null && vals.Pressure > val)
                    events.push(`T=${snap.t.toFixed(1)}s — ${rule.rule}: ${vals.Pressure.toFixed(1)} cmH₂O (${rule.iso})`);
            }
            // Low minute volume (ventilator)
            if (vals.Flow !== undefined && vals.Flow !== 0) {
                const { rule, val } = parseThreshold('Low Minute', '<');
                if (rule && val !== null && vals.Flow < val)
                    events.push(`T=${snap.t.toFixed(1)}s — ${rule.rule}: ${vals.Flow.toFixed(1)} L/min (${rule.iso})`);
            }
            // Disconnect detection (ventilator)
            if (vals.Pressure !== undefined && vals.Pressure !== 0) {
                const { rule, val } = parseThreshold('Disconnect', '<');
                const threshold = val ?? 2;
                if (rule && vals.Pressure < threshold)
                    events.push(`T=${snap.t.toFixed(1)}s — ${rule.rule} (${rule.iso})`);
            }
            // Low SpO2 (pulse oximeter)
            if (vals.SpO2 !== undefined) {
                const { rule, val } = parseThreshold('Low SpO₂', '<');
                if (rule && val !== null && vals.SpO2 < val)
                    events.push(`T=${snap.t.toFixed(1)}s — ${rule.rule}: ${vals.SpO2.toFixed(1)}% (${rule.iso})`);
            }
            // High TMP (dialysis) — dynamic threshold
            if (vals.TMP !== undefined) {
                const { rule, val } = parseThreshold('High TMP');
                if (rule && val !== null && vals.TMP > val)
                    events.push(`T=${snap.t.toFixed(1)}s — ${rule.rule}: ${vals.TMP.toFixed(0)} mmHg (${rule.iso})`);
            }
            // Venous clamp (dialysis)
            if (vals.VenousClamp === 'CLOSED') {
                const rule = cfg.safetyRules.find(r => r.rule.includes('Venous Clamp'));
                if (rule) events.push(`T=${snap.t.toFixed(1)}s — ${rule.rule} (${rule.iso})`);
            }
            // Air-in-blood (dialysis)
            if (vals.AirAlert === 'YES') {
                const rule = cfg.safetyRules.find(r => r.rule.includes('Air Detector'));
                if (rule) events.push(`T=${snap.t.toFixed(1)}s — ${rule.rule} (${rule.iso})`);
            }
            // BFR hypotension drop (dialysis) — dynamic threshold
            if (vals.BFR !== undefined && vals.BFR > 0) {
                const { rule, val } = parseThreshold('Hypotension', '<');
                const threshold = val ?? 150;
                if (rule && vals.BFR < threshold)
                    events.push(`T=${snap.t.toFixed(1)}s — ${rule.rule}: BFR=${vals.BFR.toFixed(0)} mL/min (${rule.iso})`);
            }
            if (events.length > 0) {
                setSafetyLog(p => [...events, ...p].slice(0, 20));
            }
            setAnimIdx(p => p + 1);
        }, delay);
        return () => clearTimeout(animRef.current);
    }, [simState, fullData, animIdx, frozen, delay, cfg.safetyRules]);

    const startSimulation = useCallback(async (faultParam = null, faultBias = 0) => {
        setLoading(true);
        setLiveData([]);
        setAnimIdx(0);
        setSimState('IDLE');
        setSafetyLog([]);
        try {
            const res = faultParam
                ? await runFaultySimulation(deviceType, faultParam, faultBias, 120)
                : await runSimulation(deviceType, 120, fidelity);
            setFullData(res.data.snapshots || []);
            setSimState('RUNNING');
        } catch (e) { console.error(e); }
        finally { setLoading(false); }
    }, [deviceType, fidelity]);

    const handleRun = () => {
        if (simState === 'RUNNING') { setSimState('PAUSED'); return; }
        if (simState === 'PAUSED') { setSimState('RUNNING'); return; }
        startSimulation();
    };

    const handleReset = () => {
        clearTimeout(animRef.current);
        setSimState('IDLE'); setAnimIdx(0); setLiveData([]); setSafetyLog([]);
    };

    const handleStep = () => {
        if (simState === 'RUNNING') setSimState('PAUSED');
        setAnimIdx(p => {
            const next = Math.min(p + 1, fullData.length - 1);
            if (fullData[next]) {
                const snap = fullData[next];
                setLiveData(prev => [...prev.slice(-90), { t: snap.t, ...snap.values }]);
            }
            return next;
        });
    };

    const handleModeChange = (comp, mode) => {
        setModes(prev => ({ ...prev, [comp]: mode }));
        // Device-specific fault mapping
        const faultMap = {
            ventilator: { Failed: ['compliance', -0.9], Noisy: ['leak', 0.15] },
            dialysis: { Failed: ['clog', 0.7], Noisy: ['resistance', 0.5] }
        };
        const mapping = faultMap[key] || faultMap.dialysis;
        if (mode === 'Failed' && mapping.Failed) startSimulation(mapping.Failed[0], mapping.Failed[1]);
        else if (mode === 'Noisy' && mapping.Noisy) startSimulation(mapping.Noisy[0], mapping.Noisy[1]);
    };

    const handleSnap = () => {
        setFrozenData([...liveData]);
        setFrozen(true);
    };

    const simData = { live: liveData, frozen: frozenData };
    const time = animIdx * 0.1;

    return (
        <div className="w-full h-full flex flex-col font-sans text-white overflow-hidden bg-[#212121]">
            <TopBar
                simState={simState} time={time} speed={speed} setSpeed={setSpeed}
                fidelity={fidelity} setFidelity={setFidelity}
                onRun={handleRun} onStep={handleStep} onReset={handleReset}
                deviceConfig={cfg}
            />

            {/* ── Layer Tab Bar ── */}
            <div className="flex items-center px-5 gap-1 border-b border-white/10 bg-[#212121] shrink-0">
                {[['system', 'System Twin'], ['hardware', 'Hardware / Electronics Twin']].map(([key, label]) => (
                    <button
                        key={key}
                        onClick={() => setActiveLayer(key)}
                        className={cn(
                            'px-5 py-2.5 text-[10px] font-bold uppercase tracking-wider border-b-2 transition-all',
                            activeLayer === key
                                ? 'border-[#38BDF8] text-white'
                                : 'border-transparent text-[#878787] hover:text-[#ececec] hover:border-white/20'
                        )}
                    >
                        {label}
                    </button>
                ))}
                <div className="ml-auto text-[8px] text-[#878787] font-mono italic pr-2">Both layers derive from Design Graph{cfg.designVersion ? ` v${cfg.designVersion}` : ''}</div>
            </div>

            {/* ── Layer-1: System Twin ── */}
            {activeLayer === 'system' && (
                <div className="flex-1 flex overflow-hidden min-h-0">
                    <ComponentsPanel modes={modes} setMode={handleModeChange} deviceConfig={cfg} fidelity={fidelity}
                        panelCollapsed={panelCollapsed} onTogglePanel={() => setPanelCollapsed(p => !p)} />
                    <div className="flex-1 flex flex-col overflow-hidden min-h-0 min-w-0">
                        <ArchitectureView deviceConfig={cfg} simState={simState} modes={modes} />
                        <TelemetryPanel simData={simData} deviceConfig={cfg} fidelity={fidelity}
                            frozen={frozen} setFrozen={setFrozen} onSnap={handleSnap} />
                    </div>
                    <AnalysisPanel
                        deviceConfig={cfg} fidelity={fidelity}
                        onInjectFault={(p, b) => startSimulation(p, b)}
                        safetyLog={safetyLog}
                        scenarios={cfg.scenarios}
                        activeScenario={activeScenario}
                        setActiveScenario={setActiveScenario}
                        onLoadScenario={(params) => { if (params.param) startSimulation(params.param, params.bias); else startSimulation(); }}
                        onResetBaseline={() => { setActiveScenario('Baseline'); handleReset(); }}
                    />
                </div>
            )}

            {/* ── Layer-2: Hardware / Electronics Twin ── */}
            {activeLayer === 'hardware' && (
                <div className="flex-1 overflow-hidden min-h-0">
                    <HardwareTwin
                        deviceType={deviceType}
                        designData={designData}
                        modes={modes}
                        selectedComponent={null}
                        onInjectFault={(p, b) => startSimulation(p, b)}
                        simRunning={simState === 'RUNNING'}
                    />
                </div>
            )}
        </div>
    );
}
