"""
Ventilator Design Template - IEC 60601-2-12 compliant (NO LLM)
Based on ISO 80601-2-12:2020 Ventilatory support equipment
"""
from typing import List
from .base_template import (
    DesignTemplate, Subsystem, ComponentSpec, DesignRequirements
)


class VentilatorTemplate(DesignTemplate):
    """Template for mechanical ventilator design"""
    
    def __init__(self):
        super().__init__(device_type="ventilator", device_class="Class II")
    
    def define_subsystems(self, requirements: DesignRequirements) -> List[Subsystem]:
        """
        Define ventilator subsystems per IEC 62304 §5.3
        """
        return [
            Subsystem(
                id="main_control",
                name="Main Control Unit",
                description="Central processing and control logic for ventilation modes",
                iec_62304_section="§5.3.1 - Software System Architecture",
                iso_14971_hazards=[
                    "H001: Incorrect tidal volume delivery",
                    "H002: Failure to detect apnea",
                    "H003: Software failure causing loss of ventilation"
                ],
                required_components=["microcontroller", "watchdog_timer", "rtc"],
                interfaces=["pressure_sensor_bus", "flow_sensor_bus", "motor_control_pwm", "user_interface"],
                safety_requirements=[
                    "SR001: Redundant monitoring of critical parameters",
                    "SR002: Watchdog timer with <100ms timeout",
                    "SR003: Safe state on power loss"
                ],
                test_requirements=[
                    "TR001: Verify all alarm conditions trigger within 5s",
                    "TR002: Validate mode transitions",
                    "TR003: Endurance test 30 days continuous operation"
                ]
            ),
            
            Subsystem(
                id="gas_delivery",
                name="Gas Delivery System",
                description="Pneumatic system for delivering gas mixture to patient",
                iec_62304_section="§5.3.2 - Hardware Interface Design",
                iso_14971_hazards=[
                    "H004: Overpressure causing barotrauma",
                    "H005: Inadequate gas delivery",
                    "H006: Contaminated gas delivery"
                ],
                required_components=["blower", "proportional_valve", "hepa_filter", "pressure_relief_valve"],
                interfaces=["main_control", "sensing_system", "patient_circuit"],
                safety_requirements=[
                    "SR004: Maximum pressure limit 60cmH2O",
                    "SR005: HEPA filtration 99.97% @ 0.3μm",
                    "SR006: Mechanical pressure relief valve"
                ],
                test_requirements=[
                    "TR004: Pressure accuracy ±2cmH2O",
                    "TR005: Flow accuracy ±10%",
                    "TR006: Filter efficiency test"
                ]
            ),
            
            Subsystem(
                id="sensing_system",
                name="Sensing and Monitoring",
                description="Sensors for pressure, flow, and oxygen concentration",
                iec_62304_section="§5.3.3 - Sensor Interface Design",
                iso_14971_hazards=[
                    "H007: Inaccurate pressure reading",
                    "H008: Flow sensor drift",
                    "H009: Oxygen sensor failure"
                ],
                required_components=["pressure_sensor", "flow_sensor", "o2_sensor", "signal_conditioning"],
                interfaces=["main_control", "gas_delivery"],
                safety_requirements=[
                    "SR007: Pressure sensor accuracy ±1%",
                    "SR008: Flow sensor response time <10ms",
                    "SR009: Dual redundant pressure sensing"
                ],
                test_requirements=[
                    "TR007: Sensor calibration verification",
                    "TR008: Drift test over 24 hours",
                    "TR009: Cross-talk interference test"
                ]
            ),
            
            Subsystem(
                id="user_interface",
                name="User Interface and Display",
                description="Touchscreen for settings and real-time monitoring",
                iec_62304_section="§5.3.4 - User Interface Design",
                iso_14971_hazards=[
                    "H010: Misinterpretation of displayed data",
                    "H011: Incorrect parameter entry",
                    "H012: Alarm not visible/audible"
                ],
                required_components=["touchscreen_display", "alarm_speaker", "indicator_leds"],
                interfaces=["main_control"],
                safety_requirements=[
                    "SR010: Alarm priority per IEC 60601-1-8",
                    "SR011: Display update rate ≥1Hz",
                    "SR012: Backup battery for alarms"
                ],
                test_requirements=[
                    "TR010: Usability testing per IEC 62366-1",
                    "TR011: Alarm audibility test",
                    "TR012: Display visibility in various lighting"
                ]
            ),
            
            Subsystem(
                id="power_system",
                name="Power Supply and Management",
                description="AC/DC power with battery backup",
                iec_62304_section="§5.3.5 - Power Management Design",
                iso_14971_hazards=[
                    "H013: Loss of mains power",
                    "H014: Battery depletion",
                    "H015: Power supply failure"
                ],
                required_components=["ac_dc_converter", "battery_backup", "power_monitoring"],
                interfaces=["main_control", "all_subsystems"],
                safety_requirements=[
                    "SR013: Battery runtime ≥30 minutes",
                    "SR014: 2xMOPP isolation per IEC 60601-1",
                    "SR015: Power fail alarm with 10s warning"
                ],
                test_requirements=[
                    "TR013: Battery runtime test",
                    "TR014: Isolation voltage test 4000V",
                    "TR015: Power interruption test"
                ]
            ),
            
            Subsystem(
                id="safety_monitoring",
                name="Safety and Alarm System",
                description="Independent safety monitoring and alarm generation",
                iec_62304_section="§5.3.6 - Safety Monitoring Architecture",
                iso_14971_hazards=[
                    "H016: Failure to detect hazardous condition",
                    "H017: False alarm causing alarm fatigue",
                    "H018: Alarm system failure"
                ],
                required_components=["independent_monitor", "alarm_controller", "backup_alarm"],
                interfaces=["main_control", "sensing_system", "user_interface"],
                safety_requirements=[
                    "SR016: Independent monitoring separate from main MCU",
                    "SR017: Alarm latching until acknowledged",
                    "SR018: Alarm priority classification"
                ],
                test_requirements=[
                    "TR016: Fault injection testing",
                    "TR017: Alarm response time <5s",
                    "TR018: Alarm persistence test"
                ]
            )
        ]
    
    def specify_components(self, subsystem: Subsystem, requirements: DesignRequirements) -> List[ComponentSpec]:
        """
        Specify components for each subsystem (deterministic rules)
        """
        specs_map = {
            "main_control": [
                ComponentSpec(
                    category="microcontroller",
                    description="ARM Cortex-M4 or better for real-time control",
                    required_specs={
                        "architecture": "ARM Cortex-M4",
                        "clock_speed_mhz": 168,
                        "ram_kb": 256,
                        "flash_kb": 1024,
                        "fpu": True,
                        "package": "LQFP100"
                    },
                    optional_specs={
                        "crypto_acceleration": True,
                        "ethernet": False
                    },
                    safety_critical=True,
                    medical_grade_required=True,
                    certifications_required=["IEC 60601-1"]
                ),
                ComponentSpec(
                    category="watchdog_timer",
                    description="Independent watchdog for system monitoring",
                    required_specs={
                        "type": "external",
                        "timeout_ms": 100,
                        "reset_output": True
                    },
                    safety_critical=True,
                    medical_grade_required=True
                ),
                ComponentSpec(
                    category="rtc",
                    description="Real-time clock for logging",
                    required_specs={
                        "accuracy_ppm": 20,
                        "battery_backup": True,
                        "interface": "I2C"
                    },
                    safety_critical=False,
                    medical_grade_required=False
                )
            ],
            
            "gas_delivery": [
                ComponentSpec(
                    category="blower",
                    description="Brushless DC blower for gas delivery",
                    required_specs={
                        "type": "brushless_dc",
                        "max_pressure_cmh2o": 60,
                        "max_flow_lpm": 180,
                        "voltage": requirements.input_voltage,
                        "noise_db": 55
                    },
                    optional_specs={
                        "efficiency": 0.85
                    },
                    safety_critical=True,
                    medical_grade_required=True,
                    certifications_required=["IEC 60601-1", "ISO 80601-2-12"]
                ),
                ComponentSpec(
                    category="proportional_valve",
                    description="Proportional solenoid valve for flow control",
                    required_specs={
                        "type": "proportional_solenoid",
                        "response_time_ms": 10,
                        "cv": 0.5,
                        "voltage": requirements.input_voltage,
                        "control": "PWM"
                    },
                    safety_critical=True,
                    medical_grade_required=True
                ),
                ComponentSpec(
                    category="hepa_filter",
                    description="HEPA filter for gas filtration",
                    required_specs={
                        "efficiency_percent": 99.97,
                        "particle_size_um": 0.3,
                        "pressure_drop_pa": 200
                    },
                    safety_critical=True,
                    medical_grade_required=True,
                    certifications_required=["ISO 80601-2-12"]
                ),
                ComponentSpec(
                    category="pressure_relief_valve",
                    description="Mechanical overpressure protection",
                    required_specs={
                        "set_pressure_cmh2o": 60,
                        "tolerance_cmh2o": 2,
                        "type": "spring_loaded"
                    },
                    safety_critical=True,
                    medical_grade_required=True
                )
            ],
            
            "sensing_system": [
                ComponentSpec(
                    category="pressure_sensor",
                    description="Differential pressure sensor for airway monitoring",
                    required_specs={
                        "type": "differential",
                        "range_cmh2o": 100,
                        "accuracy_percent": requirements.sensor_accuracy_percent,
                        "response_time_ms": 1,
                        "output": "I2C",
                        "medical_grade": True
                    },
                    safety_critical=True,
                    medical_grade_required=True,
                    certifications_required=["IEC 60601-1"]
                ),
                ComponentSpec(
                    category="flow_sensor",
                    description="Mass flow sensor for volume monitoring",
                    required_specs={
                        "type": "thermal_mass_flow",
                        "range_lpm": 200,
                        "accuracy_percent": 3.0,
                        "response_time_ms": 10,
                        "output": "I2C"
                    },
                    safety_critical=True,
                    medical_grade_required=True
                ),
                ComponentSpec(
                    category="o2_sensor",
                    description="Oxygen concentration sensor",
                    required_specs={
                        "type": "galvanic_cell",
                        "range_percent": 100,
                        "accuracy_percent": 2.0,
                        "response_time_s": 20,
                        "lifespan_months": 24
                    },
                    safety_critical=True,
                    medical_grade_required=True
                ),
                ComponentSpec(
                    category="signal_conditioning",
                    description="ADC for analog sensor signals",
                    required_specs={
                        "resolution_bits": 16,
                        "channels": 8,
                        "sample_rate_sps": 1000,
                        "interface": "SPI"
                    },
                    safety_critical=True,
                    medical_grade_required=True
                )
            ],
            
            "user_interface": [
                ComponentSpec(
                    category="touchscreen_display",
                    description="TFT touchscreen for user interface",
                    required_specs={
                        "size_inch": 7.0,
                        "resolution": "800x480",
                        "touch_type": "capacitive",
                        "interface": "RGB",
                        "brightness_nits": 400
                    },
                    safety_critical=False,
                    medical_grade_required=True,
                    certifications_required=["IEC 60601-1"]
                ),
                ComponentSpec(
                    category="alarm_speaker",
                    description="Piezo speaker for alarms",
                    required_specs={
                        "type": "piezo",
                        "spl_db": 85,
                        "frequency_hz": 2500,
                        "voltage": requirements.input_voltage
                    },
                    safety_critical=True,
                    medical_grade_required=True
                ),
                ComponentSpec(
                    category="indicator_leds",
                    description="Status indicator LEDs",
                    required_specs={
                        "colors": ["red", "yellow", "green"],
                        "brightness_mcd": 100,
                        "viewing_angle": 120
                    },
                    safety_critical=False,
                    medical_grade_required=False
                )
            ],
            
            "power_system": [
                ComponentSpec(
                    category="ac_dc_converter",
                    description="Medical-grade AC/DC power supply",
                    required_specs={
                        "input_voltage": "100-240VAC",
                        "output_voltage": requirements.input_voltage,
                        "output_current": requirements.max_current,
                        "efficiency_percent": 85,
                        "isolation": "2xMOPP"
                    },
                    safety_critical=True,
                    medical_grade_required=True,
                    certifications_required=["IEC 60601-1", "IEC 60601-2-12"]
                ),
                ComponentSpec(
                    category="battery_backup",
                    description="Lithium-ion battery for backup power",
                    required_specs={
                        "chemistry": "Li-Ion",
                        "voltage": requirements.input_voltage,
                        "capacity_ah": 5.0,
                        "runtime_minutes": 30,
                        "charge_time_hours": 4
                    },
                    safety_critical=True,
                    medical_grade_required=True
                ),
                ComponentSpec(
                    category="power_monitoring",
                    description="Power supply monitor IC",
                    required_specs={
                        "voltage_monitor": True,
                        "current_monitor": True,
                        "interface": "I2C",
                        "accuracy_percent": 1.0
                    },
                    safety_critical=True,
                    medical_grade_required=True
                )
            ],
            
            "safety_monitoring": [
                ComponentSpec(
                    category="independent_monitor",
                    description="Independent safety monitor MCU",
                    required_specs={
                        "architecture": "ARM Cortex-M0",
                        "clock_speed_mhz": 48,
                        "ram_kb": 32,
                        "independent": True
                    },
                    safety_critical=True,
                    medical_grade_required=True
                ),
                ComponentSpec(
                    category="alarm_controller",
                    description="Alarm management controller",
                    required_specs={
                        "priority_levels": 3,
                        "latching": True,
                        "backup_power": True
                    },
                    safety_critical=True,
                    medical_grade_required=True
                ),
                ComponentSpec(
                    category="backup_alarm",
                    description="Backup alarm system",
                    required_specs={
                        "type": "mechanical",
                        "power_source": "battery",
                        "spl_db": 85
                    },
                    safety_critical=True,
                    medical_grade_required=True
                )
            ]
        }
        
        return specs_map.get(subsystem.id, [])
