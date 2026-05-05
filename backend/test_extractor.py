import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.cases.models import Case
from apps.cases.services.extractor import extract_structured_data

case = Case.objects.last()
if case:
    print(f"Testing extraction for case: {case.case_number}")
    sections = {
        "header": "TEST HEADER",
        "operative_order": "1. Allowed. 2. The respondent shall pay Rs. 500."
    }
    result = extract_structured_data(case, sections)
    print(f"Confidence: {result.get('extraction_confidence')}")
else:
    print("No cases found in DB.")
