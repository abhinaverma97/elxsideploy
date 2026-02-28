"""
Template-based design generation system (NO LLM)
Industry-grade deterministic design generation
"""
from .base_template import DesignTemplate, DesignRequirements, SafetyClassification, RiskLevel
from .ventilator_template import VentilatorTemplate
from .dialysis_template import DialysisTemplate

__all__ = [
    'DesignTemplate',
    'DesignRequirements', 
    'SafetyClassification',
    'RiskLevel',
    'VentilatorTemplate',
    'DialysisTemplate'
]

