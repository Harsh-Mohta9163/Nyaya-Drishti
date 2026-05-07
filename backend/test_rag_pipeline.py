"""
NyayaDrishti — End-to-End RAG Pipeline Test Script
Run from backend/: python test_rag_pipeline.py

This script tests:
  1. ChromaDB contents — what's actually stored
  2. Retrieval quality — are we getting relevant chunks
  3. Full recommendation pipeline — does the 4-agent LLM chain work
"""
import os
import sys
import json
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from apps.action_plans.services.rag_engine import _get_collection, _rebuild_bm25, HybridRAGEngine
from apps.rag.parquet_store import DuckDBStore

DIVIDER = "=" * 80

def test_1_chromadb_contents():
    """Check what's in ChromaDB."""
    print(f"\n{DIVIDER}")
    print("TEST 1: ChromaDB Contents Audit")
    print(DIVIDER)
    
    col = _get_collection()
    count = col.count()
    print(f"Total chunks in ChromaDB: {count}")
    
    if count == 0:
        print("❌ ChromaDB is EMPTY! No embeddings imported.")
        print("   Run: python manage.py import_kaggle_embeddings --path .")
        return False
    
    # Sample 5 chunks to see what's in there
    sample = col.peek(limit=5)
    print(f"\nSample of {len(sample['ids'])} chunks:")
    for i, (doc_id, doc, meta) in enumerate(zip(sample['ids'], sample['documents'], sample['metadatas'])):
        print(f"\n  --- Chunk {i+1} ---")
        print(f"  ID: {doc_id}")
        print(f"  Case ID: {meta.get('case_id', 'N/A')}")
        print(f"  Court: {meta.get('court', 'N/A')}")
        print(f"  Area of Law: {meta.get('area_of_law', 'N/A')}")
        print(f"  Disposal: {meta.get('disposal_nature', 'N/A')}")
        print(f"  Title: {meta.get('title', 'N/A')[:100]}")
        print(f"  Text preview: {doc[:200]}...")
    
    # Count by area_of_law
    all_data = col.get(include=["metadatas"])
    areas = {}
    courts = {}
    disposals = {}
    for meta in all_data["metadatas"]:
        area = meta.get("area_of_law", "unknown")
        areas[area] = areas.get(area, 0) + 1
        court = meta.get("court", "unknown")
        courts[court] = courts.get(court, 0) + 1
        disp = meta.get("disposal_nature", "unknown")
        disposals[disp] = disposals.get(disp, 0) + 1
    
    print(f"\n📊 Distribution by Area of Law:")
    for area, cnt in sorted(areas.items(), key=lambda x: -x[1])[:15]:
        print(f"  {area}: {cnt} chunks")
    
    print(f"\n📊 Distribution by Court:")
    for court, cnt in sorted(courts.items(), key=lambda x: -x[1])[:10]:
        print(f"  {court}: {cnt} chunks")
    
    print(f"\n📊 Distribution by Disposal Nature:")
    for disp, cnt in sorted(disposals.items(), key=lambda x: -x[1])[:10]:
        print(f"  {disp}: {cnt} chunks")
    
    return True


def test_2_retrieval_quality():
    """Test retrieval with real legal queries."""
    print(f"\n{DIVIDER}")
    print("TEST 2: RAG Retrieval Quality")
    print(DIVIDER)
    
    _rebuild_bm25()
    rag = HybridRAGEngine()
    
    # Test queries representing real legal scenarios
    test_queries = [
        {
            "name": "Constitutional - Article 14 Equality",
            "query": "The petitioner challenges the government order as violating Article 14 of the Constitution, arguing arbitrary classification without reasonable nexus to the objective sought.",
            "area_of_law": None,
        },
        {
            "name": "Service Law - Wrongful Termination",
            "query": "The appellant a government employee was dismissed from service without following the principles of natural justice and without a proper departmental inquiry under Article 311 of the Constitution.",
            "area_of_law": None,
        },
        {
            "name": "Criminal - Bail Application",
            "query": "The accused seeks bail in a case registered under Section 302 IPC for murder. The prosecution alleges premeditated killing with a firearm.",
            "area_of_law": None,
        },
        {
            "name": "Tax / Revenue",
            "query": "The assessee challenges the reassessment order under Section 148 of the Income Tax Act on the ground that the Assessing Officer had no reason to believe that income had escaped assessment.",
            "area_of_law": None,
        },
    ]
    
    for tq in test_queries:
        print(f"\n{'─' * 60}")
        print(f"🔍 Query: {tq['name']}")
        print(f"   Text: {tq['query'][:100]}...")
        
        filters = {"area_of_law": tq["area_of_law"]} if tq["area_of_law"] else None
        
        try:
            results = rag.retrieve(tq["query"], top_k=5, filters=filters)
            print(f"   Retrieved: {len(results)} chunks")
            
            if not results:
                print("   ⚠️  No results found!")
                continue
                
            for j, r in enumerate(results):
                meta = r.get("metadata", {})
                print(f"\n   Result {j+1}:")
                print(f"     Case ID: {meta.get('case_id', 'N/A')}")
                print(f"     Title: {meta.get('title', 'N/A')[:80]}")
                print(f"     Area: {meta.get('area_of_law', 'N/A')}")
                print(f"     Disposal: {meta.get('disposal_nature', 'N/A')}")
                print(f"     Score: {r.get('score', 'N/A')}")
                print(f"     Text: {r.get('text', '')[:150]}...")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()


def test_3_duckdb_stats():
    """Test DuckDB analytical queries."""
    print(f"\n{DIVIDER}")
    print("TEST 3: DuckDB Win Rate Analytics")
    print(DIVIDER)
    
    store = DuckDBStore()
    
    # Test areas of law
    test_areas = ["constitutional", "criminal", "civil", "tax", "service", "land"]
    for area in test_areas:
        stats = store.compute_win_rates(area)
        if "error" in stats and stats["error"] == "No data available":
            print(f"  {area}: No parquet data available")
            continue
        total = stats.get("total_cases_analyzed", 0)
        if total > 0:
            print(f"  {area}: {total} cases | Allowed: {stats.get('allowed_rate', 0)*100:.0f}% | Dismissed: {stats.get('dismissed_rate', 0)*100:.0f}%")
        else:
            print(f"  {area}: 0 cases found")


def test_4_full_pipeline():
    """Test the complete 4-agent recommendation pipeline."""
    print(f"\n{DIVIDER}")
    print("TEST 4: Full 4-Agent Recommendation Pipeline")
    print(DIVIDER)
    
    from apps.action_plans.services.recommendation_pipeline import generate_recommendation
    
    # Real SC case scenario: Government employee dismissed, appeals to SC
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
    """
    
    print(f"\nTest Case: IAS Officer Compulsory Retirement Appeal to SC")
    print(f"Case text length: {len(case_text)} chars")
    print(f"\nCalling 4-Agent Pipeline (this calls Llama 70B via NVIDIA API)...")
    print(f"This may take 30-60 seconds...\n")
    
    try:
        result = generate_recommendation(
            case_id="TEST-SC-APPEAL-001",
            case_text=case_text,
            area_of_law="service",
            court="Supreme Court of India"
        )
        
        print(f"✅ Pipeline completed successfully!")
        print(f"\n📋 RESULT JSON:")
        print(json.dumps(result, indent=2, default=str))
        
        # Analyze the quality
        print(f"\n{'─' * 60}")
        print(f"📊 Quality Analysis:")
        print(f"  Recommendation ID: {result.get('recommendation_id', 'N/A')}")
        print(f"  Status: {result.get('status', 'N/A')}")
        
        verdict = result.get("verdict", {})
        print(f"  Decision: {verdict.get('decision', 'N/A')}")
        print(f"  Appeal To: {verdict.get('appeal_to', 'N/A')}")
        print(f"  Confidence: {verdict.get('confidence', 'N/A')}")
        print(f"  Urgency: {verdict.get('urgency', 'N/A')}")
        
        stats = result.get("statistical_basis", {})
        print(f"  Cases Analyzed: {stats.get('similar_cases_analyzed', 0)}")
        print(f"  Win Rate: {stats.get('government_appeal_win_rate', 0)}")
        
        print(f"\n  Primary Reasoning: {result.get('primary_reasoning', 'N/A')[:300]}")
        
        grounds = result.get("appeal_grounds", [])
        if grounds:
            print(f"\n  Appeal Grounds ({len(grounds)}):")
            for g in grounds[:3]:
                print(f"    • {g[:100]}")
        
        return result
        
    except Exception as e:
        print(f"❌ Pipeline FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print(f"\n{'#' * 80}")
    print("  NyayaDrishti RAG Pipeline — End-to-End Test Suite")
    print(f"{'#' * 80}")
    
    # Test 1: ChromaDB contents
    has_data = test_1_chromadb_contents()
    
    if not has_data:
        print("\n⛔ Cannot proceed without data. Import embeddings first!")
        sys.exit(1)
    
    # Test 2: Retrieval quality
    test_2_retrieval_quality()
    
    # Test 3: DuckDB analytics
    test_3_duckdb_stats()
    
    # Test 4: Full pipeline (requires NVIDIA API key)
    print(f"\n{'─' * 60}")
    print("About to run Test 4 (Full 4-Agent Pipeline).")
    print("This requires a valid NVIDIA API key and takes 30-60 seconds.")
    run_full = input("Run Test 4? [y/N]: ").strip().lower()
    if run_full == 'y':
        test_4_full_pipeline()
    else:
        print("Skipped Test 4.")
    
    print(f"\n{'#' * 80}")
    print("  Test Suite Complete")
    print(f"{'#' * 80}\n")
