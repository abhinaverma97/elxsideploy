from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..core.requirements.schema import Requirement
from ..core.requirements.validator import validate_requirement
from ..core.requirements.store import RequirementStore
from ..core.requirements.nlp_analyzer import analyze_requirement_text

router = APIRouter()
store = RequirementStore()


class RequirementTextInput(BaseModel):
    text: str
    device_type: str = "ventilator"


@router.post("/analyze")
def analyze_requirement(body: RequirementTextInput):
    """
    Parse a plain-English functional or non-functional requirement
    and return structured fields ready to populate the requirement form.
    """
    try:
        result = analyze_requirement_text(body.text, body.device_type)
        return {"status": "ok", "fields": result}
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
def add_requirement(req: Requirement):
    print(f"DEBUG: Incoming requirement: {req.id} ({req.type})")
    errors = validate_requirement(req)
    if errors:
        print(f"DEBUG: Validation errors for {req.id}: {errors}")
        raise HTTPException(status_code=400, detail=errors)
    store.add(req)
    return {"status": "added", "id": req.id}


@router.get("/")
def get_requirements():
    return store.get_all()
