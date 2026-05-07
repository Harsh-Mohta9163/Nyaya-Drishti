import os
import django
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.cases.models import Case, Judgment, Citation

cases = Case.objects.exclude(case_number__startswith='tmp')[:2]

for c in cases:
    j = c.judgments.first()
    print(f"\n{'='*60}")
    print(f"CASE: {c.case_number}")
    print(f"{'='*60}")

    print(f"\n--- Case model fields ---")
    print(f"  court_name:          {c.court_name}")
    print(f"  case_type:           {c.case_type}")
    print(f"  case_year:           {c.case_year}")
    print(f"  petitioner_name:     {c.petitioner_name}")
    print(f"  respondent_name:     {c.respondent_name}")
    print(f"  area_of_law:         '{c.area_of_law}'")
    print(f"  primary_statute:     '{c.primary_statute}'")
    print(f"  status:              {c.status}")

    print(f"\n--- Judgment model fields ---")
    print(f"  date_of_order:       {j.date_of_order}")
    print(f"  document_type:       {j.document_type}")
    print(f"  presiding_judges:    {j.presiding_judges}")
    print(f"  disposition:         '{j.disposition}'")
    print(f"  winning_party_type:  '{j.winning_party_type}'")
    print(f"  appeal_type:         '{j.appeal_type}'")
    print(f"  contempt_risk:       '{j.contempt_risk}'")
    print(f"  contempt_indicators: {j.contempt_indicators}")
    print(f"  financial_implications: {j.financial_implications}")
    print(f"  entities:            {j.entities}")
    print(f"  processing_status:   {j.processing_status}")
    print(f"  extraction_confidence: {j.extraction_confidence}")

    print(f"\n--- Summary of Facts ---")
    print(f"  {j.summary_of_facts[:300] if j.summary_of_facts else '(EMPTY)'}...")

    print(f"\n--- Issues Framed ---")
    if j.issues_framed:
        for i, issue in enumerate(j.issues_framed, 1):
            print(f"  {i}. {issue}")
    else:
        print("  (EMPTY)")

    print(f"\n--- Ratio Decidendi ---")
    print(f"  {j.ratio_decidendi[:200] if j.ratio_decidendi else '(EMPTY)'}...")

    print(f"\n--- Court Directions ---")
    if j.court_directions:
        for d in j.court_directions:
            print(f"  - Entity: {d.get('responsible_entity')} | Action: {d.get('action_required')} | Deadline: {d.get('deadline_mentioned')}")
    else:
        print("  (EMPTY)")

    print(f"\n--- Citations (raw_extracted_json._cases_cited) ---")
    citations = j.raw_extracted_json.get("_cases_cited", []) if j.raw_extracted_json else []
    if citations:
        for cit in citations:
            print(f"  - {cit}")
    else:
        print("  (EMPTY)")

    print(f"\n--- Raw Extracted JSON keys ---")
    print(f"  {list(j.raw_extracted_json.keys()) if j.raw_extracted_json else '(EMPTY)'}")
