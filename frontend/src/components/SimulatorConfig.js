// SimulatorConfig.js — Device-specific configs for Class I, II, III simulators

export const DEVICE_CONFIGS = {
    pulse_oximeter: {
        label: 'Pulse Oximeter',
        classLabel: 'Class I',
        designVersion: '1.2',
        signals: [
            { key: 'SpO2', label: 'SpO₂', unit: '%', color: '#22d3ee', domain: [85, 100] },
            { key: 'HeartRate', label: 'Heart Rate', unit: 'bpm', color: '#a78bfa', domain: [40, 160] },
            { key: 'Perfusion', label: 'Perf. Index', unit: '%', color: '#34d399', domain: [0, 20] },
        ],
        subsystems: [
            { id: 'sensing', label: 'Optical Sensing', x: 80, y: 180, w: 130, h: 55, components: ['LED Driver', 'Photodetector'] },
            { id: 'signal', label: 'Signal Proc.', x: 280, y: 180, w: 130, h: 55, components: ['ADC', 'DSP Filter'] },
            { id: 'pid', label: 'SpO₂ Algorithm', x: 480, y: 180, w: 130, h: 55, components: ['R-Ratio Calc', 'SpO₂ Lookup'] },
            { id: 'safety', label: 'Alarm Monitor', x: 280, y: 80, w: 130, h: 45, components: ['Alarm Logic'] },
        ],
        links: [
            { from: 'sensing', to: 'signal', label: 'Raw AC/DC', x1: 210, y1: 208, x2: 280, y2: 208 },
            { from: 'signal', to: 'pid', label: 'Filtered', x1: 410, y1: 208, x2: 480, y2: 208 },
            { from: 'safety', to: 'pid', label: 'Override', x1: 345, y1: 125, x2: 345, y2: 180, dashed: true },
        ],
        faultMatrix: [
            { label: 'LED Failure', param: 'compliance', bias: -0.9, color: 'red' },
            { label: 'Low Perfusion', param: 'leak', bias: 0.4, color: 'amber' },
            { label: 'Motion Artifact', param: 'resistance', bias: 1.2, color: 'amber' },
            { label: 'Sensor Dropout', param: 'clog', bias: 1.0, color: 'red' },
        ],
        safetyRules: [
            { rule: 'Low SpO₂ Alarm', param: 'SpO2', threshold: '< 90%', iso: 'ISO 80601-2-61 §6.8.2' },
            { rule: 'Extreme Low SpO₂', param: 'SpO2', threshold: '< 85%', iso: 'ISO 80601-2-61 §6.8.3' },
            { rule: 'Tachycardia Alarm', param: 'HeartRate', threshold: '> 130 bpm', iso: 'IEC 60601-1-8 §6.3' },
        ],
        scenarios: [
            { name: 'Baseline', params: {} },
            { name: 'Low Perfusion', params: { param: 'leak', bias: 0.35 } },
            { name: 'Motion Artifact', params: { param: 'resistance', bias: 1.2 } },
        ],
    },

    ventilator: {
        label: 'Mechanical Ventilator',
        classLabel: 'Class II',
        designVersion: '2.1',
        signals: [
            { key: 'Pressure', label: 'Airway Pressure', unit: 'cmH₂O', color: '#38bdf8', domain: [0, 40] },
            { key: 'Flow', label: 'Flow Rate', unit: 'L/min', color: '#a78bfa', domain: [-60, 60] },
            { key: 'Volume', label: 'Tidal Volume', unit: 'mL', color: '#34d399', domain: [0, 700] },
        ],
        subsystems: [
            { id: 'pneumatics', label: 'Pneumatics', x: 60, y: 180, w: 130, h: 55, components: ['Blower Motor', 'Flow Valve'] },
            { id: 'sensors', label: 'Sensors', x: 260, y: 180, w: 130, h: 55, components: ['Pressure Sensor', 'Flow Sensor'] },
            { id: 'pid', label: 'PID Controller', x: 460, y: 180, w: 130, h: 55, components: ['O₂ Mixer', 'P–Control'] },
            { id: 'safety', label: 'Safety Monitor', x: 260, y: 70, w: 130, h: 45, components: ['Relief Valve', 'Alarm'] },
            { id: 'patient', label: 'Patient Model', x: 660, y: 180, w: 110, h: 55, components: ['Lung Model'] },
        ],
        links: [
            { from: 'pneumatics', to: 'sensors', label: 'Delivered Gas', x1: 190, y1: 208, x2: 260, y2: 208 },
            { from: 'sensors', to: 'pid', label: 'P/F Feedback', x1: 390, y1: 208, x2: 460, y2: 208 },
            { from: 'pid', to: 'patient', label: 'Drive Signal', x1: 590, y1: 208, x2: 660, y2: 208 },
            { from: 'safety', to: 'pid', label: 'Override', x1: 325, y1: 115, x2: 325, y2: 180, dashed: true },
        ],
        faultMatrix: [
            { label: 'Circuit Leak (400 mL/min)', param: 'leak', bias: 0.4, color: 'red' },
            { label: 'Acute Lung Stiffness', param: 'compliance', bias: -0.6, color: 'red' },
            { label: 'HME Filter Occlusion', param: 'clog', bias: 1.0, color: 'red' },
            { label: 'Sensor Noise (+5%)', param: 'resistance', bias: 0.3, color: 'amber' },
        ],
        safetyRules: [
            { rule: 'High Pressure Alarm', param: 'Pressure', threshold: '> 35 cmH₂O', iso: 'ISO 80601-2-12 §51.3' },
            { rule: 'Low Minute Volume', param: 'Flow', threshold: '< 2 L/min', iso: 'ISO 80601-2-12 §51.4' },
            { rule: 'Relief Valve Deployed', param: 'Pressure', threshold: '> 40 cmH₂O', iso: 'ISO 80601-2-12 §201.12' },
        ],
        scenarios: [
            { name: 'Baseline (Healthy)', params: {} },
            { name: 'Compliance −40%', params: { param: 'compliance', bias: -0.4 } },
            { name: 'Airway Occlusion', params: { param: 'clog', bias: 0.8 } },
            { name: 'ARDS Model', params: { param: 'compliance', bias: -0.7 } },
        ],
    },

    dialysis: {
        label: 'Hemodialysis System',
        classLabel: 'Class III',
        designVersion: '3.0',
        signals: [
            { key: 'BFR', label: 'Blood Flow Rate', unit: 'mL/min', color: '#ef4444', domain: [0, 400] },
            { key: 'DFR', label: 'Dialysate Flow', unit: 'mL/min', color: '#38bdf8', domain: [0, 800] },
            { key: 'TMP', label: 'Trans-Membrane P.', unit: 'mmHg', color: '#f59e0b', domain: [-200, 400] },
        ],
        subsystems: [
            { id: 'blood', label: 'Blood Pump', x: 60, y: 180, w: 120, h: 55, components: ['Peristaltic Pump', 'Heparin'] },
            { id: 'dialyzer', label: 'Dialyzer', x: 250, y: 180, w: 120, h: 55, components: ['Membrane', 'UF Control'] },
            { id: 'dialysate', label: 'Dialysate Circuit', x: 440, y: 180, w: 130, h: 55, components: ['Conductivity', 'Temp Control'] },
            { id: 'safety', label: 'Safety Systems', x: 250, y: 70, w: 120, h: 45, components: ['Air Detector', 'Leak Detector'] },
            { id: 'monitor', label: 'Patient Monitor', x: 640, y: 180, w: 110, h: 55, components: ['BP Monitor', 'Weight Scale'] },
        ],
        links: [
            { from: 'blood', to: 'dialyzer', label: 'Blood In/Out', x1: 180, y1: 208, x2: 250, y2: 208 },
            { from: 'dialyzer', to: 'dialysate', label: 'Dialysate', x1: 370, y1: 208, x2: 440, y2: 208 },
            { from: 'dialysate', to: 'monitor', label: 'Vitals', x1: 570, y1: 208, x2: 640, y2: 208 },
            { from: 'safety', to: 'blood', label: 'Emergency Stop', x1: 250, y1: 93, x2: 120, y2: 93, dashed: true },
        ],
        faultMatrix: [
            { label: 'Air Embolism Risk', param: 'leak', bias: 0.8, color: 'red' },
            { label: 'High TMP', param: 'resistance', bias: 1.5, color: 'red' },
            { label: 'Membrane Clotting', param: 'clog', bias: 0.7, color: 'amber' },
            { label: 'Conductivity Alarm', param: 'compliance', bias: -0.5, color: 'amber' },
        ],
        safetyRules: [
            { rule: 'Air Detector Alarm', param: 'BFR', threshold: 'Air detected', iso: 'ISO 23328-1 §5.4' },
            { rule: 'High TMP Alarm', param: 'TMP', threshold: '> 300 mmHg', iso: 'ISO 8637-1 §5.3' },
            { rule: 'Blood Leak Detected', param: 'DFR', threshold: 'Leak flag = TRUE', iso: 'ISO 23328-1 §5.7' },
        ],
        scenarios: [
            { name: 'Baseline', params: {} },
            { name: 'High BFR (400 mL/min)', params: { param: 'resistance', bias: 0.5 } },
            { name: 'Membrane Fouling', params: { param: 'clog', bias: 0.6 } },
        ],
    },
};

export const FIDELITY_DESCRIPTIONS = {
    L1: 'Functional behavior only — steady-state signals, no fault propagation',
    L2: 'Control + timing — dynamic waveforms, control loop visible',
    L3: 'Full fault & safety — fault propagation, safety rule evaluation, ISO compliance checks',
};

export const FIDELITY_FAULT_LOCK = {
    L1: false,  // faults disabled at L1
    L2: false,
    L3: true,   // full fault injection at L3
};
