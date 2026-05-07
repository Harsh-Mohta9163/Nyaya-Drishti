import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from apps.cases.models import Case, Judgment

total = Case.objects.count()
unknown = Case.objects.filter(court_name__startswith='Unknown').count()
known = total - unknown
print(f"Total cases in DB: {total}")
print(f"Unknown (failed extraction): {unknown}")
print(f"Fully extracted: {known}")

print("\n=== FAILED (Unknown) - last 5 ===")
for j in Judgment.objects.filter(case__court_name__startswith='Unknown').order_by('-created_at')[:5]:
    ts = j.created_at.strftime("%H:%M:%S")
    print(f"  {j.case.case_number} | status={j.processing_status} | created={ts}")

print("\n=== SUCCESSFULLY EXTRACTED ===")
for c in Case.objects.exclude(court_name__startswith='Unknown').order_by('-created_at'):
    j = c.judgments.first()
    ts = c.created_at.strftime("%H:%M:%S")
    disp = j.disposition if j else "?"
    print(f"  {c.case_number} | {disp} | created={ts}")
