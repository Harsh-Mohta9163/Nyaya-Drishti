"""Reset every ActionPlan's deadlines to today + N days.

Use this before a demo so nothing shows as overdue on stage. Idempotent —
running it twice is fine. By default also flips status to "approved" for ALL
existing ActionPlans so the LCO / Nodal / Execution tabs have visible data.

Usage:
    python manage.py refresh_demo_deadlines
    python manage.py refresh_demo_deadlines --no-approve   # leave verification_status alone

The deadline math + cache patching live in
`apps/action_plans/services/demo_helpers.py` so the same logic is reused by
the upload pipeline (CaseExtractView) and by this CLI command.
"""
from datetime import date

from django.core.management.base import BaseCommand

from apps.action_plans.models import ActionPlan
from apps.action_plans.services.demo_helpers import apply_demo_deadlines


class Command(BaseCommand):
    help = "Reset all ActionPlan deadlines so nothing shows as overdue on demo day."

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-approve",
            action="store_true",
            help="Skip auto-approving plans; only refresh the deadlines.",
        )

    def handle(self, *args, no_approve=False, **options):
        today = date.today()
        qs = ActionPlan.objects.select_related("judgment__case").all().order_by("created_at")
        total = qs.count()
        self.stdout.write(f"Refreshing deadlines for {total} ActionPlan(s) as of {today}...")

        refreshed = 0
        approved_count = 0
        for idx, plan in enumerate(qs):
            summary = apply_demo_deadlines(
                plan,
                profile_idx=idx,  # spread across the 5 profiles in stable order
                today=today,
                auto_approve=not no_approve,
            )
            if summary["did_approve"]:
                approved_count += 1
            refreshed += 1
            self.stdout.write(
                f"  {plan.judgment.case.case_number[:45]:48} "
                f"-> internal={summary['internal_compliance']} "
                f"compliance={summary['compliance']} "
                f"appeal={summary['statutory_appeal']}"
            )

        self.stdout.write(self.style.SUCCESS(
            f"Refreshed {refreshed} plans"
            + (f"; flipped {approved_count} to approved" if approved_count else "")
            + "."
        ))
