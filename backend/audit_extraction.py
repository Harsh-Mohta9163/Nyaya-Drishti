"""Deep audit: Compare PDF content vs extraction output."""
import django, os, json
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from apps.cases.models import Judgment, Case
from apps.cases.services.pdf_processor import extract_text_from_pdf
from apps.cases.services.section_segmenter import segment_judgment

# 1. Read the actual PDF text
pdf_path = r"C:\Users\HARSH MOHTA\OneDrive - iiit-b\Desktop\Nyaya-Drishti\backend\KAHC020023352011_1.pdf"
markdown_text = extract_text_from_pdf(pdf_path)
segments = segment_judgment(markdown_text)

print(f"=== DOCUMENT STATS ===")
print(f"Full text: {len(markdown_text)} chars")
print(f"Header: {len(segments['header'])} chars")
print(f"Middle: {len(segments['middle'])} chars")
print(f"Operative: {len(segments['operative_order'])} chars")
print()

print(f"\n{'='*80}")
print("OPERATIVE ORDER TEXT (what the Compliance Officer Agent received)")
print(f"{'='*80}")
print(segments['operative_order'][:5000])

print(f"\n\n{'='*80}")
print("LAST 3000 CHARS OF FULL TEXT (the actual ending)")
print(f"{'='*80}")
print(markdown_text[-3000:])

# 2. Show what we extracted
print(f"\n\n{'='*80}")
print("WHAT WE EXTRACTED AS COURT DIRECTIONS (currently displayed)")
print(f"{'='*80}")
j = Judgment.objects.get(id='2521e1ff-aced-4761-9b2a-66f947c05a1e')
dirs = j.court_directions or []
for i, d in enumerate(dirs):
    print(f"\n--- Direction {i+1} ---")
    print(f"  Title: {d.get('action_required')}")
    print(f"  Full Text: {d.get('text')}")
    print(f"  Entity: {d.get('responsible_entity')}")
    print(f"  Deadline: {d.get('deadline_mentioned')}")

print(f"\n--- Operative Order Text Field ---")
oot = j.operative_order_text or ""
print(oot[:500] if oot else "EMPTY!")

# 3. Financial implications
print(f"\n--- Financial Implications ---")
print(j.financial_implications)

# 4. RAG check
print(f"\n\n{'='*80}")
print("RAG / PRECEDENT CHECK")
print(f"{'='*80}")
from apps.action_plans.models import ActionPlan
ap = ActionPlan.objects.filter(judgment=j).first()
if ap and ap.full_rag_recommendation:
    rec = ap.full_rag_recommendation
    precs = rec.get('legal_precedents', [])
    print(f"Precedents found: {len(precs)}")
    for p in precs:
        print(f"  - {p.get('case_title', p.get('case_id', '?'))}: {p.get('relevance', '')[:100]}")
    
    # Show the actual AI reasoning
    print(f"\n--- AI Reasoning ---")
    print(rec.get('primary_reasoning', '')[:500])
    print(f"\n--- AI Verdict ---")
    print(json.dumps(rec.get('verdict', {}), indent=2))
