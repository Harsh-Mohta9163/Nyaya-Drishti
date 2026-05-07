"""
NyayaDrishti — RAG Pipeline V2 Test (Post-Fix)

Run from backend/: python test_rag_v2.py

Tests the FIXED pipeline:
  1. ChromaDB retrieval WITHOUT area_of_law filter
  2. Full 4-Agent pipeline with real SC case scenarios
  3. Quality analysis of the retrieved chunks + LLM output
"""
import os
import sys
import json
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from apps.action_plans.services.rag_engine import HybridRAGEngine, _rebuild_bm25, _get_collection
from apps.action_plans.services.recommendation_pipeline import generate_recommendation

DIVIDER = "=" * 80

def check_chromadb():
    """Quick sanity check."""
    col = _get_collection()
    count = col.count()
    print(f"ChromaDB chunks: {count}")
    if count == 0:
        print("❌ EMPTY! Run: python manage.py import_kaggle_embeddings --path .")
        sys.exit(1)
    return count


def test_retrieval_no_filter():
    """Test retrieval WITHOUT area_of_law filter — the core fix."""
    print(f"\n{DIVIDER}")
    print("TEST 1: Retrieval Quality (NO area_of_law filter)")
    print(DIVIDER)

    _rebuild_bm25()
    rag = HybridRAGEngine()

    queries = [
        {
            "name": "Service Law — Compulsory Retirement",
            "text": (
                "The appellant a Grade-A officer in the Indian Administrative Service was "
                "compulsorily retired from service by the Union of India under Rule 16(3) "
                "of the All India Services Death-cum-Retirement Benefits Rules 1958. "
                "The appellant contends that the order was passed without material on "
                "record and violates Articles 14 and 16 of the Constitution. The adverse "
                "entries were never communicated to him."
            ),
        },
        {
            "name": "Criminal — Murder / Section 302 IPC",
            "text": (
                "The accused was convicted under Section 302 of the Indian Penal Code "
                "for the murder of the deceased. The prosecution case was that the "
                "accused stabbed the victim with a knife. The trial court sentenced "
                "the accused to life imprisonment. The High Court confirmed the "
                "conviction. The accused now appeals to the Supreme Court challenging "
                "the conviction on grounds of insufficient evidence and contradictions "
                "in eyewitness testimony."
            ),
        },
        {
            "name": "Tax — Section 148 Reassessment",
            "text": (
                "The assessee challenges the reassessment order under Section 148 of "
                "the Income Tax Act 1961. The Assessing Officer reopened the assessment "
                "after four years alleging that income had escaped assessment. The "
                "petitioner argues that there was no fresh tangible material to justify "
                "reopening and the original assessment was completed after due scrutiny."
            ),
        },
        {
            "name": "Constitutional — Article 21 Right to Life",
            "text": (
                "The petitioner a prisoner on death row filed a writ petition under "
                "Article 32 of the Constitution seeking commutation of the death "
                "sentence to life imprisonment on the ground of inordinate delay "
                "in execution of the sentence. The delay of 14 years amounts to "
                "cruel and unusual punishment violating Article 21."
            ),
        },
    ]

    for q in queries:
        print(f"\n{'─' * 60}")
        print(f"🔍 {q['name']}")

        results = rag.retrieve(q["text"], top_k=5, filters=None)
        print(f"   Retrieved: {len(results)} chunks")

        if not results:
            print("   ⚠️  No results!")
            continue

        seen_cases = set()
        for j, r in enumerate(results):
            m = r.get("metadata", {})
            cid = m.get("case_id", "?")
            if cid in seen_cases:
                dup_label = " (DUPLICATE CASE)"
            else:
                dup_label = ""
                seen_cases.add(cid)
            print(f"   #{j+1} | Score {r.get('score', 0):.2f} | {m.get('disposal_nature', '?'):25s} | {m.get('area_of_law', '?'):18s} | {m.get('title', '?')[:60]}{dup_label}")
            print(f"        Text: {r.get('text', '')[:120]}...")

        # Quality: How many unique cases?
        print(f"   → {len(seen_cases)} unique cases out of {len(results)} chunks")


def test_full_pipeline_sc_won():
    """SC appeal that was WON (service law — compulsory retirement overturned)."""
    print(f"\n{DIVIDER}")
    print("TEST 2A: Full Pipeline — SC Appeal WON Scenario")
    print(DIVIDER)

    case_text = """
    The appellant, a Grade-A officer in the Indian Administrative Service, was compulsorily
    retired from service by the Union of India under Rule 16(3) of the All India Services
    (Death-cum-Retirement Benefits) Rules, 1958. The appellant contends that the order of
    compulsory retirement was passed without any material on record to justify the same,
    and that it violates Articles 14 and 16 of the Constitution. The Central Administrative
    Tribunal had dismissed the appellant's original application. The High Court also dismissed
    the writ petition. The appellant now appeals to this Court by special leave.

    The respondent (Union of India) argues that the review committee had found adverse entries
    in the service record for the years 2018-2022 and that the decision was taken in public
    interest. The appellant argues these entries were never communicated to him and he was
    given no opportunity to represent against them, violating principles of natural justice.

    Key legal issues:
    1. Whether compulsory retirement can be ordered based on uncommunicated adverse entries?
    2. Whether the decision of the review committee was arbitrary?
    3. Whether the principles of natural justice were violated?
    """

    print("Calling pipeline (30-60 sec)...")
    try:
        result = generate_recommendation(
            case_id="TEST-SC-WON-001",
            case_text=case_text,
            area_of_law="service",
            court="Supreme Court of India"
        )
        print(f"\n✅ Pipeline completed!")
        print(f"\n📋 Decision: {result['verdict']['decision']}")
        print(f"   Confidence: {result['verdict']['confidence']}")
        print(f"   Appeal To: {result['verdict']['appeal_to']}")
        print(f"   Urgency: {result['verdict']['urgency']}")
        print(f"   Cases Analyzed: {result['statistical_basis']['similar_cases_analyzed']}")
        print(f"\n   Reasoning: {result['primary_reasoning'][:300]}")
        print(f"\n   Appeal Grounds:")
        for g in result.get("appeal_grounds", []):
            print(f"     • {g[:120]}")
        print(f"\n   Full JSON:\n{json.dumps(result, indent=2, default=str)}")
        return result
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_full_pipeline_sc_lost():
    """SC appeal that was LOST (criminal conviction upheld)."""
    print(f"\n{DIVIDER}")
    print("TEST 2B: Full Pipeline — SC Appeal LOST Scenario")
    print(DIVIDER)

    case_text = """
    The appellant was convicted by the Trial Court under Section 302 of the Indian Penal
    Code for the murder of his wife. The prosecution established through eyewitness
    testimony and forensic evidence that the appellant killed his wife by strangulation
    at their matrimonial home. The medical evidence including post-mortem report confirmed
    death by asphyxiation consistent with manual strangulation.

    The High Court upheld the conviction and sentence of life imprisonment. The appellant
    now appeals to this Court contending:
    1. The eyewitnesses are family members of the deceased and are interested witnesses
    2. The circumstantial evidence chain is incomplete
    3. The motive was not established by the prosecution

    The prosecution argues that the medical evidence corroborates the eyewitness accounts,
    the appellant was found at the scene, and his conduct after the incident was indicative
    of guilt. The dying declaration of the deceased naming the appellant was recorded by
    the Magistrate.

    This is a case where the government (as prosecution) has consistently succeeded through
    the Trial Court and High Court.
    """

    print("Calling pipeline (30-60 sec)...")
    try:
        result = generate_recommendation(
            case_id="TEST-SC-LOST-001",
            case_text=case_text,
            area_of_law="criminal",
            court="Supreme Court of India"
        )
        print(f"\n✅ Pipeline completed!")
        print(f"\n📋 Decision: {result['verdict']['decision']}")
        print(f"   Confidence: {result['verdict']['confidence']}")
        print(f"   Appeal To: {result['verdict']['appeal_to']}")
        print(f"   Urgency: {result['verdict']['urgency']}")
        print(f"   Cases Analyzed: {result['statistical_basis']['similar_cases_analyzed']}")
        print(f"\n   Reasoning: {result['primary_reasoning'][:300]}")
        print(f"\n   Appeal Grounds:")
        for g in result.get("appeal_grounds", []):
            print(f"     • {g[:120]}")
        print(f"\n   Full JSON:\n{json.dumps(result, indent=2, default=str)}")
        return result
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print(f"\n{'#' * 80}")
    print("  NyayaDrishti RAG Pipeline V2 — Post-Fix Test")
    print(f"{'#' * 80}")

    check_chromadb()

    # Test 1: Retrieval quality (should now work without broken filter)
    test_retrieval_no_filter()

    # Test 2: Full pipeline
    print(f"\n{'─' * 60}")
    run = input("\nRun full pipeline tests? (Uses NVIDIA API) [y/N]: ").strip().lower()
    if run == 'y':
        test_full_pipeline_sc_won()
        
        print(f"\n{'─' * 60}")
        run2 = input("\nRun SC-LOST test too? [y/N]: ").strip().lower()
        if run2 == 'y':
            test_full_pipeline_sc_lost()

    print(f"\n{'#' * 80}")
    print("  V2 Test Suite Complete")
    print(f"{'#' * 80}\n")
