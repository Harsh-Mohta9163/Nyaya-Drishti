from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cases.models import Case

from .models import ActionPlan
from .serializers import ActionPlanSerializer
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
