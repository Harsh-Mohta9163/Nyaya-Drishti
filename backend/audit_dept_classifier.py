"""One-shot audit of the department classifier against existing cases.

Run from backend/ with:  python audit_dept_classifier.py
Prints per-case ranking so a human can eyeball whether the AI dept is correct.
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.cases.models import Case
from apps.cases.services.dept_classifier import classify


def _gather_text(case: Case) -> tuple[str, list, tuple]:
    """Mirror what extractor.py feeds the classifier."""
    judgment = case.judgments.first()
    body_text = ""
    operative_text = ""
    entities: list = []
    if judgment:
        body_text = " ".join(filter(None, [
            judgment.summary_of_facts or "",
            " ".join(judgment.issues_framed or []),
            judgment.ratio_decidendi or "",
        ]))
        directions_raw = judgment.court_directions or []
        directions_strs = []
        for d in directions_raw:
            if isinstance(d, str):
                directions_strs.append(d)
            elif isinstance(d, dict):
                directions_strs.append(" ".join(str(v) for v in d.values() if isinstance(v, str)))
        operative_text = (judgment.operative_order_text or "") + " " + " ".join(directions_strs)
        ents = judgment.entities or {}
        if isinstance(ents, dict):
            for v in ents.values():
                if isinstance(v, list):
                    entities.extend(v)
        elif isinstance(ents, list):
            entities = list(ents)
    case_text = (operative_text + " " + body_text)[:8000]
    parties = (case.petitioner_name or "", case.respondent_name or "")
    return case_text, entities, parties


def main() -> None:
    cases = Case.objects.all().order_by("created_at")
    print(f"\n=== Auditing {cases.count()} cases ===\n")
    for i, case in enumerate(cases, 1):
        case_text, entities, parties = _gather_text(case)
        result = classify(case_text, entities, parties)

        current = case.primary_department.code if case.primary_department else "<none>"
        secondary_now = [d.code for d in case.secondary_departments.all()]

        print(f"--- Case {i}: {case.case_number or case.id} ---")
        print(f"  Area of law:  {(case.area_of_law or '')[:90]}")
        print(f"  Statute:      {(case.primary_statute or '')[:90]}")
        print(f"  Petitioner:   {(case.petitioner_name or '')[:80]}")
        print(f"  Respondent:   {(case.respondent_name or '')[:80]}")
        print(f"  DB primary:   {current}   secondary={secondary_now}")
        print(f"  AI primary:   {result['primary']}  secondary={result['secondary']}  "
              f"conf={result['confidence']}  method={result['method']}")
        print()


if __name__ == "__main__":
    main()
