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
        fidelity: str = "L3"
    ):
        super().__init__(fidelity)
        self.target_flow_rate = target_flow_rate
        self.max_flow_rate = max_flow_rate
        self.max_pressure = max_pressure

        # Tunable mapping / scaling parameters (avoid hidden magic numbers)
        self.noise_amplitude = 0.5
        self.pwm_scale = 4.25
        self.motor_current_scale = 12

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