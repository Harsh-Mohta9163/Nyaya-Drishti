import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from apps.cases.services.pdf_processor import extract_text_from_pdf

md = extract_text_from_pdf('KAHC020023352011_1.pdf')
print(f"Total chars: {len(md)}")
print(f"First 500 chars:\n{md[:500]}")
