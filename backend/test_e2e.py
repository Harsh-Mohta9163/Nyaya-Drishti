"""
NyayaDrishti — Full End-to-End Pipeline Test with Real PDFs

Run: python test_e2e.py

Pipeline:
  PDF → PyMuPDF → Segment → 4-Agent Extractor → Save to DB → RAG Retrieval → 4-Agent Recommendation
"""
import os
import sys
import json
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

import fitz  # PyMuPDF
from apps.cases.services.pdf_processor import extract_text_from_pdf
from apps.cases.services.section_segmenter import segment_judgment
from apps.cases.services.extractor import extract_structured_data
from apps.cases.models import Case, Judgment
from apps.action_plans.services.rag_engine import HybridRAGEngine, _rebuild_bm25
from apps.action_plans.services.recommendation_pipeline import generate_recommendation

DIVIDER = "=" * 80

# ── The two real PDFs ──────────────────────────────────────────────────────────
PDFS = [
    {
        "path": os.path.join(os.path.dirname(__file__), "hs-gaurav-v-state-of-karnataka-ors-2025-1458815.pdf"),
        "label": "PDF 1: HS Gaurav v. State of Karnataka (2025)",
    },
    {
        "path": os.path.join(os.path.dirname(__file__), "KAHC010139132023_1.pdf"),
        "label": "PDF 2: KAHC010139132023",
    },
]


def stage_1_extract_text(pdf_path: str) -> str:
    """PyMuPDF → raw markdown text."""
    print(f"\n  📄 Stage 1: Extracting text from PDF...")
    text = extract_text_from_pdf(pdf_path)
    print(f"     Extracted {len(text)} characters")
    print(f"     Preview: {text[:300]}...")
    return text


def stage_2_segment(markdown_text: str) -> dict:
    """Regex segmenter → header / middle / operative_order."""
    print(f"\n  ✂️  Stage 2: Segmenting judgment...")
    segments = segment_judgment(markdown_text)
    for key, val in segments.items():
        print(f"     {key}: {len(val)} chars")
    return segments


def stage_3_extract(segments: dict) -> tuple:
    """4-Agent LLM Extractor → structured data saved to DB."""
    print(f"\n  🤖 Stage 3: Running 4-Agent LLM Extractor...")
    print(f"     Agent 1 (Registry/8B) + Agent 4 (Compliance/8B) + Agent 2 (Analyst/70B) + Agent 3 (Scholar/70B)")
    print(f"     This will take 1-3 minutes (4 LLM calls)...\n")

    # Create a temporary Case + Judgment in the DB
    case = Case.objects.create(
        court_name="Pending Extraction",
        case_type="Pending",
        case_number="TEST-E2E",
        case_year=2025,
        status=Case.Status.PENDING,
    )

    judgment = Judgment.objects.create(
        case=case,
        date_of_order="2025-01-01",
        processing_status="extracting",
    )

    extracted_data = extract_structured_data(
        judgment_id=str(judgment.id),
        header_text=segments.get("header", ""),
        middle_text=segments.get("middle", ""),
        operative_text=segments.get("operative_order", ""),
    )

    # IMPORTANT: The extractor may delete the original Case and create a new one
    # to avoid duplicates (see extractor.py lines ~279-283).
    # Always reload via judgment to get the current case reference.
    judgment = Judgment.objects.get(id=judgment.id)
    case = judgment.case

    return case, judgment, extracted_data


def stage_4_rag_retrieval(case_text: str) -> list:
    """Query ChromaDB with the extracted facts."""
    print(f"\n  🔍 Stage 4: RAG Retrieval (ChromaDB + BM25 + Cross-Encoder)...")
    _rebuild_bm25()
    rag = HybridRAGEngine()
    results = rag.retrieve(case_text[:2000], top_k=10, filters=None)
    print(f"     Retrieved {len(results)} chunks")

    seen_cases = set()
    for j, r in enumerate(results):
        m = r.get("metadata", {})
        cid = m.get("case_id", "?")
        dup = " (DUP)" if cid in seen_cases else ""
        seen_cases.add(cid)
        print(f"     #{j+1} | Score {r.get('score', 0):.2f} | {m.get('disposal_nature', '?'):22s} | {m.get('title', '?')[:55]}{dup}")

    print(f"     → {len(seen_cases)} unique cases")
    return results


def stage_5_recommendation(case_id: str, case_text: str, area_of_law: str, court: str, **kwargs) -> dict:
    """Full 4-Agent Recommendation Pipeline V2."""
    print(f"\n  🧠 Stage 5: 4-Agent Recommendation Pipeline V2...")
    print(f"     Agent 1 (Research/NVIDIA) → Agent 2 (Arguments/NVIDIA) → Agent 3 (Risk/NVIDIA) → Agent 4 (Synthesis/NVIDIA)")
    print(f"     This will take 2-4 minutes (4 NVIDIA Llama 3.3 70B calls)...\n")

    result = generate_recommendation(
        case_id=case_id,
        case_text=case_text,
        area_of_law=area_of_law,
        court=court,
        **kwargs,
    )
    return result


def print_extraction_results(case, judgment, extracted_data):
    """Pretty-print what the 4-agent extractor found."""
    print(f"\n  {'─' * 60}")
    print(f"  📋 EXTRACTION RESULTS")
    print(f"  {'─' * 60}")

    reg = extracted_data.get("registry", {})
    print(f"  Case Number:   {reg.get('case_number', 'N/A')}")
    print(f"  Court:         {reg.get('court_name', 'N/A')}")
    print(f"  Bench:         {reg.get('bench', 'N/A')}")
    print(f"  Judges:        {reg.get('presiding_judges', [])}")
    print(f"  Case Type:     {reg.get('case_type', 'N/A')}")
    print(f"  Date:          {reg.get('date_of_order', 'N/A')}")
    print(f"  Petitioner:    {reg.get('petitioner_name', 'N/A')}")
    print(f"  Respondent:    {reg.get('respondent_name', 'N/A')}")
    print(f"  Appeal Type:   {reg.get('appeal_type', 'N/A')}")
    print(f"  Lower Court:   {reg.get('lower_court_name', 'N/A')}")

    analyst = extracted_data.get("analyst", {})
    print(f"\n  Summary of Facts:")
    print(f"    {analyst.get('summary_of_facts', 'N/A')[:500]}")
    print(f"\n  Issues Framed:")
    for issue in analyst.get("issues_framed", []):
        print(f"    • {issue[:150]}")

    scholar = extracted_data.get("scholar", {})
    print(f"\n  Ratio Decidendi:")
    print(f"    {scholar.get('ratio_decidendi', 'N/A')[:400]}")
    print(f"  Area of Law:     {scholar.get('area_of_law', 'N/A')}")
    print(f"  Primary Statute: {scholar.get('primary_statute', 'N/A')}")
    print(f"  Citations ({len(scholar.get('citations', []))}):")
    for cit in scholar.get("citations", [])[:5]:
        print(f"    • {cit.get('case_name', '?')[:80]} — {cit.get('context', '?')}")

    comp = extracted_data.get("compliance", {})
    print(f"\n  Disposition:     {comp.get('disposition', 'N/A')}")
    print(f"  Winning Party:   {comp.get('winning_party_type', 'N/A')}")
    print(f"  Contempt Risk:   {comp.get('contempt_risk', 'N/A')}")
    print(f"  Court Directions ({len(comp.get('court_directions', []))}):")
    for d in comp.get("court_directions", [])[:5]:
        print(f"    • [{d.get('responsible_entity', '?')}] {d.get('action_required', '?')[:100]}")
    print(f"  Financial:       {comp.get('financial_implications', [])}")


def print_recommendation_results(result):
    """Pretty-print the final recommendation."""
    print(f"\n  {'─' * 60}")
    print(f"  🏛️  FINAL AI RECOMMENDATION (V2)")
    print(f"  {'─' * 60}")
    v = result.get("verdict", {})
    print(f"  Decision:      {v.get('decision', 'N/A')}")
    print(f"  Appeal To:     {v.get('appeal_to', 'N/A')}")
    print(f"  Confidence:    {v.get('confidence', 'N/A')}")
    print(f"  Urgency:       {v.get('urgency', 'N/A')}")
    print(f"  Deadline:      {v.get('limitation_deadline', 'N/A')} ({v.get('days_remaining', '?')} days)")

    s = result.get("statistical_basis", {})
    print(f"\n  Cases Analyzed: {s.get('similar_cases_analyzed', 0)}")
    print(f"  Corpus Total:  {s.get('total_cases_in_corpus', 0)}")
    print(f"  Allowed Rate:  {s.get('government_appeal_win_rate', 0)}")
    print(f"  Dismissed Rate:{s.get('dismissed_rate', 0)}")

    ao = result.get("agent_outputs", {})
    print(f"\n  Agent Signals:")
    print(f"    Precedent Strength: {ao.get('precedent_strength', '?')}")
    print(f"    Overall Trend:      {ao.get('overall_trend', '?')[:120]}")
    print(f"    Balance:            {ao.get('balance_assessment', '?')}")
    print(f"    Contempt Urgency:   {ao.get('contempt_urgency', '?')}")

    print(f"\n  Primary Reasoning:")
    print(f"    {result.get('primary_reasoning', 'N/A')[:500]}")

    print(f"\n  Risk Summary:")
    print(f"    {result.get('risk_summary', 'N/A')[:300]}")

    print(f"\n  Appeal Grounds:")
    for g in result.get("appeal_grounds", []):
        print(f"    • {g[:150]}")

    print(f"\n  Alternative Routes:")
    for r in result.get("alternative_routes", []):
        print(f"    • {r[:150]}")

    ap = result.get("action_plan", {})
    print(f"\n  Immediate Actions:")
    for a in ap.get("immediate_actions", []):
        print(f"    • {a[:150]}")
    print(f"  Financial Actions:")
    for a in ap.get("financial_actions", []):
        print(f"    • {a[:150]}")


def run_full_pipeline(pdf_info: dict):
    """Run the complete E2E pipeline for one PDF."""
    print(f"\n{'#' * 80}")
    print(f"  {pdf_info['label']}")
    print(f"{'#' * 80}")

    pdf_path = pdf_info["path"]
    if not os.path.exists(pdf_path):
        print(f"  ❌ File not found: {pdf_path}")
        return None

    # Stage 1: Extract text
    markdown_text = stage_1_extract_text(pdf_path)

    # Stage 2: Segment
    segments = stage_2_segment(markdown_text)

    # Stage 3: 4-Agent LLM Extraction
    case, judgment, extracted_data = stage_3_extract(segments)

    # Print extraction results
    print_extraction_results(case, judgment, extracted_data)

    # Stage 4: RAG Retrieval
    # Use the extracted summary_of_facts as the query (this is what the real flow would use)
    facts = extracted_data.get("analyst", {}).get("summary_of_facts", "")
    if not facts:
        facts = markdown_text[:2000]  # fallback to raw text
    
    retrieved = stage_4_rag_retrieval(facts)

    # Stage 5: Full Recommendation (V2 — passes ALL extracted data)
    reg = extracted_data.get("registry", {})
    comp = extracted_data.get("compliance", {})
    scholar = extracted_data.get("scholar", {})
    analyst = extracted_data.get("analyst", {})

    result = stage_5_recommendation(
        case_id=reg.get("case_number", "TEST-E2E"),
        case_text=facts,
        area_of_law=scholar.get("area_of_law", "civil"),
        court=reg.get("court_name", "High Court of Karnataka"),
        disposition=comp.get("disposition", ""),
        winning_party=comp.get("winning_party_type", ""),
        case_type=reg.get("case_type", ""),
        bench=reg.get("bench", ""),
        petitioner=reg.get("petitioner_name", ""),
        respondent=reg.get("respondent_name", ""),
        issues=analyst.get("issues_framed", []),
    )

    # Print recommendation
    print_recommendation_results(result)

    # Save full JSON
    out_name = os.path.splitext(os.path.basename(pdf_path))[0] + "_result.json"
    out_path = os.path.join(os.path.dirname(__file__), out_name)
    with open(out_path, "w") as f:
        json.dump({
            "extraction": extracted_data,
            "rag_chunks_count": len(retrieved),
            "recommendation": result,
        }, f, indent=2, default=str)
    print(f"\n  💾 Full result saved to: {out_name}")

    return result


if __name__ == "__main__":
    print(f"\n{'#' * 80}")
    print(f"  NyayaDrishti — Full End-to-End Pipeline Test")
    print(f"  PDF → Extract → Segment → 4-Agent LLM → RAG → 4-Agent Recommendation")
    print(f"{'#' * 80}")

    # Check PDFs exist
    for p in PDFS:
        exists = "✅" if os.path.exists(p["path"]) else "❌ NOT FOUND"
        print(f"  {exists} {p['label']}")

    # Process each PDF
    for i, pdf_info in enumerate(PDFS):
        print(f"\n{'━' * 80}")
        print(f"  Processing PDF {i+1} of {len(PDFS)}")
        print(f"{'━' * 80}")

        proceed = input(f"\n  Run pipeline for {pdf_info['label']}? [y/N]: ").strip().lower()
        if proceed != 'y':
            print("  Skipped.")
            continue

        try:
            run_full_pipeline(pdf_info)
        except Exception as e:
            print(f"\n  ❌ Pipeline FAILED: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'#' * 80}")
    print(f"  E2E Test Complete")
    print(f"{'#' * 80}\n")
