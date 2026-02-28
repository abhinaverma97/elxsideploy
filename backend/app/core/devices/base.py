from typing import List, Dict, Any

class MedicalDevice:
    """
    Base class for medical device design models.
    Implements IEC 62304 design hierarchy:
    - §5.3: System Architecture (get_default_subsystems, get_default_interfaces)
    - §5.4: Subsystem Design (get_architecture, get_software_stack)
    - §5.5: Detailed Design (get_detailed_components, get_bom, get_pcb_components, get_firmware_architecture)
    
    IMPORTANT: All detailed design artifacts are now DYNAMICALLY GENERATED using RAG-driven
    design generator. No hardcoded BOMs, PCB layouts, or firmware architectures.
    """
    device_name: str
    device_class: str
    
    def __init__(self):
        """Initialize with dynamic design generator for RAG-driven component selection."""
        from ..design_graph.dynamic_generator import DynamicDesignGenerator
        self._dynamic_generator = None
        self._cached_bom = None
        self._cached_pcb = None
        self._cached_firmware = None
        self._cached_verification = None
    
    def _get_generator(self):
        """Lazy-load dynamic generator to avoid circular imports."""
        if self._dynamic_generator is None:
            from ..design_graph.dynamic_generator import DynamicDesignGenerator
            self._dynamic_generator = DynamicDesignGenerator(
                device_type=self.device_name,
                device_class=self.device_class
            )
        return self._dynamic_generator

    # ═══════════════════════════════════════════════════════════════════════
    # IEC 62304 §5.3: SYSTEM ARCHITECTURE
    # ═══════════════════════════════════════════════════════════════════════

    def get_default_subsystems(self) -> List[str]:
        """Returns top-level functional subsystems (system architecture)."""
        raise NotImplementedError

    def get_default_interfaces(self) -> List[Dict[str, str]]:
        """Returns signal/data flows between subsystems."""
        return []

    def get_design_constraints(self) -> Dict[str, Any]:
        """Returns system-level constraints (performance, safety limits)."""
        raise NotImplementedError

    # ═══════════════════════════════════════════════════════════════════════
    # IEC 62304 §5.4: SUBSYSTEM/MODULE DESIGN
    # ═══════════════════════════════════════════════════════════════════════

    def get_architecture(self) -> Dict[str, List[str]]:
        """Returns components/modules within each subsystem."""
        return {s: [] for s in self.get_default_subsystems()}

    def get_software_stack(self) -> List[Dict[str, str]]:
        """Returns software architecture layers (HAL, RTOS, App)."""
        return []

    def get_standard_safety_components(self) -> List[str]:
        """Returns mandatory safety components per device class."""
        if self.device_class in ["Class II", "Class III"]:
            return ["Safety MCU", "Watchdog Timer", "Isolated Power Supply"]
        return []

    # ═══════════════════════════════════════════════════════════════════════
    # IEC 62304 §5.5: DETAILED DESIGN
    # ═══════════════════════════════════════════════════════════════════════

    def get_detailed_components(self) -> Dict[str, Dict[str, Any]]:
        """
        Returns component-level specifications.
        Format: {"ComponentName": {"type": "MCU", "model": "STM32H7", ...}}
        """
        return {}

    def get_bom(self, requirements: List[Any] = None) -> List[Dict[str, Any]]:
        """
        Returns Bill of Materials (BOM) with part numbers and suppliers.
        IEC 62304 §5.5: Detailed design documentation requirement.
        DYNAMICALLY GENERATED using RAG queries to knowledge base.
        Format: [{"item": 1, "part_number": "...", "description": "...", 
                  "manufacturer": "...", "quantity": 1, "unit_cost": "..."}]
        """
        if self._cached_bom is None and requirements:
            generator = self._get_generator()
            subsystems = self.get_default_subsystems()
            self._cached_bom = generator.generate_bom(subsystems, requirements)
        return self._cached_bom or []

    def get_pcb_components(self, requirements: List[Any] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Returns PCB-level component placement by subsystem.
        DYNAMICALLY GENERATED from BOM using RAG for footprint data.
        Format: {"SubsystemName": [{"reference": "U1", "part": "...", 
                                      "footprint": "...", "value": "..."}]}
        """
        if self._cached_pcb is None and requirements:
            generator = self._get_generator()
            subsystems = self.get_default_subsystems()
            bom = self.get_bom(requirements)
            self._cached_pcb = generator.generate_pcb_components(subsystems, bom)
        return self._cached_pcb or {}

    def get_firmware_architecture(self, requirements: List[Any] = None) -> Dict[str, Any]:
        """
        Returns firmware/software module structure.
        IEC 62304 §5.4.4: Software unit specification.
        DYNAMICALLY GENERATED based on subsystems and safety requirements.
        Format: {"rtos": "FreeRTOS", "tasks": [...], "modules": [...], 
                 "interrupts": [...]}
        """
        if self._cached_firmware is None and requirements:
            generator = self._get_generator()
            subsystems = self.get_default_subsystems()
            self._cached_firmware = generator.generate_firmware_architecture(subsystems, requirements)
        return self._cached_firmware or {}

    def get_design_verification_plan(self, requirements: List[Any] = None) -> List[Dict[str, str]]:
        """
        Returns design verification plan per FDA 21 CFR 820.30(g).
        DYNAMICALLY GENERATED from requirements and standards using RAG.
        Format: [{"design_element": "...", "verification_method": "...", 
                  "acceptance_criteria": "...", "iec_62304_ref": "..."}]
        """
        if self._cached_verification is None and requirements:
            generator = self._get_generator()
            subsystems = self.get_default_subsystems()
            self._cached_verification = generator.generate_verification_plan(subsystems, requirements)
        return self._cached_verification or []
