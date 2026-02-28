"""
Deterministic Rule-Based Requirements Parser (NO LLM)
Replaces LLM-based parsing with regex patterns and business rules
"""
import re
from typing import Dict, Any, Optional

# Subsystem hints by device type
DEVICE_SUBSYSTEMS = {
    "ventilator": [
        "PneumaticsControl", "MainControlUnit", "PowerSupply",
        "GasMixer", "SafetyMonitor", "PatientInterface", "Display&UI"
    ],
    "dialysis": [
        "BloodCircuit", "DialysateCircuit", "Ultrafiltration",
        "ExtracorporealSafety", "ControlSystem", "PowerAndThermal", "Display&UI"
    ],
    "pulse_ox": [
        "OpticalSensor", "SignalProcessing", "DisplayUnit"
    ]
}

def extract_numbers_with_unit(text: str) -> tuple[Optional[float], Optional[float], Optional[str]]:
    """
    Extract min/max values and units from requirement text
    Returns: (min_value, max_value, unit)
    """
    # Pattern for ranges: "10 to 20 V", "10-20V", "10..20 V"
    range_pattern = r'(\d+\.?\d*)\s*(?:to|-|\.\.)\s*(\d+\.?\d*)\s*([a-zA-Z/%°]+)'
    range_match = re.search(range_pattern, text)
    if range_match:
        return float(range_match.group(1)), float(range_match.group(2)), range_match.group(3)
    
    # Pattern for single value with tolerance: "120V ±5%", "120 V ±5%"
    tolerance_pattern = r'(\d+\.?\d*)\s*([a-zA-Z/%°]+)\s*±\s*(\d+\.?\d*)\s*([%a-zA-Z]+)'
    tolerance_match = re.search(tolerance_pattern, text)
    if tolerance_match:
        value = float(tolerance_match.group(1))
        unit = tolerance_match.group(2)
        tolerance = float(tolerance_match.group(3))
        tolerance_unit = tolerance_match.group(4)
        
        if tolerance_unit == '%':
            min_val = value * (1 - tolerance / 100)
            max_val = value * (1 + tolerance / 100)
        else:
            min_val = value - tolerance
            max_val = value + tolerance
        return min_val, max_val, unit
    
    # Pattern for max value: "up to 500 mA", "maximum 500mA", "< 500 mA"
    max_pattern = r'(?:up to|maximum|max|<|≤)\s*(\d+\.?\d*)\s*([a-zA-Z/%°]+)'
    max_match = re.search(max_pattern, text, re.IGNORECASE)
    if max_match:
        return None, float(max_match.group(1)), max_match.group(2)
    
    # Pattern for min value: "at least 100 V", "minimum 100V", "> 100 V"
    min_pattern = r'(?:at least|minimum|min|>|≥)\s*(\d+\.?\d*)\s*([a-zA-Z/%°]+)'
    min_match = re.search(min_pattern, text, re.IGNORECASE)
    if min_match:
        return float(min_match.group(1)), None, min_match.group(2)
    
    # Pattern for exact value: "120 V", "5 A"
    exact_pattern = r'(\d+\.?\d*)\s*([a-zA-Z/%°]+)(?:\s|,|\.|\b)'
    exact_match = re.search(exact_pattern, text)
    if exact_match:
        value = float(exact_match.group(1))
        unit = exact_match.group(2)
        return value, value, unit
    
    return None, None, None


def extract_response_time(text: str) -> Optional[int]:
    """Extract response time in milliseconds"""
    # Pattern for time: "100 ms", "100ms", "0.1 s", "1 second"
    time_pattern = r'(\d+\.?\d*)\s*(ms|millisecond|s|second)'
    time_match = re.search(time_pattern, text, re.IGNORECASE)
    if time_match:
        value = float(time_match.group(1))
        unit = time_match.group(2).lower()
        
        if unit in ['s', 'second']:
            return int(value * 1000)
        return int(value)
    
    return None


def classify_requirement_type(text: str) -> str:
    """
    Classify requirement type using keyword matching
    """
    text_lower = text.lower()
    
    # Safety keywords
    if any(keyword in text_lower for keyword in ['hazard', 'risk', 'fail', 'emergency', 'alarm', 'critical']):
        return 'safety'
    
    # Regulatory keywords
    if any(keyword in text_lower for keyword in ['iec', 'iso', 'fda', 'standard', 'compliance', 'regulatory']):
        return 'regulatory'
    
    # Interface keywords
    if any(keyword in text_lower for keyword in ['interface', 'communicate', 'protocol', 'bus', 'signal', 'connect']):
        return 'interface'
    
    # Environmental keywords
    if any(keyword in text_lower for keyword in ['temperature', 'humidity', 'storage', 'environment', 'operating condition']):
        return 'environmental'
    
    # Performance keywords (if has numbers)
    if re.search(r'\d+\.?\d*\s*[a-zA-Z/%°]+', text):
        return 'performance'
    
    # Default to functional
    return 'functional'


def classify_fr_or_nfr(text: str, req_type: str) -> str:
    """
    Classify as functional or non-functional requirement
    """
    text_lower = text.lower()
    
    # NFR indicators
    nfr_keywords = [
        'accuracy', 'precision', 'speed', 'response time', 'reliability',
        'compliance', 'standard', 'temperature', 'humidity', 'performance'
    ]
    
    if req_type in ['performance', 'environmental', 'regulatory']:
        return 'non-functional'
    
    if any(keyword in text_lower for keyword in nfr_keywords):
        return 'non-functional'
    
    # FR indicators: action verbs
    fr_verbs = ['shall', 'must', 'will', 'display', 'control', 'monitor', 'detect', 'measure']
    if any(verb in text_lower for verb in fr_verbs):
        return 'functional'
    
    return 'functional'


def extract_subsystem(text: str, device_type: str) -> Optional[str]:
    """
    Extract subsystem name from text based on device type
    """
    text_lower = text.lower()
    subsystems = DEVICE_SUBSYSTEMS.get(device_type.lower(), [])
    
    for subsystem in subsystems:
        if subsystem.lower() in text_lower:
            return subsystem
    
    # Keyword-based matching
    subsystem_keywords = {
        "pneumatics": "PneumaticsControl",
        "control": "MainControlUnit",
        "power": "PowerSupply",
        "gas": "GasMixer",
        "safety": "SafetyMonitor",
        "patient": "PatientInterface",
        "display": "Display&UI",
        "blood": "BloodCircuit",
        "dialysate": "DialysateCircuit",
        "ultrafiltration": "Ultrafiltration",
        "optical": "OpticalSensor",
        "signal": "SignalProcessing"
    }
    
    for keyword, subsystem in subsystem_keywords.items():
        if keyword in text_lower and subsystem in subsystems:
            return subsystem
    
    return None


def extract_priority(text: str) -> str:
    """Extract requirement priority (SHALL/SHOULD/MAY)"""
    text_lower = text.lower()
    
    if 'shall' in text_lower or 'must' in text_lower or 'required' in text_lower:
        return 'SHALL'
    elif 'should' in text_lower or 'recommended' in text_lower:
        return 'SHOULD'
    elif 'may' in text_lower or 'optional' in text_lower:
        return 'MAY'
    
    return 'SHALL'  # Default


def extract_severity(text: str) -> Optional[str]:
    """Extract severity level from text"""
    text_lower = text.lower()
    
    if 'critical' in text_lower or 'catastrophic' in text_lower:
        return 'Critical'
    elif 'high' in text_lower or 'major' in text_lower:
        return 'High'
    elif 'medium' in text_lower or 'moderate' in text_lower:
        return 'Medium'
    elif 'low' in text_lower or 'minor' in text_lower:
        return 'Low'
    
    return None


def extract_probability(text: str) -> Optional[str]:
    """Extract probability level from text"""
    text_lower = text.lower()
    
    if 'frequent' in text_lower:
        return 'Frequent'
    elif 'probable' in text_lower:
        return 'Probable'
    elif 'occasional' in text_lower:
        return 'Occasional'
    elif 'remote' in text_lower:
        return 'Remote'
    elif 'negligible' in text_lower or 'unlikely' in text_lower:
        return 'Negligible'
    
    return None


def extract_standard(text: str) -> tuple[Optional[str], Optional[str]]:
    """
    Extract standard name and clause
    Returns: (standard, clause)
    """
    # Pattern for standards: "IEC 60601-1", "ISO 14971", "ISO 80601-2-12"
    standard_pattern = r'(IEC|ISO|FDA|ANSI)\s*(\d+[-.\d]*)'
    standard_match = re.search(standard_pattern, text, re.IGNORECASE)
    
    if standard_match:
        standard = f"{standard_match.group(1).upper()} {standard_match.group(2)}"
        
        # Try to find clause/section reference
        clause_pattern = r'(?:§|section|clause)\s*([\d.]+)'
        clause_match = re.search(clause_pattern, text, re.IGNORECASE)
        clause = clause_match.group(1) if clause_match else None
        
        return standard, clause
    
    return None, None


def extract_interface(text: str) -> tuple[Optional[str], Optional[str]]:
    """
    Extract interface and protocol information
    Returns: (interface_description, protocol)
    """
    # Pattern for interface: "MCU to Sensor", "Controller -> Display"
    interface_pattern = r'(\w+)\s*(?:to|->|→)\s*(\w+)'
    interface_match = re.search(interface_pattern, text)
    
    interface_desc = None
    if interface_match:
        interface_desc = f"{interface_match.group(1)} -> {interface_match.group(2)}"
    
    # Extract protocol
    protocols = ['I2C', 'SPI', 'UART', 'CAN', 'USB', 'Ethernet', 'Modbus', 'RS-232', 'RS-485']
    protocol = None
    text_upper = text.upper()
    for p in protocols:
        if p in text_upper:
            protocol = p
            break
    
    return interface_desc, protocol


def generate_title(text: str, req_type: str) -> str:
    """Generate a concise title from requirement text"""
    # Take first sentence or first 60 characters
    first_sentence = text.split('.')[0].strip()
    if len(first_sentence) > 60:
        first_sentence = first_sentence[:60] + '...'
    return first_sentence


def analyze_requirement_text(text: str, device_type: str = "ventilator") -> Dict[str, Any]:
    """
    DETERMINISTIC rule-based requirements parser (NO LLM)
    Replaces Groq LLM with regex patterns and keyword matching
    
    Args:
        text: Requirement text to parse
        device_type: Device type (ventilator, dialysis, pulse_ox)
    
    Returns:
        Structured requirement dictionary matching Requirement schema
    """
    # Extract all fields deterministically
    req_type = classify_requirement_type(text)
    fr_or_nfr = classify_fr_or_nfr(text, req_type)
    min_val, max_val, unit = extract_numbers_with_unit(text)
    response_time = extract_response_time(text)
    subsystem = extract_subsystem(text, device_type)
    priority = extract_priority(text)
    severity = extract_severity(text)
    probability = extract_probability(text)
    standard, clause = extract_standard(text)
    interface, protocol = extract_interface(text)
    title = generate_title(text, req_type)
    
    # Extract parameter name from text
    parameter = None
    if req_type == 'performance':
        # Look for common parameters
        param_keywords = ['voltage', 'current', 'temperature', 'pressure', 'flow', 'accuracy', 'frequency']
        for keyword in param_keywords:
            if keyword in text.lower():
                parameter = keyword.capitalize()
                break
    
    # Determine verification method based on type
    verification_method = 'test'
    if req_type == 'regulatory':
        verification_method = 'inspection'
    elif req_type == 'interface':
        verification_method = 'test'
    elif req_type == 'safety':
        verification_method = 'analysis'
    
    # Extract hazard description for safety requirements
    hazard = None
    if req_type == 'safety':
        # Look for hazard description after keywords
        hazard_pattern = r'(?:hazard|risk):\s*([^.]+)'
        hazard_match = re.search(hazard_pattern, text, re.IGNORECASE)
        if hazard_match:
            hazard = hazard_match.group(1).strip()
    
    # Build result dictionary
    result = {
        "fr_or_nfr": fr_or_nfr,
        "type": req_type,
        "title": title,
        "subsystem": subsystem,
        "parameter": parameter,
        "min_value": min_val,
        "max_value": max_val,
        "unit": unit,
        "response_time_ms": response_time,
        "interface": interface,
        "protocol": protocol,
        "hazard": hazard,
        "severity": severity,
        "probability": probability,
        "standard": standard,
        "clause": clause,
        "priority": priority,
        "verification_method": verification_method,
        "verification_description": f"Verify {title.lower()} through {verification_method}"
    }
    
    return result
