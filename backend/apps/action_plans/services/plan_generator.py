from apps.cases.models import Case
from apps.cases.models import ExtractedData

from ..models import ActionPlan
from .rag_engine import HybridRAGEngine
from .risk_classifier import classify_contempt_risk
from .rules_engine import compute_deadlines


RAG_ENGINE = HybridRAGEngine()


def _build_departments(extracted_data):
    entities = extracted_data.entities if extracted_data else []
    departments = []
    for entity in entities:
        if isinstance(entity, dict):
            name = entity.get("name") or entity.get("text")
        else:
            name = str(entity)
        if name and name not in departments:
            departments.append(name)
    return departments or ["General Administration"]


def generate_or_refresh_action_plan(case: Case):
    try:
        extracted_data = case.extracted_data
    except ExtractedData.DoesNotExist:
        extracted_data = None
    operative_text = extracted_data.operative_order if extracted_data else ""
    recommendation = "appeal" if "appeal" in (operative_text or "").lower() else "comply"
    deadline_info = compute_deadlines(case.judgment_date, extracted_data.order_type if extracted_data else "", recommendation)
    contempt_risk = classify_contempt_risk(operative_text)
    similar_cases = RAG_ENGINE.query(operative_text or case.case_number, top_k=5)
    compliance_actions = extracted_data.court_directions if extracted_data else []
    action_plan, _ = ActionPlan.objects.update_or_create(
        case=case,
        defaults={
            "recommendation": recommendation.title(),
            "recommendation_reasoning": "Deterministic first-pass plan generated from extracted order text.",
            "compliance_actions": compliance_actions,
            "legal_deadline": deadline_info["legal_deadline"],
            "internal_deadline": deadline_info["internal_deadline"],
            "responsible_departments": _build_departments(extracted_data),
            "ccms_stage": "Proposed for Appeal" if recommendation == "appeal" else "Order Compliance Stage",
            "contempt_risk": contempt_risk,
            "similar_cases": similar_cases,
            "verification_status": "pending",
        },
    )
    case.status = Case.Status.ACTION_CREATED
    case.save(update_fields=["status", "updated_at"])
    return action_plan
