"""
Nyaya-Drishti: PDF vs Extraction Verification Script
=====================================================
Reads a stored PDF, shows the raw text, the segmenter output,
and compares it side-by-side with the LLM extraction.

Usage:
  python verify_extraction.py                   # Pick from list
  python verify_extraction.py --case "WP No. 98"   # By case number
"""
import os
import sys
import django
import textwrap

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.cases.models import Case, Judgment
from apps.cases.services.pdf_processor import extract_text_from_pdf
from apps.cases.services.section_segmenter import segment_judgment


def wrap(text, width=100, max_lines=15):
    """Wrap and truncate text for display."""
    if not text:
        return "(EMPTY)"
    lines = textwrap.fill(text, width=width).split("\n")
    if len(lines) > max_lines:
        lines = lines[:max_lines] + [f"  ... ({len(lines) - max_lines} more lines)"]
    return "\n".join(lines)


def verify_case(case):
    j = case.judgments.first()
    if not j:
        print(f"  No judgment found for case {case.case_number}")
        return

    print("=" * 100)
    print(f"  CASE: {case.case_number} | {case.court_name}")
    print("=" * 100)

    # --- Get the PDF and re-extract text ---
    pdf_path = None
    if j.pdf_file:
        from django.conf import settings
        pdf_path = os.path.join(settings.MEDIA_ROOT, j.pdf_file.name)

    if not pdf_path or not os.path.exists(pdf_path):
        print(f"  PDF NOT FOUND: {pdf_path}")
        print(f"  Cannot verify extraction without source PDF.")
        return

    pdf_size_kb = os.path.getsize(pdf_path) / 1024
    print(f"\n  PDF: {pdf_path} ({pdf_size_kb:.1f} KB)")

    # Re-extract raw text from PDF
    raw_text = extract_text_from_pdf(pdf_path)
    page_count_estimate = max(1, len(raw_text) // 3000)  # ~3000 chars per page

    print(f"  Raw text: {len(raw_text)} characters (~{page_count_estimate} pages)")

    # Re-segment
    sections = segment_judgment(raw_text)
    header_len = len(sections.get("header", ""))
    middle_len = len(sections.get("middle", ""))
    operative_len = len(sections.get("operative_order", ""))
    total_len = len(raw_text)

    print(f"\n  SEGMENTATION:")
    print(f"    Header:    {header_len:>6} chars ({header_len*100//max(total_len,1)}%)")
    print(f"    Middle:    {middle_len:>6} chars ({middle_len*100//max(total_len,1)}%)")
    print(f"    Operative: {operative_len:>6} chars ({operative_len*100//max(total_len,1)}%)")

    # Check if this is likely a short interim order
    if total_len < 3000:
        print(f"\n  >>> WARNING: Very short document ({total_len} chars). Likely an INTERIM ORDER, not a full judgment.")
    elif operative_len < 50:
        print(f"\n  >>> WARNING: Operative section is tiny ({operative_len} chars). May be missing the ORDER heading.")

    # --- Show raw operative text from PDF ---
    print(f"\n{'='*50} RAW OPERATIVE TEXT FROM PDF {'='*50}")
    print(wrap(sections.get("operative_order", ""), max_lines=20))

    # --- Field-by-field comparison ---
    print(f"\n{'='*50} EXTRACTION vs PDF VERIFICATION {'='*50}")

    fields = [
        ("case_number", case.case_number, "From header text"),
        ("court_name", case.court_name, "From header text"),
        ("petitioner_name", case.petitioner_name, "From header text"),
        ("respondent_name", case.respondent_name, "From header text"),
        ("case_type", case.case_type, "From header text"),
        ("area_of_law", case.area_of_law, "LLM inferred"),
        ("primary_statute", case.primary_statute, "LLM inferred"),
        ("date_of_order", str(j.date_of_order), "From header text"),
        ("presiding_judges", str(j.presiding_judges), "From header text"),
        ("disposition", j.disposition, "From operative text"),
        ("winning_party_type", j.winning_party_type, "From operative text"),
        ("appeal_type", j.appeal_type, "LLM inferred"),
        ("contempt_risk", j.contempt_risk, "LLM assessed"),
    ]

    for field_name, value, source in fields:
        status = "OK" if value and value not in ("", "[]", "none", "Low") else "EMPTY"
        marker = " <<<" if status == "EMPTY" and field_name not in ("contempt_risk",) else ""
        print(f"  {field_name:<25} {str(value)[:80]:<80} [{source}]{marker}")

    # --- Appeal lineage (from raw_extracted_json) ---
    raw_json = j.raw_extracted_json or {}
    registry_data = raw_json.get("registry", {})
    is_appeal = registry_data.get("is_appeal_from_lower_court", False)
    print(f"\n--- appeal_lineage ---")
    if is_appeal:
        lc_name = registry_data.get("lower_court_name", "Unknown")
        lc_case = registry_data.get("lower_court_case_number", "Unknown")
        lc_decision = registry_data.get("lower_court_decision", "Unknown")
        print(f"  IS APPEAL: Yes")
        print(f"  Lower court: {lc_name}")
        print(f"  Lower court case: {lc_case}")
        print(f"  Lower court decision: {lc_decision}")
    else:
        print(f"  IS APPEAL: No (original petition)")

    # --- Check text fields ---
    print(f"\n--- summary_of_facts ---")
    if j.summary_of_facts:
        print(f"  Length: {len(j.summary_of_facts)} chars")
        # Check if summary text actually appears related to the PDF
        key_words = j.summary_of_facts.split()[:5]
        found_in_pdf = sum(1 for w in key_words if w.lower() in raw_text.lower())
        print(f"  Verification: {found_in_pdf}/5 key words found in source PDF {'(GOOD)' if found_in_pdf >= 3 else '(CHECK MANUALLY)'}")
    else:
        print(f"  (EMPTY) <<<")

    print(f"\n--- issues_framed ---")
    if j.issues_framed:
        print(f"  Count: {len(j.issues_framed)} issues")
        for i, issue in enumerate(j.issues_framed, 1):
            print(f"  {i}. {issue[:120]}")
    else:
        print(f"  (EMPTY) - may be normal for short orders")

    print(f"\n--- ratio_decidendi ---")
    if j.ratio_decidendi:
        print(f"  Length: {len(j.ratio_decidendi)} chars")
    else:
        print(f"  (EMPTY) <<<")

    print(f"\n--- court_directions ---")
    if j.court_directions:
        print(f"  Count: {len(j.court_directions)} directives")
        for i, d in enumerate(j.court_directions, 1):
            entity = d.get("responsible_entity", "?")
            action = d.get("action_required", "?")
            print(f"  {i}. [{entity}] {action[:100]}")
    else:
        print(f"  (EMPTY) - normal if no actionable orders in operative section")

    print(f"\n--- financial_implications ---")
    if j.financial_implications:
        print(f"  {j.financial_implications}")
    else:
        print(f"  (EMPTY)")

    print(f"\n--- entities ---")
    if j.entities:
        print(f"  {j.entities}")
    else:
        print(f"  (EMPTY) <<<")

    # --- Citations ---
    from apps.cases.models import Citation
    citations = Citation.objects.filter(citing_judgment=j)
    print(f"\n--- citations ---")
    if citations.exists():
        print(f"  Count: {citations.count()}")
        for c in citations:
            ctx = c.citation_context or "Referred"
            ref = f" {c.citation_id_raw}" if c.citation_id_raw else ""
            print(f"  - [{ctx}] {c.cited_case_name_raw[:80]}{ref}")
    else:
        # Check if PDF text mentions any case citations
        import re
        citation_pattern = re.compile(r'\(\d{4}\)\s+\d+\s+SCC\s+\d+|\d{4}\s+AIR\s+\d+|ILR\s+\d{4}', re.IGNORECASE)
        pdf_citations = citation_pattern.findall(raw_text)
        if pdf_citations:
            print(f"  (EMPTY) but PDF contains {len(pdf_citations)} citation-like patterns: {pdf_citations[:3]}")
            print(f"  >>> These should have been extracted!")
        else:
            print(f"  (EMPTY) - PDF also has no obvious citations (correct)")

    print(f"\n{'='*100}\n")


def main():
    search = None
    if "--case" in sys.argv:
        idx = sys.argv.index("--case")
        if idx + 1 < len(sys.argv):
            search = sys.argv[idx + 1]

    if search is not None:
        cases = Case.objects.exclude(court_name__startswith='Unknown').exclude(court_name__startswith='_')
        if search:
            cases = cases.filter(case_number__icontains=search)
        if not cases.exists():
            print(f"No extracted cases found matching '{search}'")
            return
        for c in cases:
            verify_case(c)
    else:
        cases = list(Case.objects.exclude(court_name__startswith='Unknown').exclude(court_name__startswith='_').order_by("-created_at"))
        if not cases:
            print("No successfully extracted cases in the database.")
            return

        print(f"\nFound {len(cases)} successfully extracted cases:\n")
        for i, c in enumerate(cases, 1):
            j = c.judgments.first()
            disp = j.disposition if j else "?"
            print(f"  [{i}] {c.case_number} | {disp}")

        print(f"\nEnter number (1-{len(cases)}), 'all', or 'q':")
        choice = input("> ").strip()

        if choice.lower() == "q":
            return
        elif choice.lower() == "all":
            for c in cases:
                verify_case(c)
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(cases):
                    verify_case(cases[idx])
                else:
                    print(f"Invalid. Choose 1-{len(cases)}")
            except ValueError:
                print("Invalid input.")


if __name__ == "__main__":
    main()
