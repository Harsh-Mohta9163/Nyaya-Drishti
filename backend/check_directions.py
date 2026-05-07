"""Check court_directions status for WA 305."""
import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from apps.cases.models import Case, Judgment
import json

# Find WA 305 cases
wa305 = Case.objects.filter(case_number__icontains='305')
print(f"WA 305 cases: {wa305.count()}")
for c in wa305:
    j = c.judgments.first()
    print(f"\n  ID: {c.id}")
    print(f"  Number: {c.case_number}")
    print(f"  Status: {j.processing_status if j else 'no judgment'}")
    print(f"  Has PDF: {bool(j.pdf_file) if j else False}")
    print(f"  Directions: {json.dumps(j.court_directions, indent=2)[:500] if j and j.court_directions else 'EMPTY'}")
    print(f"  Raw JSON keys: {list(j.raw_extracted_json.keys()) if j and j.raw_extracted_json else 'EMPTY'}")
    
    if j and j.raw_extracted_json and 'compliance' in j.raw_extracted_json:
        comp = j.raw_extracted_json['compliance']
        print(f"  Raw compliance.court_directions: {json.dumps(comp.get('court_directions', []), indent=2)[:500]}")
        print(f"  Raw compliance.disposition: {comp.get('disposition')}")
