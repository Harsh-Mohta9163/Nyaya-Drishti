"""Wipe the existing MFA case and re-ingest with the improved 70B extraction."""
import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from apps.cases.models import Case, Judgment
from apps.action_plans.models import ActionPlan

# Find and delete the existing MFA case
cases = Case.objects.filter(case_number__icontains='MFA')
print(f"Found {cases.count()} MFA case(s)")
for c in cases:
    print(f"  Deleting: {c.case_number} (id={c.id})")
    # Delete action plans first
    for j in c.judgments.all():
        ActionPlan.objects.filter(judgment=j).delete()
    c.delete()

print("Done. Ready for re-ingestion.")
