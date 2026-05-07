import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()
from apps.cases.models import Case, Judgment

for c in Case.objects.all().order_by('-created_at'):
    j = c.judgments.first()
    if j:
        print(f"{c.id} | {c.case_number} | status={j.processing_status} | raw={bool(j.raw_extracted_json)} | dirs={len(j.court_directions) if j.court_directions else 0} | pdf={bool(j.pdf_file)}")
    else:
        print(f"{c.id} | {c.case_number} | NO JUDGMENT")
