"""
RAG Pipeline Diagnostic Script
Run: python manage.py shell < test_rag_diagnosis.py
"""
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from apps.action_plans.services.rag_engine import _get_collection, _get_embedder

print("=" * 70)
print("RAG PIPELINE DIAGNOSIS")
print("=" * 70)

# 1. Check DB size
col = _get_collection()
count = col.count()
print(f"\n1. ChromaDB Collection Size: {count} chunks")
if count == 0:
    print("   EMPTY DB! No data to search. Run import_kaggle_embeddings first.")
    sys.exit(1)
elif count < 100:
    print(f"   WARNING: Only {count} chunks - very small corpus. Expected 10k+.")
else:
    print(f"   OK: {count} chunks available for search.")

# 2. Sample some metadata to verify what's in there
sample = col.peek(limit=5)
print(f"\n2. Sample metadata from DB:")
for i, meta in enumerate(sample.get('metadatas', [])):
    print(f"   [{i}] case_id={meta.get('case_id','?')}, area={meta.get('area_of_law','?')}, court={meta.get('court','?')}, disposal={meta.get('disposal_nature', '?')}")

# 3. Test query with the land acquisition case summary
test_query = """Land acquisition compensation enhanced by Division Bench. 
Consent award under Section 11 of the Land Acquisition Act. 
Deduction of 53% towards developmental charges. 
Market value determination. Karnataka High Court.
The Reference Court's error in applying the consent award to non-consenting landowners."""

print(f"\n3. Test Query (first 200 chars): {test_query[:200]}...")

# 4. Raw ChromaDB retrieval (no cross-encoder)
print("\n   Loading InLegalBERT embedder...")
embedder = _get_embedder()
query_emb = embedder([test_query])[0]
print(f"   Embedding dimension: {len(query_emb)}")

raw_results = col.query(
    query_embeddings=[query_emb],
    n_results=15,
    include=["documents", "metadatas", "distances"]
)

print(f"\n4. RAW ChromaDB Results (top 15, cosine similarity):")
print(f"   {'#':>3} | {'Cosine Sim':>10} | {'Area of Law':<25} | {'Disposal':<15} | Title")
print(f"   {'-'*3}-+-{'-'*10}-+-{'-'*25}-+-{'-'*15}-+------")
if raw_results["ids"] and raw_results["ids"][0]:
    for i, (doc_id, meta, dist) in enumerate(zip(
        raw_results["ids"][0], 
        raw_results["metadatas"][0], 
        raw_results["distances"][0]
    )):
        sim = 1.0 - dist
        title = meta.get('title', meta.get('case_id', 'Unknown'))[:50]
        area = meta.get('area_of_law', '?')[:24]
        outcome = meta.get('disposal_nature', '?')[:14]
        print(f"   {i+1:>3} | {sim:>10.4f} | {area:<25} | {outcome:<15} | {title}")
else:
    print("   NO RESULTS returned from ChromaDB!")

# 5. Now test WITH cross-encoder
try:
    from sentence_transformers import CrossEncoder
    ce = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    
    print(f"\n5. CROSS-ENCODER Reranked Scores:")
    print(f"   {'#':>3} | {'CE Score':>10} | {'Cosine':>8} | {'Status':<8} | Title")
    print(f"   {'-'*3}-+-{'-'*10}-+-{'-'*8}-+-{'-'*8}-+------")
    
    texts = raw_results["documents"][0]
    pairs = [[test_query[:512], t[:512]] for t in texts]
    ce_scores = ce.predict(pairs)
    
    for i, (score, meta) in enumerate(zip(ce_scores, raw_results["metadatas"][0])):
        title = meta.get('title', meta.get('case_id', 'Unknown'))[:50]
        orig_sim = 1.0 - raw_results["distances"][0][i]
        status = "KEPT" if score >= 0.0 else "DROPPED"
        print(f"   {i+1:>3} | {score:>10.4f} | {orig_sim:>8.4f} | {status:<8} | {title}")
    
    kept = sum(1 for s in ce_scores if s >= 0.0)
    dropped = sum(1 for s in ce_scores if s < 0.0)
    print(f"\n   Summary: {kept} KEPT, {dropped} DROPPED by score < 0.0 threshold")
    
    if dropped > 10:
        print("   >>> DIAGNOSIS: Cross-encoder is killing most results!")
        print("   >>> The ms-marco model is trained for web search, not legal text.")
        print("   >>> Fix: Use cosine similarity for scoring, cross-encoder only for reranking order.")
    
except ImportError:
    print("\n5. Cross-encoder not installed (no sentence-transformers)")
    print("   Scores are raw cosine similarity (0-1 range)")
    print("   The < 0.0 filter should NOT be dropping results in this case.")

# 6. Check what the plan_generator sees (separate path)
print(f"\n6. Plan Generator RAG Path:")
print(f"   plan_generator.py also calls RAG_ENGINE.retrieve() separately")
print(f"   with judgment.summary_of_facts as query, top_k=5")
print(f"   This is a SECOND retrieval that feeds into similar_cases on the ActionPlan model")

print("\n" + "=" * 70)
print("DIAGNOSIS COMPLETE")
print("=" * 70)
