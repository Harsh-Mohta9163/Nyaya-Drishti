from datetime import timedelta

from django.db.models import Avg, Count, Q
from django.utils import timezone
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import GLOBAL_ACCESS_ROLES
from apps.action_plans.models import ActionPlan
from apps.cases.models import Case


def _scope_cases(user, qs):
    """Apply department scoping to a Case queryset.

    Mirrors DepartmentScopedQuerysetMixin but works for non-CBV aggregations.
    """
    if not user.is_authenticated:
        return qs.none()
    if user.role in GLOBAL_ACCESS_ROLES:
        return qs
    if not user.department_id:
        return qs.none()
    return qs.filter(
        Q(primary_department=user.department_id)
        | Q(secondary_departments=user.department_id)
    ).distinct()


def _scope_action_plans(user, qs):
    if not user.is_authenticated:
        return qs.none()
    if user.role in GLOBAL_ACCESS_ROLES:
        return qs
    if not user.department_id:
        return qs.none()
    return qs.filter(
        Q(judgment__case__primary_department=user.department_id)
        | Q(judgment__case__secondary_departments=user.department_id)
    ).distinct()


class DashboardStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        seven_days = now.date() + timedelta(days=7)
        user = request.user

        cases = _scope_cases(user, Case.objects.all())
        action_plans = _scope_action_plans(user, ActionPlan.objects.all())

        total_cases = cases.count()
        pending_review = cases.exclude(
            judgments__action_plan__verification_status__startswith="approved"
        ).distinct().count()

        try:
            high_risk = action_plans.filter(judgment__contempt_risk="High").count()
        except Exception:
            high_risk = 0

        try:
            upcoming_7d = action_plans.filter(
                compliance_deadline__lte=seven_days,
                compliance_deadline__gte=now.date(),
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
            "scope": {
                "role": user.role,
                "department_code": user.department.code if user.department_id else None,
                "department_name": user.department.name if user.department_id else None,
                "global": user.role in GLOBAL_ACCESS_ROLES,
            },
        })


class DashboardDeadlinesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get("days", 30))
        cutoff = timezone.now().date() + timedelta(days=days)
        plans = _scope_action_plans(
            request.user,
            ActionPlan.objects.select_related("judgment__case")
            .filter(compliance_deadline__lte=cutoff, compliance_deadline__gte=timezone.now().date())
            .order_by("compliance_deadline"),
        )
        data = []
        for plan in plans:
            days_remaining = (plan.compliance_deadline - timezone.now().date()).days if plan.compliance_deadline else None
            case = plan.judgment.case if plan.judgment else None
            data.append({
                "case_id": case.id if case else None,
                "case_number": case.case_number if case else "",
                "case_type": case.case_type if case else "",
                "legal_deadline": plan.compliance_deadline,
                "internal_deadline": getattr(plan, "internal_compliance_deadline", None),
                "contempt_risk": plan.judgment.contempt_risk if plan.judgment else "Low",
                "ccms_stage": plan.ccms_stage,
                "days_remaining": days_remaining,
            })
        return Response(data)


class DashboardHighRiskView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        plans = _scope_action_plans(
            request.user,
            ActionPlan.objects.select_related("judgment__case")
            .filter(judgment__contempt_risk="High")
            .order_by("compliance_deadline"),
        )
        data = []
        for plan in plans:
            days_remaining = (
                (plan.compliance_deadline - timezone.now().date()).days
                if plan.compliance_deadline else None
            )
            case = plan.judgment.case if plan.judgment else None
            data.append({
                "case_id": case.id if case else None,
                "case_number": case.case_number if case else "",
                "court": case.court_name if case else "",
                "petitioner": case.petitioner_name if case else "",
                "contempt_risk": plan.judgment.contempt_risk if plan.judgment else "High",
                "legal_deadline": plan.compliance_deadline,
                "days_remaining": days_remaining,
                "ccms_stage": plan.ccms_stage,
            })
        return Response(data)


class NodalDeadlinesMonitorView(APIView):
    """GET /api/dashboard/deadlines-monitor/

    Returns approved ActionPlans for the user's department sorted by the
    NEAREST upcoming deadline (whichever of compliance / statutory appeal /
    internal-buffer comes first). Includes an urgency bucket so the UI can
    color-code without re-doing the date math.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.now().date()

        plans = ActionPlan.objects.select_related(
            "judgment__case__primary_department"
        ).filter(verification_status__startswith="approved")
        plans = _scope_action_plans(user, plans)

        # Optional drill-down for central law / monitoring
        if user.role in GLOBAL_ACCESS_ROLES:
            code = (request.query_params.get("department") or "").strip().upper()
            if code:
                plans = plans.filter(
                    judgment__case__primary_department__code=code
                )

        rows = []
        for plan in plans:
            case = plan.judgment.case if plan.judgment else None
            if case is None:
                continue

            # Pick the earliest "next deadline" the Nodal Officer must watch.
            candidates = []
            for label, dt in (
                ("Internal compliance buffer", plan.internal_compliance_deadline),
                ("Internal appeal buffer", plan.internal_appeal_deadline),
                ("Statutory compliance", plan.compliance_deadline),
                ("Statutory appeal", plan.statutory_appeal_deadline),
            ):
                if dt:
                    candidates.append((dt, label))
            candidates.sort(key=lambda x: x[0])
            if candidates:
                next_dt, next_label = candidates[0]
                days_remaining = (next_dt - today).days
                if days_remaining < 0:
                    urgency = "overdue"
                elif days_remaining <= 3:
                    urgency = "critical"
                elif days_remaining <= 14:
                    urgency = "warning"
                else:
                    urgency = "safe"
            else:
                next_dt, next_label, days_remaining, urgency = None, "", None, "unknown"

            judgment = plan.judgment
            primary_dept = case.primary_department
            rows.append({
                "action_plan_id": plan.id,
                "case_id": case.id,
                "case_number": case.case_number,
                "case_title": f"{case.petitioner_name} vs {case.respondent_name}"[:160],
                "department_code": primary_dept.code if primary_dept else None,
                "department_name": primary_dept.name if primary_dept else None,
                "recommendation": plan.recommendation,
                "verification_status": plan.verification_status,
                "compliance_deadline": plan.compliance_deadline,
                "internal_compliance_deadline": plan.internal_compliance_deadline,
                "statutory_appeal_deadline": plan.statutory_appeal_deadline,
                "internal_appeal_deadline": plan.internal_appeal_deadline,
                "statutory_period_type": plan.statutory_period_type or "",
                "contempt_risk": judgment.contempt_risk if judgment else "Low",
                "next_deadline": next_dt,
                "next_deadline_label": next_label,
                "days_remaining": days_remaining,
                "urgency": urgency,
            })

        # Sort: overdue/critical first, then by next_deadline ASC, unknown last.
        urgency_rank = {"overdue": 0, "critical": 1, "warning": 2, "safe": 3, "unknown": 4}
        rows.sort(key=lambda r: (
            urgency_rank.get(r["urgency"], 5),
            r["next_deadline"] or timezone.now().date().replace(year=9999),
        ))

        return Response(rows)


class DashboardByDepartmentView(APIView):
    """GET /api/dashboard/by-department/

    Central Law / State Monitoring tile-grid endpoint. Returns one row per of
    the 48 departments with aggregate case counts. Forbidden to dept-scoped roles.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role not in GLOBAL_ACCESS_ROLES:
            return Response({"error": "Central / monitoring access required."}, status=403)

        from apps.accounts.models import Department
        
        departments = {
            d.id: {
                "id": d.id, "code": d.code, "name": d.name, "sector": d.sector,
                "total_cases": 0, "high_risk": 0, "pending": 0
            }
            for d in Department.objects.filter(is_active=True)
        }

        cases = Case.objects.prefetch_related(
            "judgments__action_plan",
            "secondary_departments"
        )

        for case in cases:
            dept_ids = set()
            if case.primary_department_id:
                dept_ids.add(case.primary_department_id)
            for sec_dept in case.secondary_departments.all():
                dept_ids.add(sec_dept.id)

            is_pending = True
            has_high_risk = False
            
            for judgment in case.judgments.all():
                if judgment.contempt_risk == "High":
                    has_high_risk = True
                # If ANY judgment has an approved action plan, the case is no longer "pending verify"
                if hasattr(judgment, "action_plan") and judgment.action_plan.verification_status.startswith("approved"):
                    is_pending = False
                    
            for d_id in dept_ids:
                if d_id in departments:
                    departments[d_id]["total_cases"] += 1
                    if is_pending:
                        departments[d_id]["pending"] += 1
                    if has_high_risk:
                        departments[d_id]["high_risk"] += 1

        rows = sorted(departments.values(), key=lambda x: (x["sector"], x["name"]))
        return Response(rows)
