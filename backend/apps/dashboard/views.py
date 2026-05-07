from datetime import timedelta

from django.db.models import Avg, Q
from django.utils import timezone
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.action_plans.models import ActionPlan
from apps.cases.models import Case


class DashboardStatsView(APIView):
    permission_classes = [permissions.AllowAny]  # Demo access

    def get(self, request):
        now = timezone.now()
        seven_days = now.date() + timedelta(days=7)

        total_cases = Case.objects.count()
        pending_review = Case.objects.filter(status=Case.Status.PENDING).count()
        
        # Try to get high risk from action plans, gracefully handle missing fields
        try:
            high_risk = ActionPlan.objects.filter(contempt_risk="High").count()
        except Exception:
            high_risk = 0
            
        try:
            upcoming_7d = ActionPlan.objects.filter(
                legal_deadline__lte=seven_days,
                legal_deadline__gte=now.date()
            ).count()
        except Exception:
            upcoming_7d = 0

        return Response({
            "total_cases": total_cases,
            "pending_review": pending_review,
            "high_risk": high_risk,
            "upcoming_deadlines_7d": upcoming_7d,
            "verified_this_month": 0,
            "avg_extraction_confidence": 0.0,
        })


class DashboardDeadlinesView(APIView):
    def get(self, request):
        days = int(request.query_params.get("days", 30))
        cutoff = timezone.now().date() + timedelta(days=days)
        plans = (
            ActionPlan.objects.select_related("case")
            .filter(legal_deadline__lte=cutoff, legal_deadline__gte=timezone.now().date())
            .order_by("legal_deadline")
        )
        data = []
        for plan in plans:
            days_remaining = (plan.legal_deadline - timezone.now().date()).days
            data.append({
                "case_id": plan.case_id,
                "case_number": plan.case.case_number,
                "case_type": plan.case.case_type,
                "legal_deadline": plan.legal_deadline,
                "internal_deadline": plan.internal_deadline,
                "contempt_risk": plan.contempt_risk,
                "ccms_stage": plan.ccms_stage,
                "days_remaining": days_remaining,
            })
        return Response(data)


class DashboardHighRiskView(APIView):
    def get(self, request):
        plans = (
            ActionPlan.objects.select_related("case")
            .filter(contempt_risk="High")
            .order_by("legal_deadline")
        )
        data = []
        for plan in plans:
            days_remaining = (
                (plan.legal_deadline - timezone.now().date()).days
                if plan.legal_deadline
                else None
            )
            data.append({
                "case_id": plan.case_id,
                "case_number": plan.case.case_number,
                "court": plan.case.court,
                "petitioner": plan.case.petitioner,
                "contempt_risk": plan.contempt_risk,
                "legal_deadline": plan.legal_deadline,
                "days_remaining": days_remaining,
                "ccms_stage": plan.ccms_stage,
            })
        return Response(data)