import math
import random
from ..base import BaseDigitalTwin

class DialysisTwin(BaseDigitalTwin):
    """
    Digital Twin for Class III Hemodialysis Machine.
    Models Blood Flow (peristaltic), Dialysate Flow, and TMP (Transmembrane Pressure).
    """

    def __init__(
        self,
        target_bfr: float = 300.0,  # Blood Flow Rate (mL/min)
        target_dfr: float = 500.0,  # Dialysate Flow Rate (mL/min)
        max_tmp:    float = 400.0,  # Transmembrane Pressure Alarm Limit (mmHg)
        fidelity: str = "L3"
    ):
        super().__init__(fidelity)
        self.target_bfr = target_bfr
        self.target_dfr = target_dfr
        self.max_tmp    = max_tmp

        # Physiological / What-If states
        self.clot_factor = 1.0     # 1.0 = clean filter. >1 = clotting
        self.air_bubble = False    # True = air detected
        self.hypotension = False   # True = patient crash, drop BFR
        
        self.dt = 0.1
        self.safety_trip_tmp = False
        self.safety_trip_air = False

    def step(self) -> dict:
        t = self.time * self.dt
        
        bfr = 0.0
        dfr = 0.0
        tmp = 0.0
        venous_clamp = "OPEN"
        pump_pwm = 0

        # Base targets
        actual_target_bfr = self.target_bfr if not self.hypotension else self.target_bfr * 0.4
        
        if self.fidelity == "L1":
            # Static sine waves 
            bfr = actual_target_bfr + 10.0 * math.sin(t * 2 * math.pi)
            dfr = self.target_dfr
            tmp = 100.0 + 5.0 * math.sin(t * 2 * math.pi)
        else:
            noise = random.uniform(-2.0, 2.0) if self.fidelity == "L3" else 0.0
            
            # Peristaltic pump creates a pulsing wave
            pump_rpm = actual_target_bfr / 5.0  # arbitrary volume per rev
            pulse_freq = (pump_rpm / 60.0) * 2.0 * math.pi
            
            bfr = actual_target_bfr + (20.0 * math.sin(t * pulse_freq)) + noise
            dfr = self.target_dfr + (noise * 0.5)

            # Resistance of filter based on clot factor
            resistance = 0.25 * self.clot_factor
            
            # TMP proportional to BFR pushing through resistance
            tmp = (bfr * resistance) + (dfr * 0.05) + (noise * 2)

            # Safety 1: Air-in-Blood (REQ-DIAL-001)
            if self.air_bubble:
                self.safety_trip_air = True
                bfr = 0.0
                venous_clamp = "CLOSED"
            else:
                self.safety_trip_air = False

            # Safety 2: Max TMP Alarm
            if self.safety_trip_tmp:
                bfr = 0.0
                venous_clamp = "CLOSED"
            elif tmp > self.max_tmp:
                self.safety_trip_tmp = True
                bfr = 0.0
                venous_clamp = "CLOSED"
            else:
                self.safety_trip_tmp = False

        # Telemetry Mapping (Architectural)
        if venous_clamp == "OPEN":
            pump_pwm = max(0, min(255, int((bfr / 500.0) * 255)))
        tmp_sensor_mv = int(tmp * 4.5)

        # State outputs matching Dashboard expectations
        return {
            "BFR": round(bfr, 1),
            "BloodFlowRate(mL/min)": round(bfr, 1),
            "DFR": round(dfr, 1),
            "DialysateFlowRate(mL/min)": round(dfr, 1),
            "TMP": round(tmp, 1),
            "TMP(mmHg)": round(tmp, 1),
            "Pump_PWM": pump_pwm,
            "TMP_mV": tmp_sensor_mv,
            "VenousClamp": venous_clamp,
            "AirAlert": "YES" if self.air_bubble else "NO"
        }

    def apply_fault(self, param: str, bias: float):
        if param.lower() == "clotting":
            self.clot_factor = max(1.0, self.clot_factor * (1 + bias))
        elif param.lower() == "air":
            self.air_bubble = bias > 0
        elif param.lower() == "hypotension":
            self.hypotension = bias > 0
