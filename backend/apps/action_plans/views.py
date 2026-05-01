from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cases.models import Case

from .models import ActionPlan
from .serializers import ActionPlanSerializer
from .services.plan_generator import generate_or_refresh_action_plan


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
