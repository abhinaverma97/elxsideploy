"""
Medical Device Certification Validation Module

Validates component compliance with medical device standards:
- IEC 60601-1 (Medical electrical equipment)
- ISO 13485 (Quality management)
- FDA 21 CFR Part 820 (Quality system regulation)
- ISO 14971 (Risk management)
- IEC 62304 (Software lifecycle)

Author: Medical Digital Twin System
"""

from typing import Dict, List, Any, Optional
from enum import Enum


class DeviceClass(Enum):
    """FDA Device Classification"""
    CLASS_I = "Class I (Low Risk)"
    CLASS_II = "Class II (Moderate Risk)"
    CLASS_III = "Class III (High Risk)"


class CertificationLevel(Enum):
    """Component certification levels"""
    COMMERCIAL = "Commercial Grade"
    INDUSTRIAL = "Industrial Grade"
    MEDICAL = "Medical Grade (IEC 60601-1)"
    IMPLANTABLE = "Implantable Grade (ISO 14708)"


class MedicalCertification:
    """
    Medical device certification validator.
    
    Ensures components meet required medical device standards
    and certifications for regulatory submission.
    """
    
    # Required certifications per device class
    REQUIRED_CERTIFICATIONS = {
        DeviceClass.CLASS_I: [
            "IEC 60601-1 (General safety)",
            "ISO 13485 (Quality management)",
            "RoHS compliance"
        ],
        DeviceClass.CLASS_II: [
            "IEC 60601-1 (General safety)",
            "IEC 60601-1-2 (EMC)",
            "IEC 60601-1-6 (Usability)",
            "ISO 13485 (Quality management)",
            "ISO 14971 (Risk management)",
            "RoHS compliance",
            "FDA 510(k) clearance"
        ],
        DeviceClass.CLASS_III: [
            "IEC 60601-1 (General safety)",
            "IEC 60601-1-2 (EMC)",
            "IEC 60601-1-6 (Usability)",
            "IEC 60601-1-8 (Alarms)",
            "ISO 13485 (Quality management)",
            "ISO 14971 (Risk management)",
            "IEC 62304 (Software)",
            "IEC 62366 (Usability engineering)",
            "RoHS compliance",
            "FDA PMA approval"
        ]
    }
    
    # Component-specific requirements
    COMPONENT_REQUIREMENTS = {
        "sensor": {
            "accuracy_class": "Medical grade (±1% FS or better)",
            "biocompatibility": "ISO 10993 if patient contact",
            "sterilization": "Compatible with autoclave/ETO if patient contact",
            "certifications": ["IEC 60601-1", "ISO 13485"]
        },
        "actuator": {
            "reliability": "MTBF > 10,000 hours",
            "safety_rating": "SIL 2 minimum (IEC 61508)",
            "certifications": ["IEC 60601-1", "ISO 13485"]
        },
        "power_supply": {
            "isolation": "2x MOPP (Means of Patient Protection)",
            "leakage_current": "< 100 µA (IEC 60601-1 §8.7.3)",
            "efficiency": "> 85% for thermal management",
            "certifications": ["IEC 60601-1", "IEC 60601-1-2", "ISO 13485"]
        },
        "controller": {
            "safety_integrity": "IEC 62304 Class C for life-supporting",
            "watchdog": "Required for safety-critical functions",
            "certifications": ["IEC 60601-1", "IEC 62304", "ISO 13485"]
        },
        "display": {
            "usability": "IEC 62366 + IEC 60601-1-6 compliant",
            "readability": "Minimum font size per ISO 9241-3",
            "alarm_display": "IEC 60601-1-8 compliant",
            "certifications": ["IEC 60601-1-6", "IEC 62366"]
        },
        "battery": {
            "chemistry": "Approved for medical (typically Li-ion)",
            "protection": "Overcharge/discharge protection required",
            "runtime": "Minimum 30 minutes backup (IEC 60601-1)",
            "certifications": ["IEC 60601-1", "UN 38.3", "ISO 13485"]
        },
        "communication": {
            "security": "Cybersecurity controls (FDA guidance)",
            "emc": "IEC 60601-1-2 EMC compliance",
            "wireless": "IEC 60601-1-2:2014 if wireless",
            "certifications": ["IEC 60601-1-2", "FDA Cybersecurity"]
        }
    }
    
    # Biocompatibility requirements (ISO 10993)
    BIOCOMPATIBILITY_TESTS = {
        "no_contact": [],
        "surface_contact": [
            "ISO 10993-5 (Cytotoxicity)",
            "ISO 10993-10 (Sensitization)",
            "ISO 10993-11 (Systemic toxicity)"
        ],
        "external_communicating": [
            "ISO 10993-5 (Cytotoxicity)",
            "ISO 10993-10 (Sensitization)",
            "ISO 10993-11 (Systemic toxicity)",
            "ISO 10993-12 (Sample preparation)"
        ],
        "implant": [
            "ISO 10993-5 (Cytotoxicity)",
            "ISO 10993-6 (Implantation)",
            "ISO 10993-10 (Sensitization)",
            "ISO 10993-11 (Systemic toxicity)",
            "ISO 10993-15 (Chemical characterization)",
            "ISO 10993-18 (Material characterization)"
        ]
    }
    
    @staticmethod
    def validate_component_certification(
        component_name: str,
        component_type: str,
        device_class: DeviceClass,
        patient_contact: bool = False
    ) -> Dict[str, Any]:
        """
        Validate component meets certification requirements.
        
        Args:
            component_name: Name of component
            component_type: Type (sensor, actuator, power, etc.)
            device_class: FDA device classification
            patient_contact: Whether component contacts patient
            
        Returns:
            Dict with certification validation results
        """
        # Get requirements for device class
        required_device_certs = MedicalCertification.REQUIRED_CERTIFICATIONS.get(
            device_class, []
        )
        
        # Get requirements for component type
        component_reqs = MedicalCertification.COMPONENT_REQUIREMENTS.get(
            component_type, {}
        )
        
        # Determine biocompatibility needs
        if patient_contact:
            bio_category = "surface_contact"  # Conservative assumption
            bio_tests = MedicalCertification.BIOCOMPATIBILITY_TESTS[bio_category]
        else:
            bio_tests = []
        
        # Compile all requirements
        all_requirements = {
            "component_name": component_name,
            "component_type": component_type,
            "device_class": device_class.value,
            "patient_contact": patient_contact,
            "required_certifications": component_reqs.get("certifications", []),
            "device_level_certifications": required_device_certs,
            "biocompatibility_tests": bio_tests,
            "specific_requirements": {
                k: v for k, v in component_reqs.items() 
                if k != "certifications"
            }
        }
        
        return all_requirements
    
    @staticmethod
    def check_iec_60601_compliance(
        component_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check IEC 60601-1 specific compliance requirements.
        
        Args:
            component_spec: Component specifications
            
        Returns:
            Dict with IEC 60601-1 compliance analysis
        """
        checks = {
            "standard": "IEC 60601-1:2005+AMD1:2012+AMD2:2020",
            "title": "Medical electrical equipment - General requirements",
            "checks": []
        }
        
        # Check leakage current (§8.7.3)
        if "leakage_current" in component_spec:
            leakage_ok = component_spec["leakage_current"] < 100  # µA
            checks["checks"].append({
                "clause": "§8.7.3",
                "requirement": "Leakage current < 100 µA",
                "actual": f"{component_spec['leakage_current']} µA",
                "compliant": leakage_ok
            })
        
        # Check isolation (§8.8)
        if "isolation" in component_spec:
            isolation_ok = "MOPP" in component_spec["isolation"]
            checks["checks"].append({
                "clause": "§8.8",
                "requirement": "Patient isolation (MOPP)",
                "actual": component_spec["isolation"],
                "compliant": isolation_ok
            })
        
        # Check enclosure rating (§8.9)
        if "ip_rating" in component_spec:
            # Medical devices typically need minimum IPX1 (drip-proof)
            ip_ok = component_spec["ip_rating"] >= "IPX1"
            checks["checks"].append({
                "clause": "§8.9",
                "requirement": "Minimum IPX1 ingress protection",
                "actual": component_spec["ip_rating"],
                "compliant": ip_ok
            })
        
        # Overall compliance
        if checks["checks"]:
            checks["overall_compliant"] = all(c["compliant"] for c in checks["checks"])
        else:
            checks["overall_compliant"] = "Not enough data"
        
        return checks
    
    @staticmethod
    def get_regulatory_pathway(
        device_class: DeviceClass,
        market: str = "US"
    ) -> Dict[str, Any]:
        """
        Get regulatory submission pathway.
        
        Args:
            device_class: FDA device class
            market: Target market (US, EU, etc.)
            
        Returns:
            Dict with regulatory pathway information
        """
        pathways = {
            "US": {
                DeviceClass.CLASS_I: {
                    "pathway": "510(k) Exempt or General Controls",
                    "submission": "May require 510(k) depending on device",
                    "timeline": "1-3 months if 510(k) required",
                    "requirements": ["QSR (21 CFR 820)", "Listing (21 CFR 807)"]
                },
                DeviceClass.CLASS_II: {
                    "pathway": "510(k) Premarket Notification",
                    "submission": "510(k) required",
                    "timeline": "3-12 months",
                    "requirements": [
                        "QSR (21 CFR 820)",
                        "510(k) submission",
                        "Substantial equivalence",
                        "Performance testing",
                        "Labeling review"
                    ]
                },
                DeviceClass.CLASS_III: {
                    "pathway": "PMA (Premarket Approval)",
                    "submission": "PMA required",
                    "timeline": "1-3 years",
                    "requirements": [
                        "QSR (21 CFR 820)",
                        "PMA submission",
                        "Clinical trials",
                        "Full safety/efficacy data",
                        "Manufacturing validation",
                        "Post-market surveillance"
                    ]
                }
            },
            "EU": {
                DeviceClass.CLASS_I: {
                    "pathway": "CE Mark - Self-certification",
                    "submission": "Technical file + self-declaration",
                    "timeline": "3-6 months",
                    "requirements": ["MDR compliance", "Technical documentation"]
                },
                DeviceClass.CLASS_II: {
                    "pathway": "CE Mark - Notified Body",
                    "submission": "Technical file + Notified Body assessment",
                    "timeline": "6-12 months",
                    "requirements": ["MDR compliance", "Notified Body audit"]
                },
                DeviceClass.CLASS_III: {
                    "pathway": "CE Mark - Full audit",
                    "submission": "Clinical evaluation + Notified Body",
                    "timeline": "1-2 years",
                    "requirements": ["MDR compliance", "Clinical data", "Full audit"]
                }
            }
        }
        
        pathway = pathways.get(market, {}).get(device_class, {})
        pathway["market"] = market
        pathway["device_class"] = device_class.value
        
        return pathway
    
    @staticmethod
    def generate_certification_checklist(
        device_class: DeviceClass,
        components: List[str]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive certification checklist.
        
        Args:
            device_class: FDA device class
            components: List of component types
            
        Returns:
            Dict with complete certification checklist
        """
        checklist = {
            "device_class": device_class.value,
            "device_level_certifications": 
                MedicalCertification.REQUIRED_CERTIFICATIONS[device_class],
            "component_certifications": {},
            "testing_required": [],
            "documentation_required": [
                "Design History File (DHF)",
                "Device Master Record (DMR)",
                "Device History Record (DHR)",
                "Risk Management File (ISO 14971)",
                "Software Documentation (IEC 62304)",
                "Usability Engineering File (IEC 62366)",
                "Clinical Evaluation Report",
                "Technical File"
            ]
        }
        
        # Component-specific certifications
        for component_type in components:
            if component_type in MedicalCertification.COMPONENT_REQUIREMENTS:
                checklist["component_certifications"][component_type] = \
                    MedicalCertification.COMPONENT_REQUIREMENTS[component_type]
        
        # Testing requirements
        checklist["testing_required"] = [
            "Electrical safety testing (IEC 60601-1)",
            "EMC testing (IEC 60601-1-2)",
            "Software validation (IEC 62304)",
            "Usability testing (IEC 62366)",
            "Risk analysis (ISO 14971)",
            "Performance testing (device-specific)",
            "Environmental testing (IEC 60601-1 §11)",
            "Mechanical safety (IEC 60601-1 §9)"
        ]
        
        return checklist
