import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.cases.models import Case
cases = Case.objects.exclude(case_number__startswith='tmp')[:2]

for c in cases:
    j = c.judgments.first()
    print(f"\n=== Case: {c.case_number} ===")
    print(f"Case Type (Appeal or WP): {c.case_type}")
    print(f"Entities: {j.entities}")
    citations = j.raw_extracted_json.get("_cases_cited", []) if j.raw_extracted_json else []
    print(f"Citations: {citations}")
    print(f"Financial Implications: {j.financial_implications}")
    print(f"Contempt Risk/Indicators: {j.contempt_risk} - {j.contempt_indicators}")
