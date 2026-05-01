from datetime import timedelta

from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.action_plans.models import ActionPlan
from apps.cases.models import Case


class DashboardStatsView(APIView):
    def get(self, request):
        return Response(
            {
                "total_cases": Case.objects.count(),
                "pending_cases": Case.objects.filter(status__in=[Case.Status.UPLOADED, Case.Status.PROCESSING]).count(),
                "verified_cases": Case.objects.filter(status=Case.Status.VERIFIED).count(),
                "high_risk_cases": ActionPlan.objects.filter(contempt_risk="High").count(),
            }
        )


class DashboardDeadlinesView(APIView):
    def get(self, request):
        cutoff = timezone.now().date() + timedelta(days=30)
        plans = ActionPlan.objects.select_related("case").filter(legal_deadline__lte=cutoff).order_by("legal_deadline")
        data = [
            {
                "case_id": plan.case_id,
                "case_number": plan.case.case_number,
                "legal_deadline": plan.legal_deadline,
                "internal_deadline": plan.internal_deadline,
                "ccms_stage": plan.ccms_stage,
                "contempt_risk": plan.contempt_risk,
            }
            for plan in plans
        ]
        return Response(data)


class DashboardHighRiskView(APIView):
    def get(self, request):
        plans = ActionPlan.objects.select_related("case").filter(contempt_risk="High").order_by("legal_deadline")
        data = [
            {
                "case_id": plan.case_id,
                "case_number": plan.case.case_number,
                "recommendation": plan.recommendation,
                "legal_deadline": plan.legal_deadline,
                "ccms_stage": plan.ccms_stage,
            }
            for plan in plans
        ]
        return Response(data)