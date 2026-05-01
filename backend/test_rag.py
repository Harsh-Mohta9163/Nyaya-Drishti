import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.action_plans.services.rag_engine import HybridRAGEngine
rag = HybridRAGEngine()

# Load the previously seeded documents into memory for the BM25 index
from seed_data import SAMPLE_JUDGMENTS
rag.add_documents(SAMPLE_JUDGMENTS)

queries = [
    'land acquisition compensation 30 days',
    'environmental clearance western ghats',
    'contempt proceedings chief secretary affidavit'
]

print('\n' + '='*60)
print('HYBRID RAG RETRIEVAL TEST')
print('='*60)

for query in queries:
    print(f'\nQUERY: "{query}"')
    results = rag.query(query, top_k=2)
    for i, res in enumerate(results):
        score = res.get('score', 0)
        meta = res.get('metadata', {})
        text = res.get('text', '').replace('\n', ' ')
        print(f'   [{i+1}] Score: {score:.4f} | Case: {meta.get("case_number")} ({meta.get("type")})')
        print(f'       Text: {text[:150]}...')
