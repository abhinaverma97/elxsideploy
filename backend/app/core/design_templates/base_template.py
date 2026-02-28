"""
Base Design Template - Rule-based design generation (NO LLM)
All design decisions are deterministic and traceable
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class SafetyClassification(Enum):
    """IEC 62304 Software Safety Classification"""
    CLASS_A = "Class A"  # No injury or damage
    CLASS_B = "Class B"  # Non-serious injury
    CLASS_C = "Class C"  # Death or serious injury


class RiskLevel(Enum):
    """ISO 14971 Risk Levels"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    UNACCEPTABLE = "Unacceptable"


@dataclass
class Subsystem:
    """Subsystem definition with traceability"""
    id: str
    name: str
    description: str
    iec_62304_section: str
    iso_14971_hazards: List[str]
    required_components: List[str]
    interfaces: List[str]
    safety_requirements: List[str]
    test_requirements: List[str]


@dataclass
class ComponentSpec:
    """Component specification with requirements"""
    category: str
    description: str
    required_specs: Dict[str, Any]
    optional_specs: Dict[str, Any] = field(default_factory=dict)
    safety_critical: bool = False
    medical_grade_required: bool = False
    certifications_required: List[str] = field(default_factory=list)


@dataclass
class DesignRequirements:
    """Structured requirements (NO LLM parsing)"""
    # Basic specs
    device_type: str = "ventilator"
    device_class: str = "Class II"  # Class I, Class II, Class III
    
    # Electrical
    input_voltage: float = 120.0
    max_current: float = 5.0
    power_budget_w: float = 600.0
    
    # Performance
    sensor_accuracy_percent: float = 2.0
    response_time_ms: float = 100.0
    operating_frequency: Optional[float] = None
    
    # Environmental
    operating_temp_min: float = 15.0
    operating_temp_max: float = 35.0
    humidity_max: float = 85.0
    
    # Compliance
    compliance_standards: List[str] = field(default_factory=lambda: ["IEC 60601-1", "ISO 14971"])
    medical_grade: bool = True
    region: str = "Global"
    
    # Patient safety
    patient_contact: bool = True
    critical_function: bool = True


class DesignTemplate:
    """Base template for deterministic design generation"""
    
    def __init__(self, device_type: str, device_class: str):
        self.device_type = device_type
        self.device_class = device_class
        self.subsystems: List[Subsystem] = []
        self.component_specs: Dict[str, ComponentSpec] = {}
        
    def classify_safety(self, requirements: DesignRequirements) -> SafetyClassification:
        """
        IEC 62304 software safety classification (deterministic rules)
        """
        if requirements.critical_function and requirements.patient_contact:
            return SafetyClassification.CLASS_C
        elif requirements.patient_contact or requirements.critical_function:
            return SafetyClassification.CLASS_B
        else:
            return SafetyClassification.CLASS_A
    
    def assess_risk(self, hazard: str, likelihood: str, severity: str) -> RiskLevel:
        """
        ISO 14971 risk assessment (deterministic matrix)
        """
        risk_matrix = {
            ("frequent", "catastrophic"): RiskLevel.UNACCEPTABLE,
            ("frequent", "critical"): RiskLevel.UNACCEPTABLE,
            ("frequent", "marginal"): RiskLevel.HIGH,
            ("occasional", "catastrophic"): RiskLevel.UNACCEPTABLE,
            ("occasional", "critical"): RiskLevel.HIGH,
            ("occasional", "marginal"): RiskLevel.MEDIUM,
            ("remote", "catastrophic"): RiskLevel.HIGH,
            ("remote", "critical"): RiskLevel.MEDIUM,
            ("remote", "marginal"): RiskLevel.LOW,
        }
        return risk_matrix.get((likelihood.lower(), severity.lower()), RiskLevel.HIGH)
    
    def define_subsystems(self, requirements: DesignRequirements) -> List[Subsystem]:
        """
        Define subsystems based on device type (must be overridden)
        """
        raise NotImplementedError("Subclasses must implement define_subsystems")
    
    def specify_components(self, subsystem: Subsystem, requirements: DesignRequirements) -> List[ComponentSpec]:
        """
        Specify required components for subsystem (must be overridden)
        """
        raise NotImplementedError("Subclasses must implement specify_components")
    
    def validate_design(self, design: Dict[str, Any], requirements: DesignRequirements) -> Dict[str, Any]:
        """
        Validate design against requirements (deterministic checks)
        """
        validations = {
            "power_budget": self._validate_power_budget(design, requirements),
            "compliance": self._validate_compliance(design, requirements),
            "safety": self._validate_safety(design, requirements),
            "electrical": self._validate_electrical(design, requirements)
        }
        
        all_passed = all(v["passed"] for v in validations.values())
        
        return {
            "passed": all_passed,
            "validations": validations,
            "errors": [v["error"] for v in validations.values() if not v["passed"]],
            "warnings": [v.get("warning", "") for v in validations.values() if v.get("warning")]
        }
    
    def _validate_power_budget(self, design: Dict, requirements: DesignRequirements) -> Dict:
        """Validate total power consumption"""
        # Calculate total power from component specifications
        total_power = 0
        for subsys_id, specs in design.get("component_specifications", {}).items():
            for spec in specs:
                power = spec.get("required_specs", {}).get("power_w", 0)
                total_power += power
        
        # Add 20% safety margin
        max_allowed = requirements.power_budget_w * 0.8
        
        passed = total_power <= max_allowed
        
        return {
            "passed": passed,
            "total_power": total_power,
            "max_allowed": max_allowed,
            "margin": max_allowed - total_power,
            "error": f"Power budget exceeded: {total_power}W > {max_allowed}W" if not passed else None
        }
    
    def _validate_compliance(self, design: Dict, requirements: DesignRequirements) -> Dict:
        """Validate regulatory compliance"""
        required_standards = set(requirements.compliance_standards)
        design_standards = set(design.get("standards_referenced", []))
        
        missing = required_standards - design_standards
        
        passed = len(missing) == 0
        
        return {
            "passed": passed,
            "required": list(required_standards),
            "covered": list(design_standards),
            "missing": list(missing),
            "error": f"Missing standards: {', '.join(missing)}" if not passed else None
        }
    
    def _validate_safety(self, design: Dict, requirements: DesignRequirements) -> Dict:
        """Validate safety requirements"""
        safety_class = self.classify_safety(requirements)
        
        # Count safety-critical components from component specifications
        critical_count = 0
        total_count = 0
        
        for subsys_id, specs in design.get("component_specifications", {}).items():
            for spec in specs:
                total_count += 1
                if spec.get("safety_critical", False):
                    critical_count += 1
        
        # For Class C devices, we need good coverage of safety-critical components
        passed = True
        if safety_class == SafetyClassification.CLASS_C:
            # At least 30% of components should be safety-critical for Class C
            if total_count > 0 and (critical_count / total_count) < 0.3:
                passed = False
        
        return {
            "passed": passed,
            "safety_class": safety_class.value,
            "critical_components": critical_count,
            "total_components": total_count,
            "error": "Insufficient safety-critical component coverage for Class C device" if not passed else None,
            "warning": "Consider adding more safety monitoring for Class C device" if safety_class == SafetyClassification.CLASS_C and critical_count < 5 else None
        }
    
    def _validate_electrical(self, design: Dict, requirements: DesignRequirements) -> Dict:
        """Validate electrical specifications"""
        # Find power supply component from component specifications
        psu_found = False
        psu_rating = requirements.max_current  # Use requirement as fallback
        
        for subsys_id, specs in design.get("component_specifications", {}).items():
            for spec in specs:
                category = spec.get("category", "")
                if "power" in category.lower() or "ac_dc" in category.lower() or "converter" in category.lower():
                    psu_found = True
                    # Try to get current rating from specs
                    required_specs = spec.get("required_specs", {})
                    psu_rating = required_specs.get("output_current", requirements.max_current)
                    break
            if psu_found:
                break
        
        # Calculate total current (estimate based on power budget)
        total_power = 0
        for subsys_id, specs in design.get("component_specifications", {}).items():
            for spec in specs:
                power = spec.get("required_specs", {}).get("power_w", 0)
                total_power += power
        
        # Estimate current from power (P = V * I)
        voltage = requirements.input_voltage
        total_current = total_power / voltage if voltage > 0 else 0
        
        # 80% derating for reliability
        max_safe_current = psu_rating * 0.8
        
        passed = total_current <= max_safe_current
        
        return {
            "passed": passed,
            "psu_found": psu_found,
            "total_current": round(total_current, 2),
            "psu_rating": psu_rating,
            "max_safe_current": round(max_safe_current, 2),
            "margin": round(max_safe_current - total_current, 2),
            "derating": 0.8,
            "error": f"Current draw {total_current:.2f}A exceeds PSU rating {max_safe_current:.2f}A" if not passed else None
        }
    
    def generate_full_design(self, requirements: DesignRequirements) -> Dict[str, Any]:
        """
        Generate complete design (NO LLM - pure rules)
        """
        # 1. Classify safety
        safety_class = self.classify_safety(requirements)
        
        # 2. Define subsystems
        subsystems = self.define_subsystems(requirements)
        
        # 3. Specify components for each subsystem
        all_component_specs = {}
        for subsystem in subsystems:
            specs = self.specify_components(subsystem, requirements)
            all_component_specs[subsystem.id] = specs
        
        # 4. Build design structure
        design = {
            "device_type": self.device_type,
            "device_class": self.device_class,
            "safety_classification": safety_class.value,
            "requirements": requirements.__dict__,
            "subsystems": [
                {
                    "id": s.id,
                    "name": s.name,
                    "description": s.description,
                    "iec_62304_section": s.iec_62304_section,
                    "hazards": s.iso_14971_hazards,
                    "interfaces": s.interfaces,
                    "safety_requirements": s.safety_requirements,
                    "test_requirements": s.test_requirements
                }
                for s in subsystems
            ],
            "component_specifications": {
                subsys_id: [
                    {
                        "category": spec.category,
                        "description": spec.description,
                        "required_specs": spec.required_specs,
                        "optional_specs": spec.optional_specs,
                        "safety_critical": spec.safety_critical,
                        "medical_grade": spec.medical_grade_required,
                        "certifications": spec.certifications_required
                    }
                    for spec in specs
                ]
                for subsys_id, specs in all_component_specs.items()
            },
            "standards_referenced": requirements.compliance_standards,
            "generated_at": None,  # Will be set by caller
            "generation_method": "template-based (deterministic)"
        }
        
        # 5. Validate design
        validation_results = self.validate_design(design, requirements)
        design["validation"] = validation_results
        
        if not validation_results["passed"]:
            design["status"] = "validation_failed"
            design["errors"] = validation_results["errors"]
        else:
            design["status"] = "validated"
        
        return design
