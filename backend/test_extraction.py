import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.cases.models import Judgment
from apps.cases.services.extractor import extract_structured_data

j = Judgment.objects.order_by('-id').first()
print(f"Testing extraction on Case ID: {j.id}, Status: {j.processing_status}")

header = "This is a test header text from the High Court."
middle = "This is a test middle section."
operative = "The petition is allowed. The fine is 500 rupees."

try:
    print("Calling extract_structured_data...")
    res = extract_structured_data(str(j.id), header, middle, operative)
    print("Result:")
    print(res)
except Exception as e:
    print(f"Exception caught: {e}")
