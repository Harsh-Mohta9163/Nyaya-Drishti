from apps.cases.models import Case, Judgment
from ..models import ActionPlan
from .rag_engine import HybridRAGEngine
from .rules_engine import compute_deadlines

RAG_ENGINE = HybridRAGEngine()

def _build_departments(judgment):
    entities = judgment.entities if judgment else []
    departments = []
    for entity in entities:
        if isinstance(entity, dict):
            name = entity.get("name") or entity.get("text")
        else:
            name = str(entity)
        if name and name not in departments:
            departments.append(name)
    return departments or ["General Administration"]

def generate_or_refresh_action_plan(judgment: Judgment):
    operative_text = "\n".join([d.get("text", "") for d in judgment.court_directions])
    
    # 1. Determine Recommendation
    # By default, use our appeal strategy from the model if available, else rules
    action_plan, _ = ActionPlan.objects.get_or_create(judgment=judgment)
    recommendation = action_plan.recommendation if action_plan.recommendation else ("Appeal" if "appeal" in operative_text.lower() else "Comply")
    
    # 2. Compute Deadlines using deterministic rules engine (Phase 9)
    # The rules engine looks at LimitationRule and CourtCalendar
    deadline_info = compute_deadlines(judgment.date_of_order, judgment.document_type, recommendation)
    
    # 3. Retrieve similar cases (RAG)
    similar_cases = []
    if judgment.summary_of_facts:
        raw_similar = RAG_ENGINE.retrieve(judgment.summary_of_facts, top_k=5)
        for r in raw_similar:
            meta = r.get("metadata", {})
            similar_cases.append({
                "case_number": meta.get("case_number", "Unknown Case"),
                "court_name": meta.get("court_name", "Unknown Court"),
                "similarity_score": r.get("score", 0.0),
                "disposition": meta.get("disposition", "Unknown")
            })

    # 4. Update Action Plan
    action_plan.recommendation = recommendation.title()
    if not action_plan.recommendation_reasoning:
        action_plan.recommendation_reasoning = "Deterministic first-pass plan generated."
    
    action_plan.compliance_actions = judgment.court_directions
    
    # NLP-based deadlines from extracted data vs Deterministic
    # In a real app we'd merge them, but here we just take deterministic
    action_plan.statutory_appeal_deadline = deadline_info["legal_deadline"]
    action_plan.internal_appeal_deadline = deadline_info["internal_deadline"]
    
    action_plan.responsible_departments = _build_departments(judgment)
    action_plan.ccms_stage = "Proposed for Appeal" if recommendation.lower() == "appeal" else "Order Compliance Stage"
    action_plan.contempt_risk = judgment.contempt_risk
    action_plan.similar_cases = similar_cases
    if not action_plan.verification_status:
        action_plan.verification_status = "pending"
        
    action_plan.save()
    return action_plan
