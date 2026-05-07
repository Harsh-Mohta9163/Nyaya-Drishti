import django, os, json
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()
from apps.cases.models import Case, Judgment

c = Case.objects.get(case_number__startswith='Pending 753')
j = c.judgments.first()
print(f"Case: {c.case_number}")
print(f"Court: {c.court_name}")
print(f"Petitioner: {c.petitioner_name}")
print(f"Status: {j.processing_status}")
print(f"\nRaw JSON keys: {list(j.raw_extracted_json.keys()) if j.raw_extracted_json else 'NONE'}")

if j.raw_extracted_json:
    for key in j.raw_extracted_json:
        val = j.raw_extracted_json[key]
        if isinstance(val, dict):
            print(f"\n  [{key}] keys: {list(val.keys())}")
            for k, v in val.items():
                s = str(v)[:120]
                print(f"    {k}: {s}")
        elif isinstance(val, list):
            print(f"\n  [{key}] ({len(val)} items)")
        else:
            print(f"\n  [{key}]: {str(val)[:200]}")

print(f"\nCourt directions: {json.dumps(j.court_directions, indent=2)[:500] if j.court_directions else 'EMPTY'}")
print(f"Summary: {(j.summary_of_facts or 'EMPTY')[:200]}")
print(f"Disposition: {j.disposition}")
