"""
Reliability and MTBF Calculation Module

Implements reliability analysis per:
- IEC 62304 (Software life cycle)
- ISO 14971 (Risk management)
- MIL-HDBK-217F (Reliability prediction)
- IEC 61508 (Functional safety)

Author: Medical Digital Twin System
"""

import math
from typing import Dict, List, Any, Optional
from enum import Enum


class FailureRate:
    """Component failure rates (failures per million hours)"""
    
    # Based on MIL-HDBK-217F and industry data
    COMPONENT_FAILURE_RATES = {
        "sensor_pressure": 0.5,      # High reliability sensors
        "sensor_flow": 0.8,
        "sensor_temperature": 0.3,
        "sensor_spo2": 1.2,
        "actuator_valve": 2.0,       # Mechanical components higher
        "actuator_pump": 2.5,
        "controller_mcu": 0.1,       # Electronics very reliable
        "controller_asic": 0.05,
        "power_supply": 1.5,
        "power_battery": 5.0,         # Batteries degrade
        "display_lcd": 1.0,
        "communication_module": 0.8,
        "memory_flash": 0.2,
        "connector": 0.5,
        "pcb": 0.1,
        "fan": 10.0,                  # Fans are high failure rate
        "alarm_buzzer": 2.0
    }
    
    # Environmental factors (π factors per MIL-HDBK-217F)
    ENVIRONMENTAL_FACTORS = {
        "ground_benign": 1.0,      # Laboratory conditions
        "ground_mobile": 5.0,      # Ground mobile (ambulance)
        "airborne_transport": 10.0, # Aircraft
        "naval_sheltered": 6.0,    # Ship
        "medical_clinical": 2.0    # Hospital/clinic (our target)
    }
    
    # Temperature acceleration factor
    # Arrhenius equation: AF = exp(Ea/k * (1/T1 - 1/T2))
    ACTIVATION_ENERGY = 0.7  # eV typical for electronics
    BOLTZMANN = 8.617e-5     # eV/K


class ReliabilityCalculator:
    """
    Medical device reliability and MTBF calculator.
    
    Per IEC 62304: Medical software must have documented
    reliability requirements and failure mode analysis.
    """
    
    # IEC 62304 safety classes
    SAFETY_CLASS_REQUIREMENTS = {
        "Class A": {
            "description": "No injury or damage to health",
            "min_mtbf_hours": 1000,
            "failure_mode_analysis": "Basic",
            "documentation_level": "Reduced"
        },
        "Class B": {
            "description": "Non-serious injury",
            "min_mtbf_hours": 5000,
            "failure_mode_analysis": "Moderate",
            "documentation_level": "Standard"
        },
        "Class C": {
            "description": "Death or serious injury",
            "min_mtbf_hours": 10000,
            "failure_mode_analysis": "Comprehensive (FMEA/FMECA)",
            "documentation_level": "Full"
        }
    }
    
    @staticmethod
    def calculate_component_mtbf(
        component_type: str,
        quantity: int = 1,
        environment: str = "medical_clinical",
        operating_temp_c: float = 40.0,
        quality_grade: str = "medical"
    ) -> Dict[str, Any]:
        """
        Calculate component MTBF using MIL-HDBK-217F methodology.
        
        Args:
            component_type: Type of component
            quantity: Number of identical components (in series)
            environment: Operating environment
            operating_temp_c: Operating temperature
            quality_grade: Quality level (commercial, industrial, medical)
            
        Returns:
            Dict with MTBF analysis
        """
        # Base failure rate (failures per million hours)
        base_lambda = FailureRate.COMPONENT_FAILURE_RATES.get(
            component_type, 1.0
        )
        
        # Environmental factor
        env_factor = FailureRate.ENVIRONMENTAL_FACTORS.get(
            environment, 2.0
        )
        
        # Temperature acceleration factor
        # Using Arrhenius equation
        T_ref = 298.15  # 25°C in Kelvin
        T_op = operating_temp_c + 273.15  # Operating temp in Kelvin
        
        temp_factor = math.exp(
            FailureRate.ACTIVATION_ENERGY / FailureRate.BOLTZMANN *
            (1/T_ref - 1/T_op)
        )
        
        # Quality factor
        quality_factors = {
            "commercial": 2.0,
            "industrial": 1.5,
            "medical": 1.0,  # Highest quality
            "space": 0.5     # Ultra high reliability
        }
        quality_factor = quality_factors.get(quality_grade, 1.5)
        
        # Total failure rate
        total_lambda = (
            base_lambda * env_factor * temp_factor * 
            quality_factor * quantity
        )
        
        # MTBF in hours
        mtbf_hours = 1_000_000 / total_lambda
        
        # Convert to years
        mtbf_years = mtbf_hours / 8760
        
        return {
            "component_type": component_type,
            "quantity": quantity,
            "base_failure_rate_fpmh": base_lambda,
            "environmental_factor": env_factor,
            "temperature_factor": round(temp_factor, 3),
            "quality_factor": quality_factor,
            "total_failure_rate_fpmh": round(total_lambda, 3),
            "mtbf_hours": round(mtbf_hours, 0),
            "mtbf_years": round(mtbf_years, 2),
            "reliability_at_1yr_percent": round(
                math.exp(-8760 / mtbf_hours) * 100, 2
            ),
            "standard": "MIL-HDBK-217F"
        }
    
    @staticmethod
    def calculate_system_mtbf(
        components: List[Dict[str, Any]],
        architecture: str = "series"
    ) -> Dict[str, Any]:
        """
        Calculate system-level MTBF.
        
        Args:
            components: List of component MTBF data
            architecture: System architecture (series, parallel, etc.)
            
        Returns:
            Dict with system reliability analysis
        """
        if architecture == "series":
            # Series system: 1/MTBF_sys = Σ(1/MTBF_i)
            total_failure_rate = sum(
                1_000_000 / comp["mtbf_hours"] 
                for comp in components
            )
            system_mtbf = 1_000_000 / total_failure_rate
            
        elif architecture == "parallel":
            # Parallel (redundant) system
            # R_sys(t) = 1 - Π(1 - R_i(t))
            # Approximation for high reliability
            mtbfs = [comp["mtbf_hours"] for comp in components]
            system_mtbf = sum(mtbfs)  # Simplified
            
        else:
            # Default to series (conservative)
            total_failure_rate = sum(
                1_000_000 / comp["mtbf_hours"] 
                for comp in components
            )
            system_mtbf = 1_000_000 / total_failure_rate
        
        # Calculate reliability at key timepoints
        reliability_1yr = math.exp(-8760 / system_mtbf) * 100
        reliability_5yr = math.exp(-43800 / system_mtbf) * 100
        reliability_10yr = math.exp(-87600 / system_mtbf) * 100
        
        return {
            "architecture": architecture,
            "num_components": len(components),
            "system_mtbf_hours": round(system_mtbf, 0),
            "system_mtbf_years": round(system_mtbf / 8760, 2),
            "reliability_1_year_percent": round(reliability_1yr, 2),
            "reliability_5_year_percent": round(reliability_5yr, 2),
            "reliability_10_year_percent": round(reliability_10yr, 2),
            "meets_medical_requirement": system_mtbf >= 10000,
            "standard": "IEC 62304 Class C requires MTBF > 10,000 hours"
        }
    
    @staticmethod
    def perform_fmea_analysis(
        component_name: str,
        component_type: str,
        failure_modes: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Perform Failure Mode and Effects Analysis (FMEA).
        
        Required by ISO 14971 for risk management.
        
        Args:
            component_name: Component identifier
            component_type: Type of component
            failure_modes: List of potential failure modes
            
        Returns:
            Dict with FMEA results
        """
        # Default failure modes per component type
        default_failure_modes = {
            "sensor": [
                {
                    "mode": "Out of calibration",
                    "effect": "Incorrect readings",
                    "severity": 8,
                    "occurrence": 3,
                    "detection": 4,
                    "mitigation": "Calibration check at startup + periodic"
                },
                {
                    "mode": "Complete failure",
                    "effect": "No readings",
                    "severity": 9,
                    "occurrence": 2,
                    "detection": 2,
                    "mitigation": "Sensor fault detection + alarm"
                },
                {
                    "mode": "Intermittent connection",
                    "effect": "Sporadic data loss",
                    "severity": 7,
                    "occurrence": 2,
                    "detection": 3,
                    "mitigation": "Connection monitoring + redundancy"
                }
            ],
            "actuator": [
                {
                    "mode": "Stuck closed",
                    "effect": "No flow",
                    "severity": 9,
                    "occurrence": 2,
                    "detection": 2,
                    "mitigation": "Position feedback + alarm"
                },
                {
                    "mode": "Stuck open",
                    "effect": "Uncontrolled flow",
                    "severity": 10,
                    "occurrence": 1,
                    "detection": 2,
                    "mitigation": "Flow monitoring + mechanical stop"
                },
                {
                    "mode": "Slow response",
                    "effect": "Delayed control",
                    "severity": 6,
                    "occurrence": 3,
                    "detection": 4,
                    "mitigation": "Response time monitoring"
                }
            ],
            "power_supply": [
                {
                    "mode": "Output voltage out of range",
                    "effect": "Device malfunction",
                    "severity": 9,
                    "occurrence": 2,
                    "detection": 2,
                    "mitigation": "Voltage monitoring + shutdown"
                },
                {
                    "mode": "Complete failure",
                    "effect": "Loss of power",
                    "severity": 10,
                    "occurrence": 1,
                    "detection": 1,
                    "mitigation": "Battery backup + alarm"
                }
            ],
            "controller": [
                {
                    "mode": "Software crash",
                    "effect": "System halt",
                    "severity": 10,
                    "occurrence": 1,
                    "detection": 2,
                    "mitigation": "Watchdog timer + safe state"
                },
                {
                    "mode": "Communication loss",
                    "effect": "No control",
                    "severity": 9,
                    "occurrence": 2,
                    "detection": 2,
                    "mitigation": "Timeout detection + safe defaults"
                }
            ]
        }
        
        # Use provided or default failure modes
        modes = failure_modes or default_failure_modes.get(component_type, [])
        
        # Calculate Risk Priority Number (RPN) for each mode
        for mode in modes:
            mode["rpn"] = (
                mode["severity"] * 
                mode["occurrence"] * 
                mode["detection"]
            )
            
            # Risk classification
            if mode["rpn"] < 100:
                mode["risk_level"] = "Low"
            elif mode["rpn"] < 200:
                mode["risk_level"] = "Moderate"
            elif mode["rpn"] < 300:
                mode["risk_level"] = "High"
            else:
                mode["risk_level"] = "Critical"
        
        # Sort by RPN (highest risk first)
        modes.sort(key=lambda x: x["rpn"], reverse=True)
        
        return {
            "component_name": component_name,
            "component_type": component_type,
            "failure_modes": modes,
            "highest_rpn": modes[0]["rpn"] if modes else 0,
            "critical_modes": [m for m in modes if m["rpn"] >= 300],
            "standard": "ISO 14971:2019 Risk Management",
            "recommendation": "All modes with RPN > 200 require mitigation"
        }
    
    @staticmethod
    def calculate_safety_integrity_level(
        failure_rate_fpmh: float,
        proof_test_interval_months: int = 12
    ) -> Dict[str, Any]:
        """
        Calculate Safety Integrity Level per IEC 61508.
        
        Args:
            failure_rate_fpmh: Failure rate (failures per million hours)
            proof_test_interval_months: Interval for proof testing
            
        Returns:
            Dict with SIL classification
        """
        # Convert to probability of failure per hour (PFH)
        pfh = failure_rate_fpmh / 1_000_000
        
        # SIL classification (Low demand mode - IEC 61508-1 Table 2)
        if pfh < 1e-9:
            sil = "SIL 4"
            description = "10^-9 to 10^-8 (highest integrity)"
        elif pfh < 1e-8:
            sil = "SIL 3"
            description = "10^-8 to 10^-7 (high integrity)"
        elif pfh < 1e-7:
            sil = "SIL 2"
            description = "10^-7 to 10^-6 (moderate integrity)"
        elif pfh < 1e-6:
            sil = "SIL 1"
            description = "10^-6 to 10^-5 (basic integrity)"
        else:
            sil = "Below SIL 1"
            description = "Insufficient safety integrity"
        
        # Medical devices typically require SIL 2 minimum
        meets_medical = sil in ["SIL 2", "SIL 3", "SIL 4"]
        
        return {
            "failure_rate_fpmh": failure_rate_fpmh,
            "probability_failure_per_hour": f"{pfh:.2e}",
            "sil_level": sil,
            "description": description,
            "meets_medical_requirement": meets_medical,
            "recommended_sil_for_medical": "SIL 2 minimum",
            "standard": "IEC 61508 Functional Safety"
        }
    
    @staticmethod
    def recommend_redundancy(
        component_mtbf: float,
        required_system_mtbf: float = 10000
    ) -> Dict[str, Any]:
        """
        Recommend redundancy strategy to meet reliability targets.
        
        Args:
            component_mtbf: Component MTBF (hours)
            required_system_mtbf: Target system MTBF (hours)
            
        Returns:
            Dict with redundancy recommendations
        """
        # Check if single component meets requirement
        if component_mtbf >= required_system_mtbf:
            return {
                "redundancy_required": False,
                "recommendation": "Single component meets reliability target",
                "component_mtbf": component_mtbf,
                "target_mtbf": required_system_mtbf
            }
        
        # Calculate required redundancy
        # For parallel redundancy: MTBF_sys ≈ MTBF_component * (1 + 1/2 + 1/3 + ... + 1/n)
        n_redundant = 2
        while True:
            # Harmonic series approximation
            parallel_mtbf = component_mtbf * sum(1/i for i in range(1, n_redundant + 1))
            if parallel_mtbf >= required_system_mtbf or n_redundant > 5:
                break
            n_redundant += 1
        
        return {
            "redundancy_required": True,
            "component_mtbf": component_mtbf,
            "target_mtbf": required_system_mtbf,
            "recommended_redundancy": f"{n_redundant}x parallel",
            "expected_system_mtbf": round(parallel_mtbf, 0),
            "improvement_factor": round(parallel_mtbf / component_mtbf, 2),
            "standard": "IEC 60601-1 §14 (Programmable electrical medical systems)"
        }
