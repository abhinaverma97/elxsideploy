import os
import json
from groq import Groq

# Subsystem hints by device type — helps the model suggest correct subsystems
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

_SYSTEM_PROMPT = """
You are a medical device systems engineer specializing in requirements engineering.
Your job is to parse a plain-English requirement statement and extract structured fields from it.

Return ONLY valid JSON — no markdown, no explanation, no wrapping backticks.

The JSON must follow this exact schema:
{
  "fr_or_nfr": "functional" | "non-functional",
  "type": "functional" | "performance" | "interface" | "safety" | "regulatory" | "environmental",
  "title": "Short title (max 10 words)",
  "subsystem": "Best matching subsystem from the provided list, or infer one",
  "parameter": "The measured/controlled parameter name, or null",
  "min_value": number or null,
  "max_value": number or null,
  "unit": "Unit string or null",
  "response_time_ms": integer or null,
  "interface": "Source -> Target format or null",
  "protocol": "Protocol name or null",
  "hazard": "Hazard description or null",
  "severity": "Low" | "Medium" | "High" | "Critical" | null,
  "probability": "Negligible" | "Remote" | "Occasional" | "Probable" | "Frequent" | null,
  "standard": "Standard name or null",
  "clause": "Clause ref or null",
  "priority": "SHALL" | "SHOULD" | "MAY",
  "verification_method": "test" | "simulation" | "analysis" | "inspection",
  "verification_description": "Short verification plan sentence"
}

Classification rules:
- FR (functional): what the system SHALL DO — actions, outputs, behaviors
- NFR (non-functional): constraints on HOW it does it — speed, accuracy, reliability, compliance, EMI
- type=performance for anything measureable (timing, accuracy, range)
- type=safety when a hazard or risk is explicitly mentioned
- type=regulatory when a standard/compliance is mentioned
- type=interface when communication between components is described
- type=environmental for temperature, humidity, storage conditions
"""


def analyze_requirement_text(text: str, device_type: str = "ventilator") -> dict:
    """
    Parse a plain-English requirement into a structured dict matching the Requirement schema.
    Uses GROQ_API_KEY_REQ environment variable.
    Returns structured dict or raises ValueError on failure.
    """
    api_key = os.environ.get("GROQ_API_KEY_REQ", "")
    # Fallback: try loading .env and then GROQ_API_KEY if specific var not set
    if not api_key:
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except Exception:
            pass
        api_key = os.environ.get("GROQ_API_KEY_REQ", "") or os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY_REQ or GROQ_API_KEY environment variable is not set.")

    subsystems = DEVICE_SUBSYSTEMS.get(device_type.lower(), [])
    subsystems_hint = ", ".join(subsystems) if subsystems else "infer from context"

    user_prompt = f"""Device type: {device_type.upper()}
Available subsystems: {subsystems_hint}

Requirement text:
\"{text}\"

Extract and return the JSON fields."""

    try:
        # Ground the request using local retrieval if available
        try:
            from ..retrieval.retriever import Retriever
            retr = Retriever()
            hits = retr.retrieve(text, k=3)
        except Exception:
            hits = []

        # Build grounding snippets for prompt
        if hits:
            snippets = []
            for h in hits:
                src = h.get("source") or "unknown"
                snip = (h.get("text") or "").strip().replace("\n", " ")
                snippets.append(f"- Source: {src}\n  Snippet: {snip[:600]}")
            grounding = "\n\nRetrieved similar examples:\n" + "\n\n".join(snippets)
        else:
            grounding = ""

        prompt_with_grounding = user_prompt + "\n\n" + grounding

        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt_with_grounding}
            ]
        )
        content = response.choices[0].message.content.strip()

        # Strip markdown wrappers if present
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        try:
            import json_repair
            result = json_repair.loads(content.strip())
        except ImportError:
            result = json.loads(content.strip())

        # Attach retrieval citations for traceability (non-breaking: extra field)
        if hits:
            result["_citations"] = [
                {"source": h.get("source"), "score": h.get("score") if h.get("score") is not None else None, "snippet": (h.get("text") or '')[:600]} 
                for h in hits
            ]

        return result

    except Exception as e:
        raise ValueError(f"Analysis failed: {str(e)}")
