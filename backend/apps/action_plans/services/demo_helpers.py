"""Demo-mode helpers for ActionPlan deadlines.

These exist because most demo PDFs are historical judgments — the real
Limitation Act deadlines computed from `judgment.date_of_order` are years in
the past, which makes the Deadlines / Execution dashboards uniformly red.

For the demo we override those deadlines with future dates (today + N) so
each role's screen shows realistic urgency colours. Production deployments
ingesting current judgments will compute proper deadlines via `rules_engine`
and don't need this helper.
"""
from __future__ import annotations

from datetime import date, timedelta

from apps.action_plans.models import ActionPlan


# Spread the deadlines so the Deadlines Monitor shows the full urgency
# spectrum out-of-the-box: one row in "critical" (<=3d), some in "warning"
# (<=14d), the rest "safe". Tuples are (internal_compliance, compliance,
# internal_appeal, statutory_appeal) in days from today.
DEADLINE_PROFILES = [
    (2, 14, 8, 22),    # critical-warning mix
    (7, 21, 16, 30),   # warning mix
    (12, 28, 22, 40),  # warning -> safe
    (20, 45, 30, 60),  # safe
    (28, 60, 45, 90),  # very safe
]


def apply_demo_deadlines(
    plan: ActionPlan,
    *,
    profile_idx: int | None = None,
    today: date | None = None,
    auto_approve: bool = False,
) -> dict:
    """Set future-dated deadlines on an ActionPlan and (optionally) approve it.

    Args:
        plan: the ActionPlan row to mutate (saved by this function).
        profile_idx: which of the five spread profiles to use. If None, picks
            one based on the plan's primary key so each plan gets a stable
            slot in the spectrum.
        today: date to anchor "today" — defaults to `date.today()`.
        auto_approve: if True and the plan is not already approved, flips
            `verification_status` to "approved". Demo-reset commands pass
            True; the upload pipeline passes False so HLC still verifies
            interactively.

    Returns:
        Dict summarising what changed: keys `did_approve`, `internal_compliance`,
        `compliance`, `internal_appeal`, `statutory_appeal`, `profile_idx`.
    """
    if today is None:
        today = date.today()
    if profile_idx is None:
        # Stable pick based on the plan's auto-int PK so re-runs are idempotent.
        profile_idx = (plan.pk or 0) % len(DEADLINE_PROFILES)
    ic, c, ia, sa = DEADLINE_PROFILES[profile_idx % len(DEADLINE_PROFILES)]

    plan.internal_compliance_deadline = today + timedelta(days=ic)
    plan.compliance_deadline = today + timedelta(days=c)
    plan.internal_appeal_deadline = today + timedelta(days=ia)
    plan.statutory_appeal_deadline = today + timedelta(days=sa)
    if not plan.statutory_period_type:
        plan.statutory_period_type = "writ_appeal (30d)"
    if not plan.recommendation or plan.recommendation == "PENDING":
        plan.recommendation = "APPEAL" if profile_idx % 2 == 0 else "COMPLY"

    did_approve = False
    if auto_approve and not (plan.verification_status or "").startswith("approved"):
        plan.verification_status = "approved"
        did_approve = True

    # Keep any cached recommendation JSON in sync — the Dashboard reads
    # verdict.limitation_deadline from this cache, not the model fields.
    rec = plan.full_rag_recommendation or {}
    verdict = rec.get("verdict") or {}
    verdict["limitation_deadline"] = plan.statutory_appeal_deadline.isoformat()
    verdict["compliance_deadline"] = plan.compliance_deadline.isoformat()
    verdict["days_remaining"] = (plan.statutory_appeal_deadline - today).days
    rec["verdict"] = verdict
    plan.full_rag_recommendation = rec

    plan.save()

    return {
        "did_approve": did_approve,
        "internal_compliance": plan.internal_compliance_deadline,
        "compliance": plan.compliance_deadline,
        "internal_appeal": plan.internal_appeal_deadline,
        "statutory_appeal": plan.statutory_appeal_deadline,
        "profile_idx": profile_idx,
    }


def ensure_demo_plan(case, *, auto_approve: bool = False) -> tuple[ActionPlan | None, dict | None]:
    """get_or_create an ActionPlan for `case` and apply the demo deadline profile.

    Returns (plan, summary). If the case has no judgment yet, returns (None, None)
    — callers should treat that as a no-op.
    """
    judgment = case.judgments.first()
    if not judgment:
        return None, None
    plan, _created = ActionPlan.objects.get_or_create(
        judgment=judgment,
        defaults={"recommendation": "PENDING", "ccms_stage": "Extraction"},
    )
    summary = apply_demo_deadlines(plan, auto_approve=auto_approve)
    return plan, summary
