"""
Component Derating Module for Medical Devices

Implements IEC 60601-1 and IEC 60747 derating requirements:
- Electrical derating (80% max rating rule)
- Temperature derating (0.5% per °C above 25°C)
- Voltage/current safety margins
- Power dissipation calculations

Author: Medical Digital Twin System
Standards: IEC 60601-1, IEC 60747, MIL-HDBK-217
"""

import math
from typing import Dict, Any, Optional


class ComponentDerating:
    """
    Component derating calculator for medical device reliability.
    
    Per IEC 60601-1: Components must operate below their maximum ratings
    to ensure long-term reliability and patient safety.
    """
    
    # IEC 60601-1 derating factors
    ELECTRICAL_DERATING = 0.80  # Use only 80% of max rating
    THERMAL_DERATING_PER_C = 0.005  # 0.5% per °C above 25°C
    BASELINE_TEMP = 25.0  # °C
    MIN_DERATING = 0.50  # Never derate below 50%
    
    # Safety margins per component type
    SAFETY_MARGINS = {
        "sensor": 1.25,      # 25% margin for sensors
        "actuator": 1.20,    # 20% margin for actuators
        "power": 1.50,       # 50% margin for power components
        "controller": 1.30,  # 30% margin for controllers
        "safety": 2.00       # 100% margin for safety-critical
    }
    
    @staticmethod
    def calculate_electrical_derating(
        nominal_value: float,
        max_rated_value: float,
        component_type: str = "sensor"
    ) -> Dict[str, Any]:
        """
        Calculate electrical derating per IEC 60601-1.
        
        Args:
            nominal_value: Required operating value
            max_rated_value: Component's maximum rated value
            component_type: Type of component (sensor, actuator, power, etc.)
            
        Returns:
            Dict with:
                - selected_rating: Actual component rating to select
                - derating_factor: Applied derating (0.8 for medical)
                - safety_margin: Additional safety margin
                - utilization: Percentage of component capacity used
                - compliant: Whether selection meets IEC 60601-1
        """
        derating_factor = ComponentDerating.ELECTRICAL_DERATING
        safety_margin = ComponentDerating.SAFETY_MARGINS.get(component_type, 1.2)
        
        # Calculate required rating with derating
        # If we need X, and can only use 80% of rating, need rating of X/0.8
        required_rating_with_derating = nominal_value / derating_factor
        
        # Apply additional safety margin
        selected_rating = required_rating_with_derating * safety_margin
        
        # Calculate actual utilization
        utilization = (nominal_value / selected_rating) * 100
        
        # Check compliance (utilization should be < 80%)
        compliant = utilization <= (derating_factor * 100)
        
        return {
            "nominal_value": nominal_value,
            "selected_rating": selected_rating,
            "derating_factor": derating_factor,
            "safety_margin": safety_margin,
            "utilization_percent": round(utilization, 2),
            "compliant": compliant,
            "standard": "IEC 60601-1 §8.7.4"
        }
    
    @staticmethod
    def calculate_thermal_derating(
        ambient_temp: float,
        max_operating_temp: float,
        component_max_temp: float
    ) -> Dict[str, Any]:
        """
        Calculate temperature derating per IEC 60747.
        
        Args:
            ambient_temp: Operating ambient temperature (°C)
            max_operating_temp: Maximum expected operating temp (°C)
            component_max_temp: Component's maximum rated temp (°C)
            
        Returns:
            Dict with thermal derating analysis
        """
        baseline = ComponentDerating.BASELINE_TEMP
        derating_per_c = ComponentDerating.THERMAL_DERATING_PER_C
        min_derating = ComponentDerating.MIN_DERATING
        
        # Calculate temperature derating factor
        if max_operating_temp > baseline:
            temp_delta = max_operating_temp - baseline
            thermal_derating = 1.0 - (derating_per_c * temp_delta)
            thermal_derating = max(thermal_derating, min_derating)
        else:
            thermal_derating = 1.0
        
        # Calculate temperature margin
        temp_margin = component_max_temp - max_operating_temp
        
        # Check compliance (need at least 20°C margin)
        compliant = temp_margin >= 20.0
        
        return {
            "ambient_temp_c": ambient_temp,
            "max_operating_temp_c": max_operating_temp,
            "component_max_temp_c": component_max_temp,
            "thermal_derating_factor": round(thermal_derating, 3),
            "temperature_margin_c": temp_margin,
            "compliant": compliant,
            "standard": "IEC 60747 §4.2"
        }
    
    @staticmethod
    def calculate_power_derating(
        power_required_w: float,
        ambient_temp: float,
        thermal_resistance: float = 40.0  # °C/W typical
    ) -> Dict[str, Any]:
        """
        Calculate power dissipation and derating for power components.
        
        Args:
            power_required_w: Required power output
            ambient_temp: Operating temperature
            thermal_resistance: Junction-to-ambient thermal resistance
            
        Returns:
            Dict with power derating analysis
        """
        # Medical devices: derate power to 50% of max for reliability
        power_safety_margin = 2.0
        selected_power_rating = power_required_w * power_safety_margin
        
        # Calculate junction temperature rise
        junction_temp_rise = power_required_w * thermal_resistance
        junction_temp = ambient_temp + junction_temp_rise
        
        # Maximum junction temp for medical (typically 100°C for reliability)
        max_junction_temp = 100.0
        junction_margin = max_junction_temp - junction_temp
        
        compliant = junction_temp < max_junction_temp
        
        return {
            "power_required_w": power_required_w,
            "selected_rating_w": selected_power_rating,
            "safety_margin": power_safety_margin,
            "junction_temp_c": round(junction_temp, 1),
            "junction_margin_c": round(junction_margin, 1),
            "thermal_resistance_c_per_w": thermal_resistance,
            "compliant": compliant,
            "standard": "IEC 60601-1 §8.7.3"
        }
    
    @staticmethod
    def calculate_voltage_derating(
        operating_voltage: float,
        component_type: str = "power"
    ) -> Dict[str, Any]:
        """
        Calculate voltage derating for reliability.
        
        Args:
            operating_voltage: Required operating voltage
            component_type: Type of component
            
        Returns:
            Dict with voltage derating recommendations
        """
        derating = ComponentDerating.ELECTRICAL_DERATING
        safety_margin = ComponentDerating.SAFETY_MARGINS.get(component_type, 1.5)
        
        # For voltage: Must select component rated at least 125% of operating
        minimum_voltage_rating = operating_voltage / derating
        recommended_voltage_rating = operating_voltage * safety_margin
        
        return {
            "operating_voltage": operating_voltage,
            "minimum_rating": round(minimum_voltage_rating, 1),
            "recommended_rating": round(recommended_voltage_rating, 1),
            "derating_factor": derating,
            "safety_margin": safety_margin,
            "standard": "IEC 60601-1 §8.7.4.1"
        }
    
    @staticmethod
    def calculate_current_derating(
        operating_current: float,
        duty_cycle: float = 1.0,
        component_type: str = "power"
    ) -> Dict[str, Any]:
        """
        Calculate current derating including duty cycle effects.
        
        Args:
            operating_current: Required operating current (A)
            duty_cycle: Operating duty cycle (0.0 to 1.0)
            component_type: Type of component
            
        Returns:
            Dict with current derating recommendations
        """
        derating = ComponentDerating.ELECTRICAL_DERATING
        safety_margin = ComponentDerating.SAFETY_MARGINS.get(component_type, 1.5)
        
        # RMS current for duty cycle
        rms_current = operating_current * math.sqrt(duty_cycle)
        
        # Derate for continuous operation
        minimum_current_rating = rms_current / derating
        recommended_current_rating = rms_current * safety_margin
        
        return {
            "operating_current": operating_current,
            "duty_cycle": duty_cycle,
            "rms_current": round(rms_current, 3),
            "minimum_rating": round(minimum_current_rating, 3),
            "recommended_rating": round(recommended_current_rating, 3),
            "derating_factor": derating,
            "safety_margin": safety_margin,
            "standard": "IEC 60601-1 §8.7.4.2"
        }
    
    @staticmethod
    def select_sensor_with_derating(
        measurement_range: float,
        required_accuracy: float,
        sensor_type: str = "pressure"
    ) -> Dict[str, Any]:
        """
        Select sensor with proper derating for medical applications.
        
        Args:
            measurement_range: Maximum value to measure
            required_accuracy: Required measurement accuracy (%)
            sensor_type: Type of sensor
            
        Returns:
            Dict with sensor selection recommendations
        """
        # Medical sensors: Use only 80% of full scale for accuracy
        derating = ComponentDerating.ELECTRICAL_DERATING
        safety_margin = ComponentDerating.SAFETY_MARGINS["sensor"]
        
        # Calculate required sensor range
        minimum_sensor_range = measurement_range / derating
        recommended_sensor_range = measurement_range * safety_margin
        
        # Accuracy degrades near full scale - apply correction
        # Medical devices require ±1% full-scale accuracy typical
        effective_accuracy = required_accuracy / derating
        
        return {
            "measurement_range": measurement_range,
            "minimum_sensor_range": round(minimum_sensor_range, 1),
            "recommended_sensor_range": round(recommended_sensor_range, 1),
            "required_accuracy_percent": required_accuracy,
            "effective_accuracy_percent": round(effective_accuracy, 2),
            "derating_factor": derating,
            "safety_margin": safety_margin,
            "sensor_type": sensor_type,
            "standard": "IEC 60601-1 §8.6.3"
        }
    
    @staticmethod
    def calculate_component_stress_ratio(
        operating_value: float,
        rated_value: float
    ) -> Dict[str, Any]:
        """
        Calculate stress ratio for reliability prediction.
        
        Stress ratio = Operating value / Rated value
        Medical devices target: < 0.5 for critical components
        
        Args:
            operating_value: Actual operating parameter
            rated_value: Component's rated maximum
            
        Returns:
            Dict with stress analysis
        """
        stress_ratio = operating_value / rated_value
        
        # Classification per MIL-HDBK-217
        if stress_ratio < 0.3:
            stress_level = "Low (Excellent)"
        elif stress_ratio < 0.5:
            stress_level = "Moderate (Good for medical)"
        elif stress_ratio < 0.7:
            stress_level = "Normal (Acceptable)"
        elif stress_ratio < 0.8:
            stress_level = "High (Marginal)"
        else:
            stress_level = "Critical (Unacceptable)"
        
        # Medical device target: < 0.5 for safety-critical
        compliant = stress_ratio < 0.5
        
        return {
            "operating_value": operating_value,
            "rated_value": rated_value,
            "stress_ratio": round(stress_ratio, 3),
            "stress_level": stress_level,
            "compliant_for_medical": compliant,
            "target_ratio": 0.5,
            "standard": "MIL-HDBK-217F"
        }
