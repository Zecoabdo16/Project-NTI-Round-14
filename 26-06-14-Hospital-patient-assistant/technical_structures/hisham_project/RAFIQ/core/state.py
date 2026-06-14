# core/state.py
from typing import TypedDict, Optional, List, Dict

class PatientState(TypedDict):
    patient_id: str
    conversation_history: list
    detected_intent: str           # admin | medical | emergency
    urgency_level: int            # ESI 1–5
    emr_snippets: list            # retrieved records with IDs
    kg_results: list              # graph traversal findings
    draft_response: str
    grounding_confidence: float   # 0.0–1.0
    pli: float                    # 0–100
    cas: float                    # 0–100
    hitl_required: bool
    hitl_decision: Optional[str]