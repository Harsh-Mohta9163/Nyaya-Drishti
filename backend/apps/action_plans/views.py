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
                return Response(action_plan.full_rag_recommendation, status=status.HTTP_200_OK)
                
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
                date_of_order=judgment.date_of_order if 'judgment' in locals() and judgment else ""
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
