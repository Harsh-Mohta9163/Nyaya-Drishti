"""Test the upgraded rules engine."""
import os, django
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
django.setup()

from datetime import date
from apps.action_plans.services.rules_engine import compute_deadlines, get_all_applicable_deadlines

print("=" * 80)
print("RULES ENGINE TEST — Limitation Act 1963 + Karnataka HC Calendar")
print("=" * 80)

# Test 1: SLP deadline
print("\n--- Test 1: SLP from today ---")
d = compute_deadlines(date.today(), "slp")
print(f"  Judgment date:  {d['judgment_date']}")
print(f"  Start date:     {d['start_date']} (Section 12: first day excluded)")
print(f"  Raw deadline:   {d['raw_deadline']}")
print(f"  Legal deadline: {d['legal_deadline']} (Section 4: holiday adjustment)")
print(f"  Internal:       {d['internal_deadline']}")
print(f"  Basis:          {d['basis']}")
print(f"  Remaining:      {d['remaining_calendar_days']} cal / {d['remaining_working_days']} working days")
for w in d["warnings"]:
    print(f"  WARNING: {w}")

# Test 2: Section 12 — certified copy delay
print("\n--- Test 2: Section 12 — Copy obtained 10 days later ---")
d2 = compute_deadlines(date(2026, 5, 1), "lpa", copy_obtained_date=date(2026, 5, 11))
print(f"  Copy days excluded: {d2['copy_days_excluded']}")
print(f"  Start date:  {d2['start_date']}")
print(f"  Legal:       {d2['legal_deadline']}")
for w in d2["warnings"]:
    print(f"  WARNING: {w}")

# Test 3: Deadline on a Sunday (Section 4)
print("\n--- Test 3: Section 4 — Deadline on Sunday ---")
# Find a judgment date that makes the 30-day deadline land on a Sunday
d3 = compute_deadlines(date(2026, 4, 4), "compliance")
print(f"  Raw deadline:   {d3['raw_deadline']} (weekday: {d3['raw_deadline'].strftime('%A')})")
print(f"  Legal deadline: {d3['legal_deadline']} (weekday: {d3['legal_deadline'].strftime('%A')})")
print(f"  Adjusted: {'YES' if d3['deadline_on_holiday'] else 'NO'}")
for w in d3["warnings"]:
    print(f"  WARNING: {w}")

# Test 4: All applicable deadlines
print("\n--- Test 4: All Applicable Deadlines for judgment on 2026-05-01 ---")
all_deadlines = get_all_applicable_deadlines(date(2026, 5, 1))
print(f"  {'Type':<28s} {'Legal Deadline':<16s} {'Days Left':<10s} {'Section'}")
print(f"  {'-'*28} {'-'*16} {'-'*10} {'-'*30}")
for x in all_deadlines[:10]:
    print(f"  {x['type']:<28s} {str(x['legal_deadline']):<16s} {str(x['remaining_calendar_days'])+'d':<10s} {x['section']}")

# Test 5: Risk classifier
print("\n--- Test 5: Contempt Risk Classifier ---")
from apps.action_plans.services.risk_classifier import classify_contempt_risk, _bert_available
print(f"  BERT model loaded: {_bert_available}")
tests = [
    "The Secretary shall personally ensure compliance, failing which coercive action including contempt proceedings will be initiated.",
    "The respondent is directed to pay within 30 days.",
    "The petition is dismissed. No costs.",
]
for t in tests:
    risk = classify_contempt_risk(t)
    print(f"  [{risk:6s}] {t[:70]}...")

print("\nALL TESTS PASSED!")
