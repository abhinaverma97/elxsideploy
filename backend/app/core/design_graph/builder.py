from collections import defaultdict
from .graph import DesignGraph
from .nodes import SubsystemNode


class DesignGraphBuilder:
    """
    Builds a DesignGraph deterministically from structured requirements.
    Incorporates industry-grade metadata from the MedicalDevice model.
    """

    def __init__(self, device):
        self.device = device

    def build(self, requirements):
        """
        requirements: List[Requirement]
        """
        graph = DesignGraph(device_name=self.device.device_name)

        # Step 1: Group requirements by subsystem
        subsystem_requirements = self._group_by_subsystem(requirements)

        # Step 2: Get detailed architecture and metadata
        arch = self.device.get_architecture()
        all_details = self.device.get_detailed_components()
        software_stack = self.device.get_software_stack()
        safety_components = self.device.get_standard_safety_components()

        # Step 3: Create subsystem nodes with minute details
        all_subsystems = set(subsystem_requirements.keys()) | set(arch.keys())

        for subsystem in all_subsystems:
            reqs = subsystem_requirements.get(subsystem, [])
            components = arch.get(subsystem, []) or []

            # Injection logic for safety (case-insensitive, robust to empty lists)
            if any(k in (subsystem or "").lower() for k in ("control", "safety")):
                if components and isinstance(components[0], dict):
                    existing = {c.get("name") for c in components}
                    for sc in safety_components:
                        if sc not in existing:
                            components.append({"name": sc, "category": "Hardware (Electronic)"})
                else:
                    # components may be a list of strings; preserve order and uniqueness
                    combined = list(components) + list(safety_components)
                    components = list(dict.fromkeys(combined))

            # Deterministic synthesis: add components driven by requirements
            synthesized = []
            for r in reqs:
                # Performance requirements -> sensor / measurement component
                if r.type == "performance" and r.parameter:
                    sensor_name = f"{r.parameter} Sensor"
                    synthesized.append({"name": sensor_name, "category": "Hardware (Sensor)"})

                # Functional requirements that imply control -> control loop + software
                if r.type == "functional":
                    desc = (r.description or "") + " " + (r.fr_text or "")
                    if any(k in desc.lower() for k in ("control", "maintain", "regulat", "stabiliz")):
                        synthesized.append({"name": "Control Loop", "category": "Application Software"})
                        synthesized.append({"name": "Control Algorithm", "category": "Embedded Software"})

                # Interface requirements may imply protocol handlers
                if r.type == "interface" and r.protocol:
                    handler = f"{r.protocol} Interface"
                    synthesized.append({"name": handler, "category": "Hardware/Software Interface"})

            # Merge synthesized components into components list, preserving order and uniqueness
            final_components = []
            # normalize existing components to dict form
            for c in components:
                if isinstance(c, dict):
                    final_components.append(c)
                else:
                    final_components.append({"name": str(c), "category": "Unknown"})
            for s in synthesized:
                if s.get("name") not in {c.get("name") for c in final_components}:
                    final_components.append(s)

            components = final_components

            # Filter details: support dict-lists (now all dicts)
            subsystem_details = {c.get("name"): all_details.get(c.get("name"), {}) for c in components}
            
            # Map software
            subsystem_software = [s for s in software_stack if subsystem.lower() in s.get("name", "").lower() or subsystem.lower() in s.get("layer", "").lower()]

            node = self._create_subsystem_node(subsystem, reqs, components, subsystem_details, subsystem_software)
            graph.add_subsystem(node)

        # Step 4: Infer interfaces (Requirements-driven)
        self._infer_interfaces(graph, requirements)

        # Step 5: Add default interfaces from device model (to ensureArrows always show)
        default_ifaces = self.device.get_default_interfaces()
        existing_pairs = {(i.source, i.target) for i in graph.interfaces}
        for d_iface in default_ifaces:
            if (d_iface['source'], d_iface['target']) not in existing_pairs:
                graph.connect(
                    source=d_iface['source'],
                    target=d_iface['target'],
                    signal=d_iface['signal']
                )

        return graph


    def _group_by_subsystem(self, requirements):
        grouped = defaultdict(list)
        for req in requirements:
            if req.subsystem:
                grouped[req.subsystem].append(req)
        return grouped

    def _create_subsystem_node(self, subsystem, requirements, components, details, software):
        inputs = []
        outputs = []
        for req in requirements:
            if req.type == "interface":
                if req.parameter:
                    inputs.append(req.parameter)
            elif req.type in ["functional", "performance"]:
                if req.parameter:
                    outputs.append(req.parameter)

        return SubsystemNode(
            name=subsystem,
            inputs=list(set(inputs)),
            outputs=list(set(outputs)),
            components=components,
            detailed_components=details,
            software_stack=software
        )

    def _infer_interfaces(self, graph, requirements):
        for req in requirements:
            if req.type != "interface":
                continue
            if not req.interface:
                continue
            source, target = self._parse_interface(req.interface)
            signal = req.parameter or "Generic"
            graph.connect(source=source, target=target, signal=signal)

    def _parse_interface(self, interface_str):
        try:
            source, target = interface_str.split("->")
            return source.strip(), target.strip()
        except ValueError:
            return "Unknown", "Unknown"