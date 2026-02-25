// HardwareTwinConfig.js — Layer-2 Electronics Block Configs for Class I / II / III

// ─── Shared constants ──────────────────────────────────────────────────────
// Power domain color palette
export const POWER_COLORS = {
    VCC_3V3: '#22d3ee',   // cyan   — logic rail
    VCC_5V: '#a78bfa',   // violet — analog rail
    VCC_12V: '#f59e0b',   // amber  — actuator rail
    VCC_24V: '#ef4444',   // red    — high-power rail
    VBAT: '#34d399',   // green  — backup battery
    GND: '#374151',   // gray
};

// Bus color palette
export const BUS_COLORS = {
    SPI: '#38bdf8',
    I2C: '#a78bfa',
    UART: '#34d399',
    PWM: '#f59e0b',
    ANALOG: '#fb923c',
    DIGITAL: '#e2e8f0',
    INTERLOCK: '#ef4444',
    EMERGENCY: '#dc2626',
};

// ─── Class I — Pulse Oximeter ─────────────────────────────────────────────

const pulseOximeterHW = {
    label: 'Pulse Oximeter — Electronics Twin',
    classLabel: 'Class I',
    designVersion: '1.2',
    description: 'Single-supply, signal-integrity focused. MCU drives LED burst, reads ADC, computes SpO₂ via R-ratio lookup.',

    powerDomains: [
        { id: 'vcc_3v3', label: '3.3V Logic', color: POWER_COLORS.VCC_3V3, y: 30, x: 40, w: 700, h: 16, opacity: 0.12 },
        { id: 'vcc_5v', label: '5V Analog', color: POWER_COLORS.VCC_5V, y: 52, x: 40, w: 700, h: 16, opacity: 0.10 },
    ],

    blocks: [
        {
            id: 'power', label: 'Power Supply', sublabel: 'Li-Po · LDO Reg.',
            x: 40, y: 100, w: 110, h: 60,
            icon: '⚡', domain: 'VCC_3V3', layer1Component: null,
            ports: [{ id: 'out_3v3', side: 'right', y: 0.5 }],
        },
        {
            id: 'mcu', label: 'MCU', sublabel: 'ARM Cortex-M0+',
            x: 220, y: 85, w: 130, h: 90,
            icon: '⬛', domain: 'VCC_3V3', layer1Component: 'R-Ratio Calc',
            ports: [
                { id: 'in_pwr', side: 'left', y: 0.3 },
                { id: 'out_spi', side: 'left', y: 0.6 },
                { id: 'in_adc', side: 'right', y: 0.35 },
                { id: 'out_alarm', side: 'right', y: 0.7 },
            ],
        },
        {
            id: 'led_drv', label: 'LED Driver', sublabel: 'Red 660nm · IR 940nm',
            x: 40, y: 220, w: 110, h: 60,
            icon: '💡', domain: 'VCC_5V', layer1Component: 'LED Driver',
            ports: [{ id: 'in_spi', side: 'right', y: 0.5 }],
        },
        {
            id: 'adc', label: 'Photodiode ADC', sublabel: '24-bit ΔΣ · PGA',
            x: 430, y: 85, w: 120, h: 60,
            icon: '📡', domain: 'VCC_5V', layer1Component: 'Photodetector',
            ports: [
                { id: 'in_signal', side: 'left', y: 0.5 },
                { id: 'out_data', side: 'right', y: 0.5 },
            ],
        },
        {
            id: 'alarm', label: 'Alarm Output', sublabel: 'Buzzer · LED Badge',
            x: 620, y: 100, w: 110, h: 50,
            icon: '🔔', domain: 'VCC_3V3', layer1Component: 'Alarm Logic',
            ports: [{ id: 'in_sig', side: 'left', y: 0.5 }],
        },
    ],

    buses: [
        { id: 'b1', type: 'SPI', label: 'SPI · 1MHz', fromBlock: 'mcu', fromPort: 'out_spi', toBlock: 'led_drv', toPort: 'in_spi', x1: 220, y1: 137, x2: 150, y2: 250 },
        { id: 'b2', type: 'ANALOG', label: 'Diff Signal', fromBlock: 'adc', fromPort: 'in_signal', toBlock: 'led_drv', toPort: null, x1: 430, y1: 110, x2: 150, y2: 240, curved: true },
        { id: 'b3', type: 'SPI', label: 'SPI · Data', fromBlock: 'adc', fromPort: 'out_data', toBlock: 'mcu', toPort: 'in_adc', x1: 550, y1: 115, x2: 350, y2: 120 },
        { id: 'b4', type: 'DIGITAL', label: 'Alarm Out', fromBlock: 'mcu', fromPort: 'out_alarm', toBlock: 'alarm', toPort: 'in_sig', x1: 350, y1: 155, x2: 620, y2: 125 },
        { id: 'b5', type: 'I2C', label: '3.3V Rail', fromBlock: 'power', fromPort: 'out_3v3', toBlock: 'mcu', toPort: 'in_pwr', x1: 150, y1: 130, x2: 220, y2: 112 },
    ],

    faultMatrix: [
        { label: 'LED Power-off', type: 'power', target: 'led_drv', color: 'red', param: 'compliance', bias: -0.9 },
        { label: 'ADC SPI Timeout', type: 'bus', target: 'adc', color: 'amber', param: 'resistance', bias: 1.2 },
        { label: 'Supply Brownout', type: 'power', target: 'power', color: 'red', param: 'leak', bias: 0.8 },
    ],
};

// ─── Class II — Ventilator ────────────────────────────────────────────────

const ventilatorHW = {
    label: 'Mechanical Ventilator — Electronics Twin',
    classLabel: 'Class II',
    designVersion: '2.1',
    description: 'Dual-supply architecture. MCU runs closed-loop PID at 100Hz. Motor driver executes PWM commands. Safety watchdog operates independently.',

    powerDomains: [
        { id: 'primary', label: '24V Primary', color: POWER_COLORS.VCC_24V, y: 25, x: 30, w: 730, h: 18, opacity: 0.10 },
        { id: 'logic', label: '5V Logic', color: POWER_COLORS.VCC_5V, y: 50, x: 30, w: 730, h: 14, opacity: 0.10 },
        { id: 'backup', label: '12V Backup', color: POWER_COLORS.VBAT, y: 70, x: 30, w: 730, h: 10, opacity: 0.08 },
    ],

    blocks: [
        {
            id: 'psu', label: 'Power Unit', sublabel: 'AC→DC + UPS',
            x: 30, y: 110, w: 110, h: 70,
            icon: '⚡', domain: 'VCC_24V', layer1Component: null,
            ports: [{ id: 'out24', side: 'right', y: 0.35 }, { id: 'out5', side: 'right', y: 0.65 }],
        },
        {
            id: 'safety_wd', label: 'Safety WD', sublabel: 'SIL-2 Watchdog',
            x: 200, y: 95, w: 110, h: 50,
            icon: '🛡', domain: 'VCC_5V', layer1Component: 'Relief Valve',
            ports: [{ id: 'in_hb', side: 'left', y: 0.5 }, { id: 'out_cut', side: 'right', y: 0.5 }],
        },
        {
            id: 'mcu', label: 'Control MCU', sublabel: 'Cortex-M4 · 100MHz',
            x: 200, y: 185, w: 130, h: 90,
            icon: '⬛', domain: 'VCC_5V', layer1Component: 'P–Control',
            ports: [
                { id: 'in_pwr', side: 'left', y: 0.25 },
                { id: 'out_pwm', side: 'right', y: 0.3 },
                { id: 'in_p', side: 'right', y: 0.55 },
                { id: 'in_f', side: 'right', y: 0.75 },
                { id: 'out_hb', side: 'left', y: 0.75 },
            ],
        },
        {
            id: 'mdr', label: 'Motor Driver', sublabel: 'H-Bridge · 24V/5A',
            x: 400, y: 110, w: 120, h: 60,
            icon: '⚙', domain: 'VCC_24V', layer1Component: 'Blower Motor',
            ports: [{ id: 'in_pwm', side: 'left', y: 0.5 }, { id: 'out_mtr', side: 'right', y: 0.5 }],
        },
        {
            id: 'psens', label: 'Pressure IF', sublabel: 'I²C · 16-bit',
            x: 400, y: 210, w: 120, h: 55,
            icon: '📊', domain: 'VCC_5V', layer1Component: 'Pressure Sensor',
            ports: [{ id: 'out_data', side: 'left', y: 0.5 }],
        },
        {
            id: 'fsens', label: 'Flow Sensor IF', sublabel: 'SPI · Diff. Mass Flow',
            x: 400, y: 290, w: 120, h: 55,
            icon: '🌊', domain: 'VCC_5V', layer1Component: 'Flow Sensor',
            ports: [{ id: 'out_data', side: 'left', y: 0.5 }],
        },
        {
            id: 'motor', label: 'Blower Motor', sublabel: 'BLDC · 0–6000 RPM',
            x: 590, y: 110, w: 110, h: 60,
            icon: '🔄', domain: 'VCC_24V', layer1Component: 'Blower Motor',
            ports: [{ id: 'in_drv', side: 'left', y: 0.5 }],
        },
    ],

    buses: [
        { id: 'b1', type: 'PWM', label: 'PWM 20kHz', x1: 330, y1: 247, x2: 400, y2: 140 },
        { id: 'b2', type: 'I2C', label: 'I²C · P data', x1: 400, y1: 237, x2: 330, y2: 248 },
        { id: 'b3', type: 'SPI', label: 'SPI · F data', x1: 400, y1: 317, x2: 330, y2: 262 },
        { id: 'b4', type: 'DIGITAL', label: 'Motor Drive', x1: 520, y1: 140, x2: 590, y2: 140 },
        { id: 'b5', type: 'INTERLOCK', label: 'Cut-off', x1: 310, y1: 120, x2: 400, y2: 140, dashed: true },
    ],

    faultMatrix: [
        { label: 'Motor Driver Fail', type: 'power', target: 'mdr', color: 'red', param: 'compliance', bias: -0.9 },
        { label: 'Primary Power Loss', type: 'power', target: 'psu', color: 'red', param: 'leak', bias: 0.9 },
        { label: 'Watchdog Timeout', type: 'timing', target: 'safety_wd', color: 'red', param: 'clog', bias: 1.0 },
        { label: 'Sensor I²C Glitch', type: 'bus', target: 'psens', color: 'amber', param: 'resistance', bias: 0.8 },
    ],
};

// ─── Class III — Hemodialysis ─────────────────────────────────────────────

const hemodialysisHW = {
    label: 'Hemodialysis System — Electronics Twin',
    classLabel: 'Class III',
    designVersion: '3.0',
    description: 'Life-critical dual-controller architecture. Control MCU and Safety MCU are hardware-separated. Three power domains with active redundancy. Emergency clamp engages within <10ms on any safety trip.',

    powerDomains: [
        { id: 'primary', label: '24V Primary', color: POWER_COLORS.VCC_24V, y: 20, x: 20, w: 750, h: 16, opacity: 0.09 },
        { id: 'backup', label: '12V UPS Backup', color: POWER_COLORS.VBAT, y: 40, x: 20, w: 750, h: 14, opacity: 0.09 },
        { id: 'logic', label: '5V Logic (Iso)', color: POWER_COLORS.VCC_5V, y: 58, x: 20, w: 750, h: 12, opacity: 0.09 },
        { id: 'blood_iso', label: 'Blood Iso Rail', color: '#ef4444', y: 74, x: 20, w: 360, h: 10, opacity: 0.06 },
        { id: 'dial_iso', label: 'Dialysate Rail', color: '#38bdf8', y: 74, x: 400, w: 370, h: 10, opacity: 0.06 },
    ],

    blocks: [
        {
            id: 'psu', label: 'Power Unit', sublabel: 'AC/DC + 3-rail UPS',
            x: 20, y: 105, w: 110, h: 80,
            icon: '⚡', domain: 'VCC_24V', layer1Component: null,
            ports: [{ id: 'out_main', side: 'right', y: 0.4 }, { id: 'out_bkp', side: 'right', y: 0.7 }],
        },
        {
            id: 'ctrl_mcu', label: 'Control MCU', sublabel: 'Cortex-M7 · 216MHz',
            x: 180, y: 105, w: 130, h: 80,
            icon: '⬛', domain: 'VCC_5V', layer1Component: 'Conductivity',
            ports: [
                { id: 'in_pwr', side: 'left', y: 0.3 },
                { id: 'out_bp', side: 'right', y: 0.25 },
                { id: 'out_dp', side: 'right', y: 0.5 },
                { id: 'in_sens', side: 'right', y: 0.75 },
                { id: 'out_hb', side: 'left', y: 0.75 },
            ],
        },
        {
            id: 'safe_mcu', label: 'Safety MCU', sublabel: 'SIL-3 · Lockstep',
            x: 180, y: 230, w: 130, h: 70,
            icon: '🛡', domain: 'VCC_5V', layer1Component: 'Air Detector',
            ports: [
                { id: 'in_hb', side: 'left', y: 0.4 },
                { id: 'out_clamp', side: 'right', y: 0.35 },
                { id: 'out_alarm', side: 'right', y: 0.65 },
            ],
        },
        {
            id: 'blood_drv', label: 'Blood Pump Drv', sublabel: 'Peristaltic · 24V',
            x: 380, y: 100, w: 120, h: 55,
            icon: '🩸', domain: 'VCC_24V', layer1Component: 'Peristaltic Pump',
            ports: [{ id: 'in_cmd', side: 'left', y: 0.5 }, { id: 'out_mtr', side: 'right', y: 0.5 }],
        },
        {
            id: 'dial_drv', label: 'Dialysate Drv', sublabel: 'Centrifugal · 24V',
            x: 380, y: 185, w: 120, h: 55,
            icon: '💧', domain: 'VCC_24V', layer1Component: 'UF Control',
            ports: [{ id: 'in_cmd', side: 'left', y: 0.5 }, { id: 'out_mtr', side: 'right', y: 0.5 }],
        },
        {
            id: 'air_det', label: 'Air Detector', sublabel: 'Ultrasonic · 1MHz',
            x: 380, y: 265, w: 120, h: 45,
            icon: '🫧', domain: 'VCC_5V', layer1Component: 'Air Detector',
            ports: [{ id: 'out_flag', side: 'left', y: 0.5 }],
        },
        {
            id: 'tmp_sens', label: 'TMP Sensor IF', sublabel: 'Diff. Pressure · I²C',
            x: 380, y: 330, w: 120, h: 45,
            icon: '📊', domain: 'VCC_5V', layer1Component: 'Membrane',
            ports: [{ id: 'out_data', side: 'left', y: 0.5 }],
        },
        {
            id: 'clamp', label: 'Emergency Clamp', sublabel: 'Arterial Line · <10ms',
            x: 570, y: 240, w: 120, h: 50,
            icon: '🚨', domain: 'VCC_24V', layer1Component: 'Leak Detector',
            ports: [{ id: 'in_en', side: 'left', y: 0.5 }],
        },
        {
            id: 'alarm_out', label: 'Alarm Panel', sublabel: 'Visual + Audible',
            x: 570, y: 305, w: 120, h: 50,
            icon: '🔔', domain: 'VCC_5V', layer1Component: 'Leak Detector',
            ports: [{ id: 'in_sig', side: 'left', y: 0.5 }],
        },
    ],

    buses: [
        { id: 'b1', type: 'PWM', label: 'Blood PWM', x1: 310, y1: 133, x2: 380, y2: 128 },
        { id: 'b2', type: 'PWM', label: 'Dialysate PWM', x1: 310, y1: 158, x2: 380, y2: 212 },
        { id: 'b3', type: 'I2C', label: 'Air Flag', x1: 380, y1: 287, x2: 310, y2: 170 },
        { id: 'b4', type: 'I2C', label: 'TMP Data', x1: 380, y1: 352, x2: 310, y2: 175 },
        { id: 'b5', type: 'INTERLOCK', label: 'HB Signal', x1: 310, y1: 248, x2: 180, y2: 115, dashed: true },
        { id: 'b6', type: 'EMERGENCY', label: 'CLAMP EN', x1: 310, y1: 262, x2: 570, y2: 265, dashed: true },
        { id: 'b7', type: 'EMERGENCY', label: 'ALARM', x1: 310, y1: 275, x2: 570, y2: 330, dashed: true },
    ],

    faultMatrix: [
        { label: 'Primary Power Loss', type: 'power', target: 'psu', color: 'red', param: 'leak', bias: 0.9 },
        { label: 'Blood Pump Fail', type: 'power', target: 'blood_drv', color: 'red', param: 'compliance', bias: -0.9 },
        { label: 'Air Detector Alarm', type: 'sensor', target: 'air_det', color: 'red', param: 'clog', bias: 1.0 },
        { label: 'Safety MCU Timeout', type: 'timing', target: 'safe_mcu', color: 'red', param: 'clog', bias: 1.0 },
        { label: 'Hi TMP / Clot', type: 'sensor', target: 'tmp_sens', color: 'amber', param: 'resistance', bias: 1.5 },
        { label: 'Dialysate Pump Fault', type: 'power', target: 'dial_drv', color: 'amber', param: 'compliance', bias: -0.5 },
    ],
};

// ─── Export ───────────────────────────────────────────────────────────────

export const HW_CONFIGS = {
    pulse_oximeter: pulseOximeterHW,
    ventilator: ventilatorHW,
    dialysis: hemodialysisHW,
};
