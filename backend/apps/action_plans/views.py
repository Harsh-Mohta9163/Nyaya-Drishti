from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import GLOBAL_ACCESS_ROLES
from apps.cases.models import Case

from .models import ActionPlan, DirectiveExecution
from .serializers import ActionPlanSerializer, DirectiveExecutionSerializer
from .services.plan_generator import generate_or_refresh_action_plan
from .services.recommendation_pipeline import generate_recommendation
from .services.rag_engine import HybridRAGEngine


def backfill_precedents(case_text: str, cached_rec: dict, action_plan=None) -> dict:
    """Extract and backfill precedents into cached recommendation if missing."""
    agent_outputs = cached_rec.get("agent_outputs", {})
    precedents = agent_outputs.get("precedents", [])
    
    if precedents:
        return cached_rec
    
    try:
        rag = HybridRAGEngine()
        raw_chunks = rag.retrieve(case_text[:2000], top_k=8, filters=None)
        
        # Deduplicate by case_id
        seen_cases = {}
        for c in (raw_chunks or []):
            score = c.get('score', 0)
            if score < 0.85:  # Cosine similarity threshold (not cross-encoder)
                continue
            meta = c.get('metadata', {})
            cid = meta.get('case_id', '')
            if cid in seen_cases:
                continue
            seen_cases[cid] = True
            
            text = c.get('text', '')
            # Bucket relevance for frontend
            relevance_label = "High" if score >= 0.93 else "Moderate" if score >= 0.91 else "Low"
            
            seen_cases[cid] = {
                "case_id": str(cid),
                "case_title": str(meta.get('title', 'Unknown')),
                "relevance": relevance_label,
                "similarity_score": round(score, 4),
                "key_holding": text[:500] + ("..." if len(text) > 500 else ""),
                "outcome": str(meta.get('disposal_nature', 'UNKNOWN')),
                "applicability": ""
            }
        
        extracted_precedents = [v for v in seen_cases.values() if isinstance(v, dict)]
        
        cached_rec["agent_outputs"] = agent_outputs
        cached_rec["agent_outputs"]["precedents"] = extracted_precedents
        cached_rec["agent_outputs"]["precedent_strength"] = "STRONG" if len(extracted_precedents) >= 5 else "MODERATE" if extracted_precedents else "WEAK"
        cached_rec["agent_outputs"]["overall_trend"] = f"{len(extracted_precedents)} similar precedents found via InLegalBERT semantic search." if extracted_precedents else "No precedents found."
        
        if action_plan:
            action_plan.full_rag_recommendation = cached_rec
            action_plan.save()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Precedent backfill failed: {e}")
    
    return cached_rec


class ActionPlanListView(ListAPIView):
    queryset = ActionPlan.objects.select_related("case").all().order_by("-updated_at")
    serializer_class = ActionPlanSerializer


class ActionPlanDetailView(RetrieveAPIView):
    queryset = ActionPlan.objects.select_related("case").all()
    serializer_class = ActionPlanSerializer


class GenerateActionPlanView(APIView):
    def post(self, request, pk):
        case = get_object_or_404(Case, pk=pk)
        action_plan = generate_or_refresh_action_plan(case)
        return Response(ActionPlanSerializer(action_plan).data, status=status.HTTP_200_OK)


class GenerateRecommendationView(APIView):
    permission_classes = [permissions.AllowAny]  # Allow demo access to RAG pipeline

    def post(self, request, pk=None):
        area_of_law = request.data.get("area_of_law", "constitutional")
        court = request.data.get("court", "Supreme Court of India")
        case_text = request.data.get("case_text", "Sample case text")
        
        # If pk is provided, try to load from DB
        case_id = request.data.get("case_id", "mock-id")
        case = None
        
        # Additional metadata fields
        disposition = ""
        winning_party = ""
        case_type = request.data.get("case_type", "")
        bench = ""
        petitioner = ""
        respondent = ""
        issues = []
        
        if pk:
            from apps.cases.models import Case
            try:
                case = Case.objects.get(pk=pk)
                case_id = case.cnr_number or str(case.id)
                case_type = case.case_type or case_type
                petitioner = case.petitioner_name or petitioner
                respondent = case.respondent_name or respondent
                court = case.court_name or court
                area_of_law = case.area_of_law or area_of_law
                
                if hasattr(case, 'facts') and case.facts:
                    case_text = case.facts
                elif case.judgments.exists() and case.judgments.first().summary_of_facts:
                    case_text = case.judgments.first().summary_of_facts
                    
                # Extract judgment-specific fields
                if case.judgments.exists():
                    judgment = case.judgments.first()
                    disposition = judgment.disposition or disposition
                    winning_party = judgment.winning_party_type or winning_party
                    if judgment.presiding_judges:
                        bench = ", ".join(judgment.presiding_judges)
                    issues = judgment.issues_framed or issues
                    
            except Exception:
                pass
                
        # Check cache if we have a valid case
        force_regenerate = request.data.get("force_regenerate", False)
        action_plan = None
        if case and case.judgments.exists():
            judgment = case.judgments.first()
            from apps.action_plans.models import ActionPlan
            action_plan, _ = ActionPlan.objects.get_or_create(
                judgment=judgment,
                defaults={"recommendation": "PENDING", "ccms_stage": "Extraction"}
            )
            
            # If we already have the full recommendation cached, return it directly
            # Unless force_regenerate is True
            if action_plan.full_rag_recommendation and not force_regenerate:
                cached = backfill_precedents(case_text, action_plan.full_rag_recommendation, action_plan)
                return Response(cached, status=status.HTTP_200_OK)
                
        try:
            recommendation = generate_recommendation(
                case_id=case_id,
                case_text=case_text,
                area_of_law=area_of_law,
                court=court,
                disposition=disposition,
                winning_party=winning_party,
                case_type=case_type,
                bench=bench,
                petitioner=petitioner,
                respondent=respondent,
                issues=issues,
                date_of_order=judgment.date_of_order if 'judgment' in locals() and judgment else "",
                court_directions=judgment.court_directions if 'judgment' in locals() and judgment else [],
                operative_order_text=judgment.operative_order_text if 'judgment' in locals() and judgment else "",
                ratio_decidendi=judgment.ratio_decidendi if 'judgment' in locals() and judgment else "",
                financial_implications=judgment.financial_implications if 'judgment' in locals() and judgment else None,
                use_rag=True
            )
            
            # Cache it
            if action_plan:
                action_plan.full_rag_recommendation = recommendation
                # Update high-level fields too
                action_plan.recommendation = recommendation.get("verdict", {}).get("decision", "PENDING")
                action_plan.save()
                
            return Response(recommendation, status=status.HTTP_200_OK)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---------------------------------------------------------------------------
# LCO Execution dashboard
# ---------------------------------------------------------------------------

def _approved_plans_for_user(user):
    """Approved ActionPlans visible to the calling user.

    Dept-scoped users see plans for cases whose primary or secondary department
    matches theirs. Global roles see everything (or `?department=CODE`).
    """
    qs = (
        ActionPlan.objects
        .select_related("judgment__case__primary_department")
        .filter(verification_status__startswith="approved")
    )
    if not user or not user.is_authenticated:
        return qs.none()
    if user.role in GLOBAL_ACCESS_ROLES:
        return qs
    if not user.department_id:
        return qs.none()
    return qs.filter(
        Q(judgment__case__primary_department=user.department_id)
        | Q(judgment__case__secondary_departments=user.department_id)
    ).distinct()


def _materialize_executions(plan: ActionPlan) -> list[DirectiveExecution]:
    """Ensure one DirectiveExecution row exists per court_directions entry."""
    judgment = plan.judgment
    directions = judgment.court_directions or []
    existing = {e.directive_index: e for e in plan.executions.all()}
    created = []
    for idx, d in enumerate(directions):
        if idx in existing:
            continue
        if not isinstance(d, dict):
            continue
        created.append(DirectiveExecution.objects.create(
            action_plan=plan,
            directive_index=idx,
            directive_text=(d.get("text") or "")[:5000],
            responsible_entity=(d.get("responsible_entity") or "")[:300],
            action_required=(d.get("action_required") or "")[:5000],
            deadline_mentioned=(d.get("deadline_mentioned") or "")[:200],
        ))
    return list(plan.executions.all().order_by("directive_index"))


class LCOExecutionListView(APIView):
    """GET /api/action-plans/execution/

    Returns approved directives for the LCO's department.
    Optional query params:
      - department=CODE  (central law / monitoring only — drill-down)
      - status=pending|in_progress|completed|blocked
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        plans = _approved_plans_for_user(request.user)

        if request.user.role in GLOBAL_ACCESS_ROLES:
            code = (request.query_params.get("department") or "").strip().upper()
            if code:
                plans = plans.filter(judgment__case__primary_department__code=code)

        # Materialize execution rows lazily.
        for plan in plans:
            _materialize_executions(plan)

        execs = DirectiveExecution.objects.filter(action_plan__in=plans).select_related(
            "action_plan__judgment__case__primary_department",
            "executed_by",
        )

        status_filter = (request.query_params.get("status") or "").strip()
        if status_filter:
            execs = execs.filter(status=status_filter)

        execs = execs.order_by("status", "action_plan__compliance_deadline", "created_at")

        # Default: only show directives that are BOTH
        #   (a) a government action (gov_action_required=True), AND
        #   (b) explicitly verified by the HLC (isVerified=True).
        # The HLC checkbox on the Verify-Actions tab is what flips isVerified.
        # Pass ?include=all to show everything (central-law audit view).
        include_all = (request.query_params.get("include") or "").lower() == "all"
        rows = list(execs)
        if not include_all:
            filtered = []
            for e in rows:
                directions = e.action_plan.judgment.court_directions or []
                if 0 <= e.directive_index < len(directions):
                    d = directions[e.directive_index]
                    if not isinstance(d, dict):
                        continue
                    if d.get("gov_action_required") is not True:
                        continue
                    if not d.get("isVerified"):
                        continue
                    filtered.append(e)
            rows = filtered

        ser = DirectiveExecutionSerializer(rows, many=True, context={"request": request})
        return Response(ser.data)


class LCOExecutionDetailView(APIView):
    """PATCH /api/action-plans/execution/<uuid:pk>/

    Updates status / notes / optional proof_file for a single directive.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def _can_edit(self, user, execution: DirectiveExecution) -> bool:
        if user.role in GLOBAL_ACCESS_ROLES:
            return True
        if not user.department_id:
            return False
        case = execution.action_plan.judgment.case
        return (
            case.primary_department_id == user.department_id
            or case.secondary_departments.filter(id=user.department_id).exists()
        )

    def patch(self, request, pk):
        execution = get_object_or_404(DirectiveExecution, pk=pk)
        if not self._can_edit(request.user, execution):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        new_status = request.data.get("status")
        if new_status:
            valid = {c[0] for c in DirectiveExecution.Status.choices}
            if new_status not in valid:
                return Response(
                    {"detail": f"status must be one of {sorted(valid)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            execution.status = new_status
            if new_status == DirectiveExecution.Status.COMPLETED:
                execution.completed_at = timezone.now()
                execution.executed_by = request.user
            elif new_status != DirectiveExecution.Status.COMPLETED:
                execution.completed_at = None

        if "notes" in request.data:
            execution.notes = (request.data.get("notes") or "")[:10000]
        if "proof_file" in request.data and request.data["proof_file"]:
            execution.proof_file = request.data["proof_file"]

        execution.save()
        return Response(
            DirectiveExecutionSerializer(execution, context={"request": request}).data
        )
