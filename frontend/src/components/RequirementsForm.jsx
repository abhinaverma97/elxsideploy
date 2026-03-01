import React, { useState } from 'react'
import { addRequirement, analyzeRequirement } from '../api'
import { ClipboardList, Plus, Sparkles, AlertCircle, Info, RotateCcw, CheckCircle2, Activity } from 'lucide-react'

import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

const SAMPLES = {
	ventilator: {
		id: 'REQ-VENT-001',
		title: 'Peak Inspiratory Pressure (PIP) Limit',
		description: 'The ventilator pneumatic delivery subsystem shall maintain Peak Inspiratory Pressure (PIP) within defined bounds to prevent barotrauma. The Main Control Unit shall command the inspiratory proportional valve using a PWM signal.',
		type: 'performance',
		priority: 'SHALL',
		subsystem: 'PneumaticsControl',
		status: 'Draft',
		fr_text: 'The pneumatics subsystem shall control and deliver inspiratory pressure between 5–40 cmH2O in real time during each breath cycle. The safety monitor shall detect airway pressure >60 cmH2O, trigger a P1 alarm, and actuate the exhalation valve.',
		nfr_text: 'PIP regulation accuracy shall be within ±2 cmH2O at all flow rates. Alarm response time from threshold breach to valve open shall be ≤200ms.',
		verification: { method: 'simulation', description: 'Run Digital Twin closed-loop patient lung simulation under fault conditions.' },

		// Performance Bounds
		bounds: {
			parameter: 'PIP',
			min: '5',
			max: '40',
			unit: 'cmH2O',
			responseTimeMs: '100'
		},
		min_value: '5',
		max_value: '40',
		unit: 'cmH2O',
		tolerance: '2.0',
		response_time_ms: '100',

		// Interface
		interface: 'MainMCU -> InspValve',
		protocol: 'PWM (10kHz)',

		// Safety
		hazard: 'Barotrauma / Over-pressurization',
		severity: 'Critical',
		probability: 'Occasional',
		standard: 'ISO 80601-2-12',
		clause: '201.12.4',
		parameter: 'AirwayPressure',
	},
	dialysis: {
		id: 'REQ-DIAL-001',
		title: 'Air-in-Blood Detection & Ultrafiltration',
		description: 'The system shall detect air bubbles in the extracorporeal blood circuit and stop the blood pump, while the Master Controller commands the arterial peristaltic blood pump over CAN-FD.',
		type: 'safety',
		priority: 'SHALL',
		subsystem: 'ExtracorporealSafety',
		status: 'Draft',
		fr_text: 'The ultrasonic bubble detector shall continuously monitor the venous line and command an immediate blood pump stop upon air detection. The Master Controller shall calculate fluid removal rate.',
		nfr_text: 'Bubble detection response time shall be ≤500ms. Cumulative UF volume error shall not exceed ±1% or ±50mL over a 4-hour session. ISO 10993 cytotoxicity parameters must be met.',
		verification: { method: 'simulation', description: 'Inject air into virtual sensor and verify pump cutoff response time. Run 4-hour closed loop UF simulation.' },

		// Performance Bounds
		bounds: {
			parameter: 'UFRate',
			min: '0',
			max: '4000',
			unit: 'mL/hr',
			responseTimeMs: '500'
		},
		min_value: '0',
		max_value: '4000',
		unit: 'mL/hr',
		tolerance: '30.0',
		response_time_ms: '500',

		// Interface
		interface: 'MainMCU -> ArterialPump',
		protocol: 'CAN-FD (1Mbps)',

		// Safety / Regulatory
		hazard: 'Air Embolism (Critical)',
		severity: 'Critical',
		probability: 'Probable',
		standard: 'ISO 60601-2-16',
		clause: '201.12.4.102',
		parameter: 'AirBubble',
	}
}


const INITIAL_STATE = {
	id: 'REQ-NEW-001',
	title: '',
	description: '',
	parent_id: '',
	type: 'functional',
	priority: 'SHALL',
	status: 'Draft',
	subsystem: '',
	parameter: '',
	min_value: '',
	max_value: '',
	unit: '',
	tolerance: '',
	response_time_ms: '',
	interface: '',
	protocol: '',
	hazard: '',
	severity: 'Low',
	probability: 'Remote',
	standard: '',
	clause: '',
	fr_text: '',
	nfr_text: '',
	verification: { method: 'simulation', description: '' }
}

export default function RequirementsForm({ deviceType, setView }) {
	const [req, setReq] = useState(INITIAL_STATE)
	const [loading, setLoading] = useState(false)
	const [msg, setMsg] = useState(null)
	const [submittedReqs, setSubmittedReqs] = useState([])

	const loadSample = () => {
		const sample = SAMPLES[deviceType] || SAMPLES.ventilator
		setReq({ ...INITIAL_STATE, ...sample })
		setMsg({ type: 'success', text: `Sample loaded: ${sample.title}` })
	}

	const resetForm = () => {
		setReq(INITIAL_STATE)
		setMsg(null)
	}

	const handleSubmit = async (e) => {
		e.preventDefault()
		setLoading(true)

		let enriched = { ...req, verification: { ...req.verification } }

		// Silently enrich empty fields from FR/NFR text if provided
		const hasFrNfr = enriched.fr_text?.trim() || enriched.nfr_text?.trim()
		if (hasFrNfr) {
			try {
				const combinedText = [enriched.fr_text, enriched.nfr_text].filter(Boolean).join(' ')
				const res = await analyzeRequirement(combinedText, deviceType)
				const f = res.data.fields
				// Only backfill fields the user left empty
				if (!enriched.subsystem && f.subsystem) enriched.subsystem = f.subsystem
				if (enriched.type === 'functional' && f.type && f.type !== 'functional') enriched.type = f.type
				if (!enriched.parameter && f.parameter) enriched.parameter = f.parameter
				if (!enriched.unit && f.unit) enriched.unit = f.unit
				if (!enriched.min_value && f.min_value != null) enriched.min_value = String(f.min_value)
				if (!enriched.max_value && f.max_value != null) enriched.max_value = String(f.max_value)
				if (!enriched.response_time_ms && f.response_time_ms != null) enriched.response_time_ms = String(f.response_time_ms)
				if (!enriched.hazard && f.hazard) enriched.hazard = f.hazard
				if (enriched.severity === 'Low' && f.severity && f.severity !== 'Low') enriched.severity = f.severity
				if (!enriched.standard && f.standard) enriched.standard = f.standard
				if (!enriched.clause && f.clause) enriched.clause = f.clause
				if (!enriched.verification.description && f.verification_description)
					enriched.verification.description = f.verification_description
				// Sync back to display
				setReq(enriched)
			} catch (_) {
				// Silent — proceed with what user entered
			}
		}

		const payload = { ...enriched, verification: { ...enriched.verification } }
		if (payload.min_value !== '') payload.min_value = parseFloat(payload.min_value)
		if (payload.max_value !== '') payload.max_value = parseFloat(payload.max_value)
		if (payload.tolerance !== '') payload.tolerance = parseFloat(payload.tolerance)
		if (payload.response_time_ms !== '') payload.response_time_ms = parseInt(payload.response_time_ms)

		Object.keys(payload).forEach(key => {
			if (payload[key] === '') delete payload[key]
		})

		try {
			await addRequirement(payload)
			setMsg({ type: 'success', text: `Requirement ${enriched.id} added successfully.` })
			setSubmittedReqs(prev => [payload, ...prev].slice(0, 5))

			// Navigate to the design page after a short delay for UX
			if (setView) {
				setTimeout(() => {
					setView('design')
				}, 600)
			}
		} catch (err) {
			console.error('SUBMIT_ERROR:', err)
			const errorDetail = err.response?.data?.detail
			let errorMsg = 'Add failed.'

			if (Array.isArray(errorDetail)) {
				errorMsg = typeof errorDetail[0] === 'string' ? errorDetail[0] : (errorDetail[0]?.msg || JSON.stringify(errorDetail[0]))
			} else if (typeof errorDetail === 'string') {
				errorMsg = errorDetail
			}
			setMsg({ type: 'error', text: errorMsg })
		} finally {
			setLoading(false)
		}
	}

	const SectionHeader = ({ title, icon: Icon }) => (
		<div className="flex items-center gap-2 border-b pb-2 mb-4">
			<Icon size={16} className="text-muted-foreground" />
			<h4 className="text-sm font-semibold tracking-tight text-foreground">{title}</h4>
		</div>
	)

	return (
		<div className="space-y-6">
			{/* Page Header */}
			<div className="flex items-center justify-between pb-4 border-b border-white/5">
				<div>
					<h2 className="text-2xl font-semibold tracking-tight">Requirements Intake</h2>
					<p className="text-muted-foreground text-sm mt-1">Define functional and non-functional requirements for {deviceType}.</p>
				</div>
				<div className="flex gap-2">
					<Button variant="outline" size="sm" onClick={resetForm} className="bg-transparent border-white/10 hover:bg-white/5">
						<RotateCcw className="mr-2 h-4 w-4" /> Reset
					</Button>
					<Button variant="secondary" size="sm" onClick={() => loadSample()} className="bg-white/10 hover:bg-white/15 text-white">
						<Sparkles className="mr-2 h-4 w-4" /> Load Sample
					</Button>
					{/* Secondary sample buttons hidden per user request */}
					{/* 
					{deviceType === 'ventilator' && (
						<>
							<Button variant="secondary" size="sm" onClick={() => loadSample('interface')} className="bg-white/10 hover:bg-white/15 text-white">
								<Activity className="mr-2 h-4 w-4" /> Load Interface Sample
							</Button>
							<Button variant="secondary" size="sm" onClick={() => loadSample('safety')} className="bg-destructive/20 hover:bg-destructive/30 text-destructive-foreground border border-destructive/50">
								<AlertCircle className="mr-2 h-4 w-4" /> Load Safety Sample
							</Button>
						</>
					)}
					{deviceType === 'dialysis' && (
						<>
							<Button variant="secondary" size="sm" onClick={() => loadSample('performance')} className="bg-white/10 hover:bg-white/15 text-white">
								<Activity className="mr-2 h-4 w-4" /> Load Performance Sample
							</Button>
							<Button variant="secondary" size="sm" onClick={() => loadSample('interface')} className="bg-white/10 hover:bg-white/15 text-white">
								<Activity className="mr-2 h-4 w-4" /> Load Interface Sample
							</Button>
							<Button variant="secondary" size="sm" onClick={() => loadSample('safety')} className="bg-destructive/20 hover:bg-destructive/30 text-destructive-foreground border border-destructive/50">
								<AlertCircle className="mr-2 h-4 w-4" /> Load Safety Sample
							</Button>
						</>
					)}
					*/}
				</div>
			</div>

			<div className="w-full">
				<form onSubmit={handleSubmit} className="space-y-8">

					<div className="space-y-4">
						<SectionHeader title="Identification & Classification" icon={Info} />

						<div className="grid grid-cols-1 md:grid-cols-4 gap-4">
							<div className="space-y-1">
								<Label className="text-xs text-[#878787] font-medium">REQ ID</Label>
								<Input className="bg-[#171717] border-white/10 focus-visible:ring-1 focus-visible:ring-white/20 text-[#ececec]" value={req.id} onChange={e => setReq({ ...req, id: e.target.value })} required />
							</div>
							<div className="md:col-span-2 space-y-1">
								<Label className="text-xs text-[#878787] font-medium">Title</Label>
								<Input className="bg-[#171717] border-white/10 focus-visible:ring-1 focus-visible:ring-white/20 text-[#ececec]" value={req.title} onChange={e => setReq({ ...req, title: e.target.value })} required />
							</div>
							<div className="space-y-1">
								<Label className="text-xs text-[#878787] font-medium">Requirement Type</Label>
								<Select value={req.type} onValueChange={v => setReq({ ...req, type: v })}>
									<SelectTrigger className="bg-[#171717] border-white/10 focus-visible:ring-1 focus-visible:ring-white/20 text-[#ececec]">
										<SelectValue placeholder="Select type..." />
									</SelectTrigger>
									<SelectContent className="bg-[#171717] border-white/10 text-white">
										<SelectItem value="functional">Functional</SelectItem>
										<SelectItem value="performance">Performance</SelectItem>
										<SelectItem value="interface">Interface</SelectItem>
										<SelectItem value="safety">Safety (ISO 14971)</SelectItem>
										<SelectItem value="regulatory">Regulatory</SelectItem>
										<SelectItem value="environmental">Environmental</SelectItem>
									</SelectContent>
								</Select>
							</div>
						</div>
					</div>

					<div className="space-y-4">
						<div className="grid grid-cols-1 md:grid-cols-4 gap-4">
							<div className="space-y-1">
								<Label className="text-xs text-[#878787] font-medium">Status</Label>
								<Select value={req.status} onValueChange={v => setReq({ ...req, status: v })}>
									<SelectTrigger className="bg-[#171717] border-white/10 focus-visible:ring-1 focus-visible:ring-white/20 text-[#ececec]">
										<SelectValue placeholder="Select status..." />
									</SelectTrigger>
									<SelectContent className="bg-[#171717] border-white/10 text-white">
										<SelectItem value="draft">Draft</SelectItem>
										<SelectItem value="review">Under Review</SelectItem>
										<SelectItem value="approved">Approved</SelectItem>
									</SelectContent>
								</Select>
							</div>
							<div className="space-y-1 md:col-span-3">
								<Label className="text-xs text-[#878787] font-medium">Target Subsystem</Label>
								<Input list="subsystems" className="bg-[#171717] border-white/10 focus-visible:ring-1 focus-visible:ring-white/20 text-[#ececec]" value={req.subsystem} onChange={e => setReq({ ...req, subsystem: e.target.value })} placeholder="e.g. Blower Control" />
								<datalist id="subsystems">
									{deviceType === 'ventilator' && (
										<>
											<option value="PneumaticsControl" />
											<option value="MainControlUnit" />
											<option value="PowerSupply" />
											<option value="GasMixer" />
											<option value="SafetyMonitor" />
											<option value="PatientInterface" />
											<option value="Display&UI" />
										</>
									)}
									{deviceType === 'dialysis' && (
										<>
											<option value="BloodCircuit" />
											<option value="DialysateCircuit" />
											<option value="Ultrafiltration" />
											<option value="ExtracorporealSafety" />
											<option value="ControlSystem" />
											<option value="PowerAndThermal" />
											<option value="Display&UI" />
										</>
									)}
									{deviceType === 'pulse_ox' && (
										<>
											<option value="OpticalSensor" />
											<option value="SignalProcessing" />
											<option value="DisplayUnit" />
										</>
									)}
								</datalist>
							</div>
						</div>
					</div>

					<div className="space-y-2">
						<Label className="text-xs text-[#878787] font-medium">Technical Description</Label>
						<textarea
							className="flex w-full rounded-md border border-white/10 bg-[#171717] px-3 py-2 text-sm text-[#ececec] placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-white/20 min-h-[100px] resize-y"
							value={req.description}
							onChange={e => setReq({ ...req, description: e.target.value })}
							required
						/>
					</div>

					{/* FR / NFR Sections */}
					<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
						<div className="space-y-2">
							<SectionHeader title="Functional Requirement" icon={ClipboardList} />
							<p className="text-[11px] text-[#878787] -mt-2">What the system must DO — actions, outputs, measurable behaviors.</p>
							<textarea
								className="flex w-full rounded-md border border-white/10 bg-[#171717] px-3 py-2 text-sm text-[#ececec] placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-white/20 min-h-[90px] resize-y"
								value={req.fr_text}
								onChange={e => setReq({ ...req, fr_text: e.target.value })}
								placeholder="e.g. The device shall deliver tidal volumes between 200–2000 mL with ±5% accuracy."
							/>
						</div>
						<div className="space-y-2">
							<SectionHeader title="Non-Functional Requirement" icon={ClipboardList} />
							<p className="text-[11px] text-[#878787] -mt-2">HOW the system must behave — reliability, speed, compliance, EMI, safety.</p>
							<textarea
								className="flex w-full rounded-md border border-white/10 bg-[#171717] px-3 py-2 text-sm text-[#ececec] placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-white/20 min-h-[90px] resize-y"
								value={req.nfr_text}
								onChange={e => setReq({ ...req, nfr_text: e.target.value })}
								placeholder="e.g. Alarm response time shall not exceed 500ms. Device shall be EMI-compliant per IEC 60601-1-2."
							/>
						</div>
					</div>

					{/* CONDITIONAL SECTIONS */}
					{(req.type === 'performance' || req.type === 'functional') && (
						<div className="space-y-4">
							<SectionHeader title="Performance Bounds" icon={Activity} />
							<div className="grid grid-cols-1 md:grid-cols-5 gap-4">
								<div className="md:col-span-2 space-y-1">
									<Label className="text-xs text-[#878787] font-medium">Parameter Name</Label>
									<Input className="bg-[#171717] border-white/10 focus-visible:ring-1 focus-visible:ring-white/20 text-[#ececec]" value={req.bounds?.parameter || ''} onChange={e => setReq({ ...req, bounds: { ...req.bounds, parameter: e.target.value } })} placeholder="e.g. Pressure" />
								</div>
								<div className="space-y-1">
									<Label className="text-xs text-[#878787] font-medium">Min Value</Label>
									<Input className="bg-[#171717] border-white/10 focus-visible:ring-1 focus-visible:ring-white/20 text-[#ececec]" type="number" step="any" value={req.bounds?.min || ''} onChange={e => setReq({ ...req, bounds: { ...req.bounds, min: e.target.value } })} />
								</div>
								<div className="space-y-1">
									<Label className="text-xs text-[#878787] font-medium">Max Value</Label>
									<Input className="bg-[#171717] border-white/10 focus-visible:ring-1 focus-visible:ring-white/20 text-[#ececec]" type="number" step="any" value={req.bounds?.max || ''} onChange={e => setReq({ ...req, bounds: { ...req.bounds, max: e.target.value } })} />
								</div>
								<div className="space-y-1">
									<Label className="text-xs text-[#878787] font-medium">Unit</Label>
									<Input className="bg-[#171717] border-white/10 focus-visible:ring-1 focus-visible:ring-white/20 text-[#ececec]" value={req.bounds?.unit || ''} onChange={e => setReq({ ...req, bounds: { ...req.bounds, unit: e.target.value } })} placeholder="e.g. L/min" />
								</div>
								<div className="space-y-1">
									<Label className="text-xs text-[#878787] font-medium">Response (ms)</Label>
									<Input className="bg-[#171717] border-white/10 focus-visible:ring-1 focus-visible:ring-white/20 text-[#ececec]" type="number" value={req.bounds?.responseTimeMs || ''} onChange={e => setReq({ ...req, bounds: { ...req.bounds, responseTimeMs: e.target.value } })} />
								</div>
							</div>
						</div>
					)}

					{req.type === 'interface' && (
						<div className="space-y-4">
							<SectionHeader title="Interface Definition" icon={Activity} />
							<div className="grid grid-cols-1 md:grid-cols-3 gap-4">
								<div className="space-y-1">
									<Label className="text-xs text-[#878787] font-medium">Interface Mapping</Label>
									<Input className="bg-[#171717] border-white/10 focus-visible:ring-1 focus-visible:ring-white/20 text-[#ececec]" value={req.interface} onChange={e => setReq({ ...req, interface: e.target.value })} placeholder="Source -> Target" />
								</div>
								<div className="space-y-1">
									<Label className="text-xs text-[#878787] font-medium">Protocol / Signal</Label>
									<Input className="bg-[#171717] border-white/10 focus-visible:ring-1 focus-visible:ring-white/20 text-[#ececec]" value={req.protocol} onChange={e => setReq({ ...req, protocol: e.target.value })} />
								</div>
								<div className="space-y-1">
									<Label className="text-xs text-[#878787] font-medium">Parameter Flow</Label>
									<Input className="bg-[#171717] border-white/10 focus-visible:ring-1 focus-visible:ring-white/20 text-[#ececec]" value={req.parameter} onChange={e => setReq({ ...req, parameter: e.target.value })} />
								</div>
							</div>
						</div>
					)}

					{req.type === 'safety' && (
						<div className="space-y-4">
							<SectionHeader title="ISO 14971 Risk Assessment" icon={AlertCircle} />
							<div className="grid grid-cols-1 md:grid-cols-3 gap-4">
								<div className="space-y-1">
									<Label className="text-xs text-[#878787] font-medium">Hazard Type</Label>
									<Input className="bg-[#171717] border-white/10 focus-visible:ring-1 focus-visible:ring-white/20 text-[#ececec]" value={req.hazard} onChange={e => setReq({ ...req, hazard: e.target.value })} placeholder="e.g. Excessive Pressure" />
								</div>
								<div className="space-y-1">
									<Label className="text-xs text-[#878787] font-medium">Severity</Label>
									<Select value={req.severity} onValueChange={v => setReq({ ...req, severity: v })}>
										<SelectTrigger className="bg-[#171717] border-white/10 focus-visible:ring-1 focus-visible:ring-white/20 text-[#ececec]">
											<SelectValue placeholder="Select severity..." />
										</SelectTrigger>
										<SelectContent className="bg-[#171717] border-white/10 text-white">
											<SelectItem value="Low">Low</SelectItem>
											<SelectItem value="Medium">Medium</SelectItem>
											<SelectItem value="High">High</SelectItem>
											<SelectItem value="Critical">Critical</SelectItem>
										</SelectContent>
									</Select>
								</div>
								<div className="space-y-1">
									<Label className="text-xs text-[#878787] font-medium">Probability (P1)</Label>
									<Select value={req.probability} onValueChange={v => setReq({ ...req, probability: v })}>
										<SelectTrigger className="bg-[#171717] border-white/10 focus-visible:ring-1 focus-visible:ring-white/20 text-[#ececec]">
											<SelectValue placeholder="Select probability..." />
										</SelectTrigger>
										<SelectContent className="bg-[#171717] border-white/10 text-white">
											<SelectItem value="Negligible">Negligible</SelectItem>
											<SelectItem value="Remote">Remote</SelectItem>
											<SelectItem value="Occasional">Occasional</SelectItem>
											<SelectItem value="Probable">Probable</SelectItem>
											<SelectItem value="Frequent">Frequent</SelectItem>
										</SelectContent>
									</Select>
								</div>
							</div>
							<div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-4">
								<div className="space-y-1">
									<Label className="text-xs text-[#878787] font-medium">Monitored Parameter</Label>
									<Input className="bg-[#171717] border-white/10 focus-visible:ring-1 focus-visible:ring-white/20 text-[#ececec]" value={req.parameter} onChange={e => setReq({ ...req, parameter: e.target.value })} />
								</div>
								<div className="space-y-1">
									<Label className="text-xs text-[#878787] font-medium">Safety Limit (Max)</Label>
									<Input className="bg-[#171717] border-white/10 focus-visible:ring-1 focus-visible:ring-white/20 text-[#ececec]" type="number" step="any" value={req.max_value} onChange={e => setReq({ ...req, max_value: e.target.value })} />
								</div>
								<div className="space-y-1">
									<Label className="text-xs text-[#878787] font-medium">Regulation Standard</Label>
									<Input className="bg-[#171717] border-white/10 focus-visible:ring-1 focus-visible:ring-white/20 text-[#ececec]" value={req.standard} onChange={e => setReq({ ...req, standard: e.target.value })} placeholder="ISO 14971" />
								</div>
								<div className="space-y-1">
									<Label className="text-xs text-[#878787] font-medium">Clause REF</Label>
									<Input className="bg-[#171717] border-white/10 focus-visible:ring-1 focus-visible:ring-white/20 text-[#ececec]" value={req.clause} onChange={e => setReq({ ...req, clause: e.target.value })} />
								</div>
							</div>
						</div>
					)}



					<div className="flex items-center justify-between border-t border-white/10 pt-6 mt-6">
						<div className="flex items-center gap-4">
							{msg && (
								<p className={`text-sm font-medium ${msg.type === 'success' ? 'text-emerald-500' : 'text-destructive'}`}>
									{msg.text}
								</p>
							)}
						</div>
						<Button type="submit" disabled={loading} className="gap-2 bg-white text-black hover:bg-white/90">
							{loading ? 'Submitting...' : <><Plus className="h-4 w-4" /> Commit Requirement</>}
						</Button>
					</div>
				</form>
			</div>

			{submittedReqs.length > 0 && (
				<div className="space-y-3">
					<h4 className="text-sm font-semibold text-[#878787] flex items-center gap-2">
						<CheckCircle2 className="h-4 w-4 text-emerald-500" /> Recent Submissions
					</h4>
					<div className="grid gap-2">
						{submittedReqs.map((r, i) => (
							<div key={i} className="p-3 flex items-center justify-between bg-[#171717] hover:bg-[#2f2f2f] transition-colors rounded-xl border border-white/5">
								<div className="flex items-center gap-3">
									<div className="text-xs font-mono font-medium bg-[#2f2f2f] text-[#ececec] px-2 py-1 rounded">
										{r.id}
									</div>
									<span className="text-sm font-medium text-[#ececec]">{r.title}</span>
								</div>
								<span className="text-[10px] text-[#878787] uppercase font-bold tracking-wider">{r.type}</span>
							</div>
						))}
					</div>
				</div>
			)}
		</div>
	)
}

const ActivityCircle = ({ size, className }) => (
	<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
		<path d="M22 12h-4l-3 9L9 3l-3 9H2" />
	</svg>
)

const FileCheck2 = ({ size, className }) => (
	<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
		<path d="M4 22h14a2 2 0 0 0 2-2V7l-5-5H6a2 2 0 0 0-2 2v4" />
		<path d="M14 2v4a2 2 0 0 0 2 2h4" />
		<path d="m9 15 2 2 4-4" />
	</svg>
)
