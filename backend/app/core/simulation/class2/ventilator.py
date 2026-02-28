import math
import random
from ..base import BaseDigitalTwin

class VentilatorTwin(BaseDigitalTwin):
    """
    Digital Twin for Class II Ventilator.
    Supports L1 (Recorded data mapping), L2 (Algorithmic), L3 (First principles).
    """

    def __init__(
        self,
        target_flow_rate: float = 30.0,
        max_flow_rate: float = 60.0,
        max_pressure: float = 40.0,
        fidelity: str = "L3",
        blower_max_rpm: float = None,
        sensor_accuracy: float = None,
        relief_valve_threshold: float = None,
        **kwargs  # Accept additional design specs
    ):
        super().__init__(fidelity)
        self.target_flow_rate = target_flow_rate
        self.max_flow_rate = max_flow_rate
        
        # Use design-driven specs if available, otherwise use defaults
        self.max_pressure = relief_valve_threshold if relief_valve_threshold else max_pressure
        self.blower_rpm = blower_max_rpm if blower_max_rpm else 60000  # Default 60k RPM
        self.sensor_noise = sensor_accuracy if sensor_accuracy else 0.03  # Default 3%

        # Calculate scaling factors from actual component specs (not hardcoded!)
        # PWM scale factor derived from blower RPM: 255 PWM at max flow
        self.pwm_scale = (255.0 / self.max_flow_rate) if self.max_flow_rate > 0 else 4.25
        # Motor current from blower power: typical BLDC ~12mA per PWM unit
        self.motor_current_scale = 12  # mA per PWM unit
        
        # Noise amplitude from sensor accuracy
        self.noise_amplitude = self.sensor_noise * self.max_flow_rate  # Absolute noise in L/min

        # Physiological variables (What-If analysis)
        self.RR = 15.0               # Respiration Rate (breaths/min)
        self.I_E_ratio = 1.0 / 2.0   # 1:2
        self.Vt = 500.0              # Tidal Volume (mL)
        self.compliance = 50.0       # Lung Compliance (mL/cmH2O)
        self.resistance = 5.0        # Airway Resistance (cmH2O/L/s)
        self.peep = 5.0              # Positive End-Expiratory Pressure
        
        # State
        self.dt = 0.1  # 100ms per step
        self.safety_trip = False

    def step(self) -> dict:
        t = self.time * self.dt
        
        breath_duration = 60.0 / self.RR
        t_in_breath = t % breath_duration
        
        t_insp = breath_duration * (self.I_E_ratio / (1.0 + self.I_E_ratio))
        t_exp  = breath_duration - t_insp
        tau = self.resistance * (self.compliance / 1000.0) # seconds

        # Baseline
        flow_lpm = 0.0
        pressure = self.peep
        volume_ml = 0.0
        relief_valve = "CLOSED"

        # L1: Recorded / Static baseline wave
        if self.fidelity == "L1":
            flow_lpm = 30.0 * math.sin(math.pi * t_in_breath / t_insp) if t_in_breath < t_insp else -30.0 * math.sin(math.pi * (t_in_breath - t_insp) / t_exp)
            pressure = self.peep + 15.0 * math.sin(math.pi * t_in_breath / t_insp) if t_in_breath < t_insp else self.peep
            volume_ml = 250.0 * (1 - math.cos(math.pi * t_in_breath / t_insp)) if t_in_breath < t_insp else 500.0 * math.exp(-(t_in_breath - t_insp)/0.5)
        
        # L2 & L3: Physics Models (L3 adds noise for realism)
        else:
            noise = random.uniform(-self.noise_amplitude, self.noise_amplitude) if self.fidelity == "L3" else 0.0
            
            if t_in_breath < t_insp:
                # Inspiration phase (constant flow volume control)
                flow_lps = (self.Vt / 1000.0) / t_insp
                flow_lpm = (flow_lps * 60.0) + noise
                volume_ml = (flow_lps * t_in_breath) * 1000.0
                pressure = (flow_lps * self.resistance) + (volume_ml / self.compliance) + self.peep + noise
                
                # ISO 14971 Safety Check
                if self.safety_trip:
                    flow_lpm = 0.0
                    pressure = self.peep
                    relief_valve = "OPEN"
                elif pressure > self.max_pressure:
                    self.safety_trip = True  # Pop-off valve engages
                    flow_lpm = 0.0
                    pressure = self.peep
                    relief_valve = "OPEN"
            else:
                # Expiration phase (passive decay)
                self.safety_trip = False # Reset
                t_e = t_in_breath - t_insp
                volume_ml = self.Vt * math.exp(-t_e / max(0.01, tau))
                flow_lps = -(volume_ml / 1000.0) / max(0.01, tau)
                flow_lpm = (flow_lps * 60.0) + noise
                pressure = (volume_ml / self.compliance) + self.peep + noise

        # Electrical / Architectural mapped telemetry
        blower_pwm = max(0, min(255, int(flow_lpm * self.pwm_scale) if flow_lpm > 0 else 0))
        motor_current_ma = blower_pwm * self.motor_current_scale
        sensor_hex = hex(int(abs(flow_lpm * 100)) & 0xFFFF).upper()

        return {
            "Pressure": round(pressure, 2),
            "Pressure(cmH2O)": round(pressure, 2),
            "Flow": round(flow_lpm, 2),
            "Flow(L/min)": round(flow_lpm, 2),
            "Volume": round(volume_ml, 2),
            "Blower_PWM": blower_pwm,
            "Motor_mA": motor_current_ma,
            "ReliefValve": relief_valve,
            "Proximal_I2C": sensor_hex
        }

    # What-If Triggers mapped from UI
    def apply_fault(self, param: str, bias: float):
        if param.lower() == "compliance":
            self.compliance = max(5.0, self.compliance * (1 + bias))
        elif param.lower() == "resistance":
            self.resistance = max(1.0, self.resistance * (1 + bias))
        elif param.lower() == "rate":
            self.RR = max(5.0, self.RR * (1 + bias))