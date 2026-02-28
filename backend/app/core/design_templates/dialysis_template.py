"""
Hemodialysis Machine Design Template - IEC 60601-2-16 compliant (NO LLM)
Based on IEC 60601-2-16:2018 Hemodialysis equipment
"""
from typing import List
from .base_template import (
    DesignTemplate, Subsystem, ComponentSpec, DesignRequirements
)


class DialysisTemplate(DesignTemplate):
    """Template for hemodialysis machine design"""
    
    def __init__(self):
        super().__init__(device_type="hemodialysis", device_class="Class III")
    
    def define_subsystems(self, requirements: DesignRequirements) -> List[Subsystem]:
        """
        Define hemodialysis subsystems per IEC 62304 §5.3
        """
        return [
            Subsystem(
                id="blood_circuit",
                name="Extracorporeal Blood Circuit",
                description="Blood pump and monitoring for patient blood circulation",
                iec_62304_section="§5.3.1 - Blood Circuit Architecture",
                iso_14971_hazards=[
                    "H001: Air embolism",
                    "H002: Blood leak",
                    "H003: Hemolysis from pump"
                ],
                required_components=["blood_pump", "air_detector", "blood_leak_detector", "pressure_sensor"],
                interfaces=["dialysate_circuit", "safety_system", "main_control"],
                safety_requirements=[
                    "SR001: Air detection <0.3ml",
                    "SR002: Blood leak detection <0.5ml/min",
                    "SR003: Occlusion detection within 30s"
                ],
                test_requirements=[
                    "TR001: Air detection sensitivity test",
                    "TR002: Pump flow accuracy ±5%",
                    "TR003: Hemolysis test per ISO 10993"
                ]
            ),
            
            Subsystem(
                id="dialysate_circuit",
                name="Dialysate Preparation and Delivery",
                description="Dialysate mixing, heating, and circulation system",
                iec_62304_section="§5.3.2 - Dialysate System Design",
                iso_14971_hazards=[
                    "H004: Incorrect conductivity causing hypo/hypernatremia",
                    "H005: Temperature too high causing burns",
                    "H006: Bacterial contamination"
                ],
                required_components=["dialysate_pump", "heater", "conductivity_sensor", "temperature_sensor", "uv_disinfection"],
                interfaces=["blood_circuit", "water_treatment", "main_control"],
                safety_requirements=[
                    "SR004: Temperature range 35-39°C ±0.5°C",
                    "SR005: Conductivity monitoring ±0.5mS/cm",
                    "SR006: Endotoxin level <0.25 EU/ml"
                ],
                test_requirements=[
                    "TR004: Temperature accuracy test",
                    "TR005: Conductivity calibration",
                    "TR006: Bacterial filtration efficiency"
                ]
            ),
            
            Subsystem(
                id="ultrafiltration",
                name="Ultrafiltration Control",
                description="Fluid removal control and monitoring",
                iec_62304_section="§5.3.3 - Ultrafiltration System",
                iso_14971_hazards=[
                    "H007: Excessive fluid removal causing hypotension",
                    "H008: Inadequate ultrafiltration",
                    "H009: Pressure imbalance"
                ],
                required_components=["pressure_transducers", "balance_chamber", "uf_pump", "weight_scale"],
                interfaces=["blood_circuit", "dialysate_circuit", "main_control"],
                safety_requirements=[
                    "SR007: UF rate accuracy ±10ml/h",
                    "SR008: Total UF volume accuracy ±100ml",
                    "SR009: TMP alarm limits"
                ],
                test_requirements=[
                    "TR007: Volumetric accuracy test",
                    "TR008: Pressure monitoring accuracy",
                    "TR009: Balance chamber integrity test"
                ]
            )
        ]
    
    def specify_components(self, subsystem: Subsystem, requirements: DesignRequirements) -> List[ComponentSpec]:
        """
        Specify components for dialysis subsystems
        """
        specs_map = {
            "blood_circuit": [
                ComponentSpec(
                    category="blood_pump",
                    description="Peristaltic blood pump",
                    required_specs={
                        "type": "peristaltic",
                        "flow_rate_ml_min": 600,
                        "accuracy_percent": 5.0,
                        "tubing_compatibility": "standard_bloodline",
                        "motor_type": "brushless_dc"
                    },
                    safety_critical=True,
                    medical_grade_required=True,
                    certifications_required=["IEC 60601-2-16", "ISO 10993"]
                ),
                ComponentSpec(
                    category="air_detector",
                    description="Ultrasonic air bubble detector",
                    required_specs={
                        "type": "ultrasonic",
                        "sensitivity_ml": 0.3,
                        "response_time_ms": 100,
                        "false_alarm_rate": 0.01
                    },
                    safety_critical=True,
                    medical_grade_required=True
                )
            ],
            
            "dialysate_circuit": [
                ComponentSpec(
                    category="heater",
                    description="Dialysate heater with PID control",
                    required_specs={
                        "power_w": 500,
                        "temperature_range_c": [35, 39],
                        "accuracy_c": 0.5,
                        "control_type": "PID"
                    },
                    safety_critical=True,
                    medical_grade_required=True
                ),
                ComponentSpec(
                    category="conductivity_sensor",
                    description="Inline conductivity measurement",
                    required_specs={
                        "range_ms_cm": [12, 16],
                        "accuracy_ms_cm": 0.5,
                        "temperature_compensation": True,
                        "interface": "4-20mA"
                    },
                    safety_critical=True,
                    medical_grade_required=True
                )
            ],
            
            "ultrafiltration": [
                ComponentSpec(
                    category="pressure_transducers",
                    description="Pressure monitoring sensors",
                    required_specs={
                        "type": "differential",
                        "range_mmhg": 500,
                        "accuracy_percent": 2.0,
                        "output": "analog"
                    },
                    safety_critical=True,
                    medical_grade_required=True
                )
            ]
        }
        
        return specs_map.get(subsystem.id, [])
