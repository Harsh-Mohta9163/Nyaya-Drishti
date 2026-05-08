import os, django, json
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()
from apps.cases.models import Case, Judgment

j = Judgment.objects.get(case__case_number__startswith='MFA No.20338')
raw = j.raw_extracted_json or {}

# Fix compliance data — unwrap from schema wrapper
if "compliance" in raw:
    c = raw["compliance"]
    if "$defs" in c or ("properties" in c and "type" in c):
        c = c.get("properties", c)
        print("Unwrapped compliance from schema wrapper")
    
    j.court_directions = c.get("court_directions", [])
    j.disposition = c.get("disposition", "")
    j.winning_party_type = c.get("winning_party_type", "")
    j.contempt_indicators = c.get("contempt_indicators", [])
    j.contempt_risk = c.get("contempt_risk", "Low")
    j.financial_implications = c.get("financial_implications", [])
    j.save()
    
    print(f"Fixed! court_directions: {len(j.court_directions)} items")
    print(f"disposition: {j.disposition}")
    print(f"winning_party: {j.winning_party_type}")
    for d in j.court_directions:
        print(f"  - {d.get('text', '')[:120]}")
else:
    print("No compliance data found")
