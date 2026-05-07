"""
Nyaya-Drishti: Case Inspection Script
======================================
Displays ALL fields from the Case, Judgment, and Citation tables for a given case.
Also shows the PDF file path so you can open the source document to verify.

Usage:
  python inspect_case.py                     # Shows ALL cases with a numbered list, then you pick one
  python inspect_case.py --case "WP No. 98"  # Search by case number substring
"""
import os
import sys
import json
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.cases.models import Case, Judgment, Citation


def print_divider(char="=", width=80):
    print(char * width)


def print_section(title):
    print(f"\n--- {title} ---")


def display_case(case):
    """Display all fields for a single case, its judgments, and citations."""
    print_divider()
    print(f"  CASE: {case.case_number}")
    print_divider()

    # ===== CASE TABLE =====
    print_section("CASE TABLE (apps.cases.models.Case)")
    fields = [
        ("id", case.id),
        ("matter_id", case.matter_id),
        ("cnr_number", case.cnr_number or "(empty)"),
        ("court_name", case.court_name),
        ("case_type", case.case_type),
        ("case_number", case.case_number),
        ("case_year", case.case_year),
        ("petitioner_name", case.petitioner_name or "(empty)"),
        ("respondent_name", case.respondent_name or "(empty)"),
        ("status", case.status),
        ("area_of_law", case.area_of_law or "(MISSING)"),
        ("primary_statute", case.primary_statute or "(MISSING)"),
        ("appealed_from_case", case.appealed_from_case_id or "(none)"),
        ("created_at", case.created_at),
        ("updated_at", case.updated_at),
    ]
    max_label = max(len(f[0]) for f in fields)
    for label, value in fields:
        marker = " <<<< EMPTY" if value in ("(empty)", "(MISSING)") else ""
        print(f"  {label:<{max_label+2}} {value}{marker}")

    # ===== JUDGMENT TABLE =====
    judgments = case.judgments.all()
    if not judgments.exists():
        print_section("JUDGMENT TABLE")
        print("  (No judgments found for this case)")
        return

    for j in judgments:
        print_section(f"JUDGMENT TABLE (apps.cases.models.Judgment) - {j.id}")
        j_fields = [
            ("id", j.id),
            ("date_of_order", j.date_of_order),
            ("document_type", j.document_type),
            ("presiding_judges", j.presiding_judges),
            ("disposition", j.disposition or "(MISSING)"),
            ("winning_party_type", j.winning_party_type or "(MISSING)"),
            ("appeal_type", j.appeal_type or "(MISSING)"),
            ("contempt_risk", j.contempt_risk or "(MISSING)"),
            ("contempt_indicators", j.contempt_indicators),
            ("financial_implications", j.financial_implications),
            ("entities", j.entities),
            ("extraction_confidence", j.extraction_confidence),
            ("processing_status", j.processing_status),
            ("pdf_file", j.pdf_file.name if j.pdf_file else "(no PDF)"),
        ]
        max_label_j = max(len(f[0]) for f in j_fields)
        for label, value in j_fields:
            marker = " <<<< EMPTY" if value in ("(MISSING)",) else ""
            print(f"  {label:<{max_label_j+2}} {value}{marker}")

        # Show the actual PDF path on disk
        if j.pdf_file:
            from django.conf import settings
            pdf_full_path = os.path.join(settings.MEDIA_ROOT, j.pdf_file.name)
            print(f"\n  PDF ON DISK: {pdf_full_path}")
            if os.path.exists(pdf_full_path):
                size_kb = os.path.getsize(pdf_full_path) / 1024
                print(f"  PDF EXISTS:  Yes ({size_kb:.1f} KB)")
            else:
                print(f"  PDF EXISTS:  NO (file not found)")

        # Extracted text fields
        print_section("SUMMARY OF FACTS")
        print(f"  {j.summary_of_facts if j.summary_of_facts else '(EMPTY) <<<< MISSING'}")

        print_section("ISSUES FRAMED")
        if j.issues_framed:
            for i, issue in enumerate(j.issues_framed, 1):
                print(f"  {i}. {issue}")
        else:
            print("  (EMPTY) <<<< MISSING")

        print_section("RATIO DECIDENDI")
        print(f"  {j.ratio_decidendi if j.ratio_decidendi else '(EMPTY) <<<< MISSING'}")

        print_section("COURT DIRECTIONS / DIRECTIVES")
        if j.court_directions:
            for i, d in enumerate(j.court_directions, 1):
                print(f"  {i}. Entity: {d.get('responsible_entity', '?')}")
                print(f"     Action: {d.get('action_required', '?')}")
                print(f"     Text:   {d.get('text', '?')[:200]}")
                print(f"     Deadline: {d.get('deadline_mentioned') or d.get('deadline_date_iso') or 'None'}")
        else:
            print("  (EMPTY - may be correct if no actionable directives exist)")

        # ===== CITATIONS =====
        print_section("CITATIONS (apps.cases.models.Citation)")
        citations = Citation.objects.filter(citing_judgment=j)
        if citations.exists():
            for i, c in enumerate(citations, 1):
                print(f"  {i}. {c.cited_case_name_raw}")
                print(f"     Citation ID: {c.citation_id_raw or '(none)'}")
                print(f"     Context:     {c.citation_context}")
        else:
            print("  (EMPTY - check if this judgment truly cites no precedents)")

        # ===== RAW JSON KEYS =====
        print_section("RAW EXTRACTED JSON (keys)")
        if j.raw_extracted_json:
            print(f"  Keys: {list(j.raw_extracted_json.keys())}")
        else:
            print("  (EMPTY)")

    print_divider()


def main():
    search = None
    if "--case" in sys.argv:
        idx = sys.argv.index("--case")
        if idx + 1 < len(sys.argv):
            search = sys.argv[idx + 1]

    if search:
        cases = Case.objects.filter(case_number__icontains=search)
        if not cases.exists():
            print(f"No cases found matching '{search}'")
            return
        for c in cases:
            display_case(c)
    else:
        cases = list(Case.objects.all().order_by("-created_at"))
        if not cases:
            print("No cases in the database.")
            return

        print(f"\nFound {len(cases)} cases in the database:\n")
        for i, c in enumerate(cases, 1):
            j = c.judgments.first()
            disp = j.disposition if j else "?"
            print(f"  [{i}] {c.case_number} | {c.court_name} | Disposition: {disp}")

        print(f"\nEnter a number (1-{len(cases)}) to inspect, or 'all' to show all, or 'q' to quit:")
        choice = input("> ").strip()

        if choice.lower() == "q":
            return
        elif choice.lower() == "all":
            for c in cases:
                display_case(c)
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(cases):
                    display_case(cases[idx])
                else:
                    print(f"Invalid number. Choose 1-{len(cases)}")
            except ValueError:
                print("Invalid input.")


if __name__ == "__main__":
    main()
