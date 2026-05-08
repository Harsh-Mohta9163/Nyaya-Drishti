"""Re-ingest the MFA PDF with the improved 70B compliance extraction."""
import django, os, sys, shutil
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from apps.cases.models import Case, Judgment
from apps.cases.services.pdf_processor import extract_text_from_pdf
from apps.cases.services.section_segmenter import segment_judgment
from apps.cases.services.extractor import extract_structured_data
from apps.cases.views import _annotate_source_locations

PDF_SRC = r"C:\Users\HARSH MOHTA\OneDrive - iiit-b\Desktop\Nyaya-Drishti\backend\KAHC020023352011_1.pdf"

print("=" * 60)
print("Step 1: Creating case + judgment")
print("=" * 60)

case = Case.objects.create(
    case_number="PENDING_REINGEST",
    case_year=2011,
    status=Case.Status.PENDING,
)

# Copy PDF to media directory
from django.core.files import File
with open(PDF_SRC, 'rb') as f:
    judgment = Judgment.objects.create(
        case=case,
        date_of_order="2011-01-01",
        processing_status="parsing",
    )
    judgment.pdf_file.save("KAHC020023352011_1.pdf", File(f), save=True)

print(f"  Case ID: {case.id}")
print(f"  Judgment ID: {judgment.id}")

print("\n" + "=" * 60)
print("Step 2: PDF -> Markdown")
print("=" * 60)
pdf_path = judgment.pdf_file.path
markdown_text = extract_text_from_pdf(pdf_path)
print(f"  Text length: {len(markdown_text)} chars")

print("\n" + "=" * 60)
print("Step 3: Segment judgment")
print("=" * 60)
segments = segment_judgment(markdown_text)
print(f"  Header: {len(segments['header'])} chars")
print(f"  Middle: {len(segments['middle'])} chars")
print(f"  Operative: {len(segments['operative_order'])} chars")

print("\n" + "=" * 60)
print("Step 4: 4-Agent Extraction (70B for compliance)")
print("=" * 60)
judgment.processing_status = "extracting"
judgment.save()

try:
    extracted_data = extract_structured_data(
        judgment_id=str(judgment.id),
        header_text=segments.get("header", ""),
        middle_text=segments.get("middle", ""),
        operative_text=segments.get("operative_order", "")
    )
    
    # Refresh
    judgment.refresh_from_db()
    case.refresh_from_db()
    
    # Step 5: Source highlighting
    print("\n" + "=" * 60)
    print("Step 5: Annotating source locations")
    print("=" * 60)
    if judgment.court_directions:
        judgment.court_directions = _annotate_source_locations(pdf_path, judgment.court_directions)
        judgment.save()
    
    # Finalize
    judgment.processing_status = "complete"
    judgment.save()
    
    # Print results
    print("\n" + "=" * 60)
    print("EXTRACTION RESULTS")
    print("=" * 60)
    
    print(f"\nCase: {case.case_number}")
    print(f"Disposition: {judgment.disposition}")
    print(f"Winning party: {judgment.winning_party_type}")
    print(f"Operative Order Text: {(judgment.operative_order_text or 'EMPTY')[:300]}")
    
    print(f"\n--- Court Directions ---")
    dirs = judgment.court_directions or []
    for i, d in enumerate(dirs):
        print(f"\n  Direction {i+1}:")
        print(f"    Title: {d.get('action_required', '')[:200]}")
        print(f"    Entity: {d.get('responsible_entity')}")
        print(f"    Financials: {d.get('financial_details', 'none')}")
        print(f"    Text: {d.get('text', '')[:200]}")
        print(f"    Source: page {d.get('source_location', {}).get('page', '?')}")
    
    print(f"\n--- Financial Implications ---")
    print(judgment.financial_implications)
    
    print(f"\n[OK] DONE! Case re-ingested successfully.")

except Exception as e:
    import traceback
    traceback.print_exc()
    judgment.processing_status = "failed"
    judgment.save()
    print(f"\n[FAIL] FAILED: {e}")
