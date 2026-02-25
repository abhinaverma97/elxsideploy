import os
import json
from groq import Groq
from fastapi import APIRouter
from ..core.devices.class2.ventilator import Ventilator
from ..core.devices.class1.pulse_oximeter import PulseOximeter
from ..core.devices.class3.dialysis import DialysisMachine
from ..core.design_graph.builder import DesignGraphBuilder
from .requirements import store

router = APIRouter()
design_graph = None

DEVICE_MAP = {
    "ventilator": Ventilator,
    "pulse_ox": PulseOximeter,
    "dialysis": DialysisMachine
}

@router.post("/build")
def build_design(device_type: str = "ventilator"):
    global design_graph
    
    device_class = DEVICE_MAP.get(device_type.lower())
    if not device_class:
        return {"error": f"Device type {device_type} not supported"}
    
    device = device_class()

    # Build design graph (Industry-Grade)
    requirements = store.get_all()
    builder = DesignGraphBuilder(device)
    design_graph = builder.build(requirements)

    architecture_nodes = []
    for name, node in design_graph.subsystems.items():
        architecture_nodes.append({
            "id": name,
            "name": name,
            "type": "subsystem",
            "components": node.components if hasattr(node, "components") else [],
            "detailed_components": node.detailed_components if hasattr(node, "detailed_components") else {},
            "software_stack": node.software_stack if hasattr(node, "software_stack") else []
        })

    interfaces_list = [
        {"source": i.source, "target": i.target, "signal": i.signal} for i in design_graph.interfaces
    ]

    return {
        "device": device.device_name,
        "class": device.device_class,
        "subsystems": list(design_graph.subsystems),
        "raw": {
            "architecture": architecture_nodes,
            "interfaces": interfaces_list
        },
        "interfaces": interfaces_list
    }

@router.post("/generate-details")
def generate_design_details(device_type: str = "ventilator"):
    reqs = store.get_all()

    def req_context(r):
        lines = [f"- [{r.id}] {r.title}: {r.description}"]
        if r.fr_text:
            lines.append(f"  Functional Requirement: {r.fr_text}")
        if r.nfr_text:
            lines.append(f"  Non-Functional Requirement: {r.nfr_text}")
        return "\n".join(lines)

    reqs_text = "\n".join([req_context(r) for r in reqs])
    
    prompt = f"""
    You are an expert Systems Engineer designing a Class II/III Medical Device: {device_type.upper()}.
    
    Here are the system requirements:
    {reqs_text}
    
    Generate a comprehensive, highly technical system design specification in STRICT JSON format. 
    DO NOT wrap the response in markdown blocks like ```json. Return ONLY valid JSON.
    
    The JSON must follow this exact structure:
    {{
      "Architecture": {{
        "SystemOverview": "Detailed text...",
        "Subsystems": [
           {{"name": "...", "components": ["...", "..."]}}
        ],
        "MechanicalAssemblies": [
           {{"name": "...", "details": "..."}}
        ],
        "MechanicalOverview": "Text..."
      }},
      "Hardware": {{
        "ComponentsTable": [
           {{"partNumber": "...", "manufacturer": "...", "package": "...", "specifications": "...", "cost": "..."}}
        ],
        "PowerTree": [
           {{"rail": "...", "regulator": "...", "load": "..."}}
        ]
      }},
      "Software": {{
        "SoftwareModules": [
           {{"name": "...", "safetyClass": "...", "language": "...", "rtosDependency": "...", "io": "..."}}
        ],
        "RTOSTasks": [
           {{"name": "...", "priority": "...", "period": "...", "description": "..."}}
        ],
        "IPCMechanisms": "Text..."
      }},
      "Interfaces": {{
        "SystemInterfaces": [
           {{"name": "...", "protocol": "...", "speed": "...", "voltage": "..."}}
        ],
        "Signals": [
           {{"name": "...", "type": "Analog/Digital", "range": "...", "resolution": "...", "rate": "...", "unit": "..."}}
        ],
        "DataPowerFlows": [
           {{"flow": "...", "medium": "...", "nominalValue": "..."}}
        ],
        "InterfaceMap": [
           {{"bus": "...", "master": "...", "slaves": ["...", "..."]}}
        ]
      }},
      "Risks": {{
        "RiskAnalysis": [
           {{"hazard": "...", "severity": "...", "probability": "...", "riskLevel": "...", "mitigation": "..."}}
        ],
        "StandardsCompliance": [
           {{"standard": "...", "clause": "...", "requirement": "..."}}
        ]
      }},
      "Connections": [
        {{"type": "ConnectsTo", "from": "...", "to": "..."}}
      ],
      "Environment": {{
        "OperatingConditions": [
           {{"parameter": "...", "spec": "..."}}
        ]
      }}
    }}
    """
    
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        return {"error": "GROQ_API_KEY environment variable is not set."}
        
    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        content = response.choices[0].message.content
        

        # Clean markdown wrappers if present
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
            
        if content.endswith("```"):
            content = content[:-3]
            
        try:
            import json_repair
            parsed_json = json_repair.loads(content.strip())
        except ImportError:
            # Fallback if json_repair isn't available
            parsed_json = json.loads(content.strip())
            
        return {"data": parsed_json}
    except Exception as e:
        return {"error": f"Failed to generate or parse response: {str(e)}", "raw": content if 'content' in locals() else ""}