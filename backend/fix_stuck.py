"""Check and fix the stuck 'extracting' case."""
import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from apps.cases.models import Case, Judgment

# Find the stuck extracting case
stuck = Judgment.objects.filter(processing_status='extracting')
print(f"Stuck cases: {stuck.count()}")
for j in stuck:
    print(f"  Case: {j.case.id} | {j.case.case_number}")
    print(f"  Created: {j.case.created_at}")
    print(f"  Has raw_json: {bool(j.raw_extracted_json)}")
    print(f"  Has summary: {bool(j.summary_of_facts)}")
    print(f"  Directions: {len(j.court_directions) if j.court_directions else 0}")
    
    if j.raw_extracted_json:
        print(f"  Raw JSON keys: {list(j.raw_extracted_json.keys())}")
        # It may have extracted but just didn't finish saving — fix it
        print("\n  → Fixing status to 'complete'...")
        j.processing_status = 'complete'
        j.save()
        print("  → Fixed!")
    else:
        print("  → No extracted data — extraction may have failed mid-way.")
        print("  → Setting to 'failed' so it doesn't show as processing forever.")
        j.processing_status = 'failed'
        j.save()
