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
        if pk:
            from apps.cases.models import Case
            try:
                case = Case.objects.get(pk=pk)
                case_id = case.cnr_number or str(case.id)
                if hasattr(case, 'facts') and case.facts:
                    case_text = case.facts
            except Exception:
                pass
                
        try:
            recommendation = generate_recommendation(
                case_id=case_id,
                case_text=case_text,
                area_of_law=area_of_law,
                court=court
            )
            return Response(recommendation, status=status.HTTP_200_OK)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
