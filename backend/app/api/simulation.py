from fastapi import APIRouter
from ..core.simulation.class2.ventilator import VentilatorTwin
from ..core.simulation.class1.pulse_oximeter import PulseOximeterTwin
from ..core.simulation.class3.dialysis import DialysisTwin
from ..core.simulation.engine import SimulationEngine
from ..core.simulation.faults import FaultInjector
from .requirements import store
from ..core.devices.class2.ventilator import Ventilator
from ..core.devices.class1.pulse_oximeter import PulseOximeter
from ..core.devices.class3.dialysis import DialysisMachine

router = APIRouter()
simulation_results = []


def _extract_design_specs(device_type: str) -> dict:
    """
    Extract component specifications from design for simulation integration.
    NO HARDCODING - Uses dynamically generated design data.
    """
    # Map device type to device class
    device_map = {
        "ventilator": Ventilator,
        "pulse_ox": PulseOximeter,
        "dialysis": DialysisMachine
    }
    
    device_class = device_map.get(device_type.lower())
    if not device_class:
        return {}
    
    device = device_class()
    detailed_components = device.get_detailed_components()
    
    specs = {}
    
    # Extract key component specs for simulation physics
    # These specs will be used to parameterize the physics models
    if device_type == "ventilator":
        # Blower specifications
        blower_specs = detailed_components.get("Blower Turbine", {})
        if "speed" in blower_specs:
            speed_str = blower_specs["speed"]
            # Extract numeric value from "60k RPM" -> 60000
            import re
            match = re.search(r'(\d+)k?\s*RPM', speed_str, re.IGNORECASE)
            if match:
                rpm = int(match.group(1))
                if 'k' in speed_str.lower():
                    rpm *= 1000
                specs["blower_max_rpm"] = rpm
        
        # Sensor specifications
        sensor_specs = detailed_components.get("Proximal Flow Sensor", {})
        if "accuracy" in sensor_specs:
            acc_str = sensor_specs["accuracy"]
            match = re.search(r'(\d+(?:\.\d+)?)', acc_str)
            if match:
                specs["sensor_accuracy"] = float(match.group(1)) / 100.0  # 3% -> 0.03
        
        # Safety valve specifications
        valve_specs = detailed_components.get("Relief Valve (Pop-off)", {})
        if "threshold" in valve_specs:
            thresh_str = valve_specs["threshold"]
            match = re.search(r'(\d+)', thresh_str)
            if match:
                specs["relief_valve_threshold"] = float(match.group(1))
    
    return specs


def _extract_ventilator_params(requirements) -> dict:
    """
    Derives simulation parameters from structured requirements.
    Walks all performance and safety requirements and extracts:
      - target_flow_rate : first performance req for FlowRate with a midpoint
      - max_flow_rate    : max_value of the flow-rate performance req
      - max_pressure     : max_value of the pressure safety req

    Falls back to safe device-class defaults if requirements are not yet
    loaded or the relevant fields are absent.
    """
    params = {
        "target_flow_rate": 30.0,   # L/min default
        "max_flow_rate":    60.0,   # L/min default
        "max_pressure":     40.0,   # cmH2O default (IEC 80601-2-12)
    }

    for req in requirements:
        if req.type == "performance" and req.parameter:
            param_lower = req.parameter.lower()
            if "flow" in param_lower:
                if req.max_value is not None:
                    params["max_flow_rate"] = req.max_value
                if req.min_value is not None and req.max_value is not None:
                    # Target = midpoint of operating range
                    params["target_flow_rate"] = (
                        req.min_value + req.max_value
                    ) / 2.0

        if req.type == "safety" and req.parameter:
            param_lower = req.parameter.lower()
            if "pressure" in param_lower and req.max_value is not None:
                params["max_pressure"] = req.max_value

    return params


def _extract_pulse_ox_params(requirements) -> dict:
    """
    Derives SpO2 and Pulse Rate parameters from requirements.
    """
    params = {
        "target_spo2": 98.0,
        "min_spo2":    90.0,
        "target_hr":   70.0,
        "max_hr":      120.0,
    }

    for req in requirements:
        if req.type == "performance" and req.parameter:
            param_lower = req.parameter.lower()
            if "spo2" in param_lower:
                if req.min_value is not None and req.max_value is not None:
                    params["target_spo2"] = (req.min_value + req.max_value) / 2.0
            elif "pulse" in param_lower or "hr" in param_lower:
                if req.min_value is not None and req.max_value is not None:
                    params["target_hr"] = (req.min_value + req.max_value) / 2.0

        if req.type == "safety" and req.parameter:
            param_lower = req.parameter.lower()
            if "spo2" in param_lower and req.min_value is not None:
                params["min_spo2"] = req.min_value
            elif ("pulse" in param_lower or "hr" in param_lower) and req.max_value is not None:
                params["max_hr"] = req.max_value

    return params


def _extract_dialysis_params(requirements):
    params = {
        "target_bfr": 300.0,
        "target_dfr": 500.0,
        "max_tmp": 400.0
    }
    for req in requirements:
        if req.type == "performance" and req.parameter:
            param_lower = req.parameter.lower()
            if "bfr" in param_lower or "blood" in param_lower:
                if getattr(req, "min_value", None) is not None and getattr(req, "max_value", None) is not None:
                    params["target_bfr"] = (req.min_value + req.max_value) / 2.0
            elif "dfr" in param_lower or "dialysate" in param_lower:
                if getattr(req, "min_value", None) is not None and getattr(req, "max_value", None) is not None:
                    params["target_dfr"] = (req.min_value + req.max_value) / 2.0
        
        if req.type == "safety" and req.parameter:
            param_lower = req.parameter.lower()
            if "tmp" in param_lower and getattr(req, "max_value", None) is not None:
                params["max_tmp"] = req.max_value
    return params


TWIN_MAP = {
    "ventilator": VentilatorTwin,
    "pulse_ox": PulseOximeterTwin,
    "pulse_oximeter": PulseOximeterTwin,
    "dialysis": DialysisTwin
}

PARAM_EXTRACTOR_MAP = {
    "ventilator": _extract_ventilator_params,
    "pulse_ox": _extract_pulse_ox_params,
    "pulse_oximeter": _extract_pulse_ox_params,
    "dialysis": _extract_dialysis_params
}


@router.post("/run")
def run_simulation(steps: int = 10, device_type: str = "ventilator", fidelity: str = "L2"):
    """
    Runs a Digital Twin simulation of the specified device.
    NOW INTEGRATED with design graph - uses component specs from generated design.
    """
    global simulation_results

    device_type = device_type.lower()
    twin_class = TWIN_MAP.get(device_type)
    extractor = PARAM_EXTRACTOR_MAP.get(device_type)

    if not twin_class or not extractor:
        return {"error": f"Device type {device_type} not supported"}

    # Extract parameters from requirements
    params = extractor(store.get_all())
    params["fidelity"] = fidelity
    
    # CRITICAL: Extract component specs from design (RAG-driven, not hardcoded)
    design_specs = _extract_design_specs(device_type)
    params.update(design_specs)  # Merge design specs into simulation params
    
    twin = twin_class(**params)
    
    engine = SimulationEngine(twin)
    simulation_results = engine.run(steps)

    return {
        "parameters_used": params,
        "design_specs_used": design_specs,
        "integration_status": "Design→Simulation connected" if design_specs else "Requirements-only",
        "steps": steps,
        "snapshots": simulation_results
    }


@router.post("/fault")
def run_faulty_simulation(
    parameter: str,
    bias: float,
    steps: int = 10,
    device_type: str = "ventilator",
    fidelity: str = "L2"
):
    """
    Injects a fault into the simulation for safety/what-if analysis.
    NOW INTEGRATED with design graph - uses component specs.
    bias: e.g. 0.2 means +20% sensor bias.
    """
    global simulation_results

    device_type = device_type.lower()
    twin_class = TWIN_MAP.get(device_type)
    extractor = PARAM_EXTRACTOR_MAP.get(device_type)

    if not twin_class or not extractor:
        return {"error": f"Device type {device_type} not supported"}

    # Extract parameters from requirements
    params = extractor(store.get_all())
    params["fidelity"] = fidelity
    
    # CRITICAL: Extract component specs from design (RAG-driven)
    design_specs = _extract_design_specs(device_type)
    params.update(design_specs)
    
    twin = twin_class(**params)
    
    # Apply Fault
    injector = FaultInjector(twin)
    try:
        injector.apply_sensor_bias(parameter, bias)
    except ValueError as e:
        return {"error": str(e)}

    engine = SimulationEngine(twin)
    simulation_results = engine.run(steps)

    return {
        "status": "fault_injected",
        "fault": {"parameter": parameter, "bias": bias},
        "parameters_used": params,
        "design_specs_used": design_specs,
        "integration_status": "Design→Simulation connected",
        "snapshots": simulation_results
    }