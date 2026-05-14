"""Reset every approved ActionPlan's deadlines to today + N days.

Use this just before a demo so nothing shows as overdue on stage. Idempotent —
running it twice is fine. Also flips status to "approved" for ALL existing
ActionPlans so the LCO / Nodal / Execution tabs have visible data.

Usage:
    python manage.py refresh_demo_deadlines
    python manage.py refresh_demo_deadlines --no-approve   # leave verification_status alone
"""
from datetime import date, timedelta

from django.core.management.base import BaseCommand

from apps.action_plans.models import ActionPlan


# Spread the deadlines so the Deadlines monitor shows the full urgency spectrum:
# one row in "critical" (≤3d), one in "warning" (≤14d), rest "safe".
DEADLINE_PROFILES = [
    # (internal_compliance, compliance, internal_appeal, statutory_appeal)
    (2, 14, 8, 22),    # critical-warning mix
    (7, 21, 16, 30),   # warning mix
    (12, 28, 22, 40),  # warning -> safe
    (20, 45, 30, 60),  # safe
    (28, 60, 45, 90),  # very safe
]


class Command(BaseCommand):
    help = "Reset all approved ActionPlan deadlines so nothing shows as overdue on demo day."

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-approve",
            action="store_true",
            help="Skip auto-approving plans; only refresh existing approved ones.",
        )

    def handle(self, *args, no_approve=False, **options):
        today = date.today()
        qs = ActionPlan.objects.select_related("judgment__case").all().order_by("created_at")
        total = qs.count()
        self.stdout.write(f"Refreshing deadlines for {total} ActionPlan(s) as of {today}...")

        refreshed = 0
        approved_count = 0
        for idx, plan in enumerate(qs):
            ic, c, ia, sa = DEADLINE_PROFILES[idx % len(DEADLINE_PROFILES)]
            plan.internal_compliance_deadline = today + timedelta(days=ic)
            plan.compliance_deadline = today + timedelta(days=c)
            plan.internal_appeal_deadline = today + timedelta(days=ia)
            plan.statutory_appeal_deadline = today + timedelta(days=sa)
            if not plan.statutory_period_type:
                plan.statutory_period_type = "writ_appeal (30d)"
            if not plan.recommendation or plan.recommendation == "PENDING":
                plan.recommendation = "APPEAL" if idx % 2 == 0 else "COMPLY"
            if not no_approve and not plan.verification_status.startswith("approved"):
                plan.verification_status = "approved"
                approved_count += 1

            # Also patch any date strings cached inside the recommendation JSON
            # so the Dashboard / CaseOverview don't display stale "overdue" badges.
            rec = plan.full_rag_recommendation or {}
            verdict = rec.get("verdict") or {}
            verdict["limitation_deadline"] = plan.statutory_appeal_deadline.isoformat()
            verdict["compliance_deadline"] = plan.compliance_deadline.isoformat()
            verdict["days_remaining"] = (plan.statutory_appeal_deadline - today).days
            rec["verdict"] = verdict
            plan.full_rag_recommendation = rec

            plan.save()
            refreshed += 1
            self.stdout.write(
                f"  {plan.judgment.case.case_number[:45]:48} "
                f"-> internal={plan.internal_compliance_deadline} "
                f"compliance={plan.compliance_deadline} "
                f"appeal={plan.statutory_appeal_deadline}"
            )

        self.stdout.write(self.style.SUCCESS(
            f"Refreshed {refreshed} plans"
            + (f"; flipped {approved_count} to approved" if approved_count else "")
            + "."
        ))
