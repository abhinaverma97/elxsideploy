import React, { useState, useEffect } from 'react'
import { runSimulation, runFaultySimulation } from '../api'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Activity, AlertTriangle, Zap, Play, RotateCcw, ActivitySquare, Wind } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { cn } from "@/lib/utils"

export default function SimulationView({ deviceType }) {
	const [data, setData] = useState(null)
	const [fullData, setFullData] = useState([])
	const [animating, setAnimating] = useState(false)
	const [animationIdx, setAnimationIdx] = useState(0)

	const [loading, setLoading] = useState(false)
	const [fidelity, setFidelity] = useState('L3')
	const [faultParam, setFaultParam] = useState('')
	const [faultBias, setFaultBias] = useState(0.2)
	const [activeFault, setActiveFault] = useState(null)

	useEffect(() => {
		if (animating && fullData.length > 0 && animationIdx < fullData.length) {
			const timer = setTimeout(() => {
				setData(prev => prev ? [...prev, fullData[animationIdx]] : [fullData[animationIdx]])
				setAnimationIdx(prev => prev + 1)
			}, 40) // 40ms per frame for a smooth sweep
			return () => clearTimeout(timer)
		} else if (animating && animationIdx >= fullData.length) {
			setAnimating(false)
		}
	}, [animating, fullData, animationIdx])

	const handleRun = async () => {
		setLoading(true)
		setActiveFault(null)
		setAnimating(false)
		try {
			const res = await runSimulation(deviceType, 120, fidelity)
			setFullData(res.data.snapshots)
			setData([res.data.snapshots[0]])
			setAnimationIdx(1)
			setAnimating(true)
		} catch (err) {
			console.error(err)
		} finally {
			setLoading(false)
		}
	}

	const handleRunFault = async (param = faultParam, bias = faultBias) => {
		if (!param) return alert('Please specify a parameter to inject a fault into.')
		setLoading(true)
		setAnimating(false)
		try {
			const res = await runFaultySimulation(deviceType, param, bias, 120)
			if (res.data.error) throw new Error(res.data.error)
			setFullData(res.data.snapshots)
			setData([res.data.snapshots[0]])
			setAnimationIdx(1)
			setAnimating(true)
			setActiveFault({ parameter: param, bias: bias })
		} catch (err) {
			alert(`Fault Injection Failed: ${err.message}`)
		} finally {
			setLoading(false)
		}
	}

	const chartData = data?.map(snap => ({
		time: snap.t,
		...snap.values
	}))

	const lastSnapshot = chartData ? chartData[chartData.length - 1] : null;

	const renderChart = (dataKey, color, label, IconComponent) => (
		<div className="flex-1 min-h-[160px] flex flex-col relative border border-white/5 bg-[#121212] rounded-xl overflow-hidden shadow-inner">
			<div className="absolute top-3 left-4 flex items-center gap-2 z-10">
				<IconComponent className="h-4 w-4" style={{ color }} />
				<span className="text-xs font-bold tracking-wider uppercase" style={{ color }}>{label}</span>
			</div>
			<ResponsiveContainer width="100%" height="100%" minWidth={1} minHeight={1}>
				<LineChart data={chartData} margin={{ top: 30, right: 10, left: -20, bottom: 0 }}>
					<CartesianGrid strokeDasharray="3 3" stroke="#222" vertical={false} />
					<XAxis dataKey="time" hide domain={[0, 12]} type="number" />
					<YAxis domain={['auto', 'auto']} stroke="#555" fontSize={10} tickLine={false} axisLine={false} />
					<Tooltip
						contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333', borderRadius: '8px', fontSize: '12px', color: '#ececec' }}
						itemStyle={{ color: color }}
						labelStyle={{ display: 'none' }}
						isAnimationActive={false}
					/>
					<Line type="monotone" dataKey={dataKey} stroke={color} strokeWidth={2.5} dot={false} isAnimationActive={false} />
				</LineChart>
			</ResponsiveContainer>
		</div>
	)

	return (
		<div className="space-y-6 w-full h-[calc(100vh-8rem)] flex flex-col pt-2">
			<div className="flex items-center justify-between pb-4 border-b border-white/5 shrink-0">
				<div>
					<h2 className="text-2xl font-semibold tracking-tight">ICU Telemetry Dashboard</h2>
					<p className="text-muted-foreground text-sm mt-1">First-principles simulation and temporal IO validation.</p>
				</div>

				<div className="flex gap-4">
					<div className="flex p-1 bg-[#171717] rounded-lg w-fit">
						{['L1', 'L2', 'L3'].map(l => (
							<button
								key={l}
								onClick={() => setFidelity(l)}
								className={cn(
									"px-4 py-1.5 rounded-md text-sm font-medium transition-all",
									fidelity === l
										? "bg-[#2f2f2f] text-white shadow-sm"
										: "text-muted-foreground hover:text-[#ececec]"
								)}
							>
								{l}
							</button>
						))}
					</div>
					<Button onClick={handleRun} disabled={loading || animating} className="gap-2 bg-white text-black hover:bg-white/90 shadow-lg shadow-white/5">
						{animating ? <RotateCcw className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4 fill-black" />}
						{animating ? 'Simulating...' : 'Run 12s Loop'}
					</Button>
				</div>
			</div>

			<div className="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-6 min-h-0 overflow-hidden pb-4">

				{/* Chart Panel (3 stacked panes) */}
				<div className="lg:col-span-3 flex flex-col gap-4 overflow-y-auto pr-2 custom-scrollbar">
					{chartData ? (
						<>
							{renderChart(deviceType === 'ventilator' ? "Pressure" : "BFR", "#fbbf24", deviceType === 'ventilator' ? "PAW (cmH2O)" : "Blood Flow (mL/min)", Activity)}
							{renderChart(deviceType === 'ventilator' ? "Flow" : "DFR", "#2dd4bf", deviceType === 'ventilator' ? "Flow (L/min)" : "Dialysate Flow (mL/min)", Wind)}
							{renderChart(deviceType === 'ventilator' ? "Volume" : "TMP", "#a855f7", deviceType === 'ventilator' ? "Volume (mL)" : "TMP (mmHg)", Activity)}
						</>
					) : (
						<div className="flex-1 flex flex-col items-center justify-center text-muted-foreground/40 gap-4 border border-white/5 rounded-2xl bg-[#121212] min-h-[500px]">
							<RotateCcw className="h-12 w-12 animate-spin-slow opacity-30" />
							<p className="text-sm font-medium text-[#878787]">Awaiting simulation start...</p>
						</div>
					)}
				</div>

				{/* Side Panel (What-If & Telemetry) */}
				<div className="lg:col-span-1 space-y-4 overflow-y-auto pr-2 custom-scrollbar">

					{/* IO Telemetry */}
					<div className="border border-white/5 rounded-2xl bg-[#121212] p-5 space-y-4 shadow-sm">
						<div className="pb-3 border-b border-white/5">
							<h3 className="text-xs uppercase tracking-widest text-[#878787] flex items-center gap-2 font-semibold">
								<ActivitySquare className="h-4 w-4 text-emerald-400" /> Digital IO States
							</h3>
						</div>
						{lastSnapshot ? (
							<div className="space-y-3 font-mono text-[11px]">
								{Object.entries(lastSnapshot).map(([k, v]) => {
									if (['time', 'Pressure', 'Flow', 'Volume', 'BFR', 'DFR', 'TMP'].includes(k)) return null;
									const isAlert = (k === 'ReliefValve' && v === 'OPEN') || (k === 'VenousClamp' && v === 'CLOSED') || (k === 'AirAlert' && v === 'YES');
									return (
										<div key={k} className="flex justify-between items-center bg-[#1a1a1a] px-3 py-2 rounded-lg border border-white/5 transition-colors duration-150">
											<span className="text-muted-foreground">{k}</span>
											<span className={cn("font-bold tracking-wider", isAlert ? "text-red-500 animate-pulse" : "text-emerald-400")}>
												{v}
											</span>
										</div>
									)
								})}
							</div>
						) : (
							<div className="text-xs text-muted-foreground text-center py-4 bg-[#1a1a1a] rounded-lg border border-white/5">NO DATA SOURCE</div>
						)}
					</div>

					{/* What-If Controls */}
					<div className="border border-white/5 rounded-2xl bg-[#121212] p-5 space-y-5 shadow-sm">
						<div className="pb-3 border-b border-white/5">
							<h3 className="text-xs uppercase tracking-widest text-[#878787] flex items-center gap-2 font-semibold">
								<Zap className="h-4 w-4 text-amber-500" /> Patient What-If Analysis
							</h3>
						</div>

						{deviceType === 'ventilator' && (
							<div className="space-y-2 pb-5 mb-5 border-b border-white/5">
								<Button size="sm" variant="outline" onClick={() => handleRunFault('compliance', -0.5)} disabled={animating} className="w-full text-xs justify-start border-white/5 text-white bg-[#1a1a1a] hover:bg-white/10 hover:text-white transition-colors h-9 disabled:opacity-50">
									Stiff Lungs (Compliance -50%)
								</Button>
								<Button size="sm" variant="outline" onClick={() => handleRunFault('resistance', 0.8)} disabled={animating} className="w-full text-xs justify-start border-white/5 text-white bg-[#1a1a1a] hover:bg-white/10 hover:text-white transition-colors h-9 disabled:opacity-50">
									Airway Obstruction (Resistance +80%)
								</Button>
								<Button size="sm" variant="outline" onClick={() => handleRunFault('rate', 0.5)} disabled={animating} className="w-full text-xs justify-start border-white/5 text-white bg-[#1a1a1a] hover:bg-white/10 hover:text-white transition-colors h-9 disabled:opacity-50">
									Tachypnea (Resp Rate +50%)
								</Button>
							</div>
						)}

						{deviceType === 'dialysis' && (
							<div className="space-y-2 pb-5 mb-5 border-b border-white/5">
								<Button size="sm" variant="outline" onClick={() => handleRunFault('clotting', 0.8)} disabled={animating} className="w-full text-xs justify-start border-white/5 text-white bg-[#1a1a1a] hover:bg-white/10 hover:text-white transition-colors h-9 disabled:opacity-50">
									Filter Clotting (Resistance +80%)
								</Button>
								<Button size="sm" variant="outline" onClick={() => handleRunFault('air', 1.0)} disabled={animating} className="w-full text-xs justify-start border-white/5 text-white bg-[#1a1a1a] hover:bg-white/10 hover:text-white transition-colors h-9 disabled:opacity-50 border-red-500/20 hover:border-red-500/40 text-red-100">
									Extracorporeal Air Bubble Detected
								</Button>
								<Button size="sm" variant="outline" onClick={() => handleRunFault('hypotension', 1.0)} disabled={animating} className="w-full text-xs justify-start border-white/5 text-white bg-[#1a1a1a] hover:bg-white/10 hover:text-white transition-colors h-9 disabled:opacity-50">
									Patient Hypotension Crash
								</Button>
							</div>
						)}

						<div className="space-y-4">
							<Label className="text-[11px] text-[#878787] font-medium tracking-wide uppercase">Custom Injection</Label>
							<Input
								type="text"
								value={faultParam}
								onChange={(e) => setFaultParam(e.target.value)}
								placeholder="Parameter (e.g. resistance)"
								className="bg-[#1a1a1a] border-white/5 text-[#ececec] text-xs h-9 focus-visible:ring-1 focus-visible:ring-amber-500/50"
							/>
							<div className="flex flex-col pt-1 gap-2">
								<div className="flex justify-between">
									<Label className="text-[10px] text-[#878787] uppercase tracking-wider">Bias offset: {Math.round(faultBias * 100)}%</Label>
								</div>
								<input
									type="range" min="-0.8" max="1.5" step="0.1"
									value={faultBias}
									onChange={(e) => setFaultBias(parseFloat(e.target.value))}
									className="w-full accent-amber-500 h-1.5 bg-[#1a1a1a] rounded-lg appearance-none cursor-pointer"
								/>
							</div>
							<Button
								variant="outline"
								onClick={() => handleRunFault()}
								disabled={loading || animating}
								className="w-full h-9 text-xs gap-2 border-amber-500/20 text-amber-500 hover:bg-amber-500/10 hover:border-amber-500/50 hover:text-amber-400 bg-transparent mt-2 transition-all disabled:opacity-50"
							>
								<AlertTriangle className="h-3.5 w-3.5" /> Execute Param Shift
							</Button>
						</div>

						{activeFault && (
							<div className="border border-red-500/30 bg-[#1a1a1a] rounded-xl p-4 text-[11px] text-red-400 font-medium leading-relaxed relative overflow-hidden group hover:border-red-500/50 transition-colors">
								<div className="absolute top-0 left-0 w-1 h-full bg-red-500/50 group-hover:bg-red-500 transition-colors"></div>
								<div className="flex items-center gap-1.5 mb-1.5 text-red-500">
									<AlertTriangle className="h-3.5 w-3.5" />
									<span className="uppercase tracking-wider font-bold text-[10px]">Active Shift</span>
								</div>
								<span className="text-white">{activeFault.parameter}</span> modified by <span className="text-white">{Math.round(activeFault.bias * 100)}%</span>
								<div className="mt-2 text-[#878787] font-normal leading-tight">Monitor IO telemetry and architecture trip states.</div>
							</div>
						)}
					</div>
				</div>
			</div>
		</div>
	)
}
