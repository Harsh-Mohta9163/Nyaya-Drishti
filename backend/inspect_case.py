import os, django, json
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()
from apps.cases.models import Case, Judgment

j = Judgment.objects.get(case__case_number__startswith='MFA No.20338')
raw = j.raw_extracted_json or {}
print("=== RAW EXTRACTED DATA ===")
for key in raw:
    val = raw[key]
    if isinstance(val, dict):
        print(f"\n[{key}]:")
        for k, v in val.items():
            s = str(v)[:200]
            print(f"  {k}: {s}")
    elif isinstance(val, list):
        print(f"\n[{key}]: ({len(val)} items)")
        for item in val[:3]:
            print(f"  - {str(item)[:200]}")

print(f"\n=== DB FIELDS ===")
print(f"court_directions: {j.court_directions}")
print(f"disposition: {j.disposition}")
print(f"winning_party: {j.winning_party_type}")
print(f"summary: {(j.summary_of_facts or '')[:300]}")
