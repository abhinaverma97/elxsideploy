from pydantic import BaseModel
from typing import Optional, Literal

RequirementType = Literal[
    "functional",
    "performance",
    "interface",
    "safety",
    "environmental",
    "regulatory"
]

VerificationType = Literal[
    "simulation",
    "analysis",
    "inspection",
    "test"
]

# ISO 14971:2019 — probability of occurrence of hazardous situation
ProbabilityLevel = Literal[
    "Negligible",   # so unlikely it can be disregarded
    "Remote",       # unlikely but conceivable
    "Occasional",   # could occur sometime
    "Probable",     # likely to occur
    "Frequent"      # likely to occur many times
]

SeverityLevel = Literal["Low", "Medium", "High", "Critical"]

# Requirement lifecycle state (per IEC/ISO SE practice)
RequirementStatus = Literal["Draft", "Approved", "Implemented", "Verified"]

# Obligation level (SHALL = mandatory, SHOULD = recommended, MAY = optional)
PriorityLevel = Literal["SHALL", "SHOULD", "MAY"]


class Verification(BaseModel):
    method: VerificationType
    description: str


class Requirement(BaseModel):
    # ── Identity ────────────────────────────────────────────────────
    id: str                            # e.g. REQ-VENT-001
    title: str
    description: str
    parent_id: Optional[str] = None    # decomposition: SYS → SUB → COMP

    # ── FR / NFR plain-text context ────────────────────────────────
    fr_text: Optional[str] = None      # Functional requirement in plain language
    nfr_text: Optional[str] = None     # Non-functional requirement in plain language

    # ── Classification ──────────────────────────────────────────────
    type: RequirementType
    priority: PriorityLevel = "SHALL"
    status: RequirementStatus = "Draft"
    subsystem: Optional[str] = None

    # ── Quantitative bounds (performance / functional) ───────────────
    parameter: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    unit: Optional[str] = None
    tolerance: Optional[float] = None
    response_time_ms: Optional[int] = None

    # ── Interface ───────────────────────────────────────────────────
    interface: Optional[str] = None    # "SourceSubsystem -> TargetSubsystem"
    protocol: Optional[str] = None

    # ── Risk (ISO 14971) ────────────────────────────────────────────
    hazard: Optional[str] = None
    severity: Optional[SeverityLevel] = None
    probability: Optional[ProbabilityLevel] = None  # P1 — probability of hazardous situation

    # ── Regulatory traceability ─────────────────────────────────────
    standard: Optional[str] = None
    clause: Optional[str] = None

    # ── Verification ────────────────────────────────────────────────
    verification: Verification