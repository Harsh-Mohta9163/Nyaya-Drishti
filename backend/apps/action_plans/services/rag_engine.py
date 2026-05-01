"""
Hybrid RAG Engine: BM25 + NVIDIA Dense Embeddings + NVIDIA Cross-Encoder Reranker.

Pipeline:
  Query → BM25 sparse (top-50) + Dense vector (top-50)
       → Reciprocal Rank Fusion
       → NVIDIA nv-rerankqa cross-encoder (top-5)
       → Final results with scores
"""
import logging
import os

import chromadb
import requests
from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)

# Lazy globals (initialized on first use)
_chroma_client = None
_collection = None
_bm25_index = None
_bm25_corpus = []
_bm25_doc_ids = []


def _get_collection():
    """Get or create the ChromaDB collection."""
    global _chroma_client, _collection
    if _collection is None:
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "data", "chroma_db",
        )
        os.makedirs(db_path, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=db_path)
        _collection = _chroma_client.get_or_create_collection(
            name="karnataka_hc_judgments",
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def _nvidia_embed(texts: list[str]) -> list[list[float]]:
    """Get embeddings from NVIDIA NIM API."""
    from django.conf import settings

    api_key = getattr(settings, "NVIDIA_API_KEY", "") or os.getenv("NVIDIA_API_KEY", "")
    if not api_key:
        logger.warning("No NVIDIA API key for embeddings — using empty vectors")
        return [[0.0] * 1024] * len(texts)

    try:
        from openai import OpenAI

        client = OpenAI(
            base_url=getattr(settings, "NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"),
            api_key=api_key,
        )
        # Process in batches of 10 to avoid token limits
        all_embeddings = []
        for i in range(0, len(texts), 10):
            batch = texts[i : i + 10]
            # Truncate each text to ~500 tokens (~2000 chars)
            batch = [t[:2000] for t in batch]
            resp = client.embeddings.create(
                model="nvidia/nv-embedqa-e5-v5",
                input=batch,
                encoding_format="float",
                extra_body={"input_type": "passage", "truncate": "END"},
            )
            all_embeddings.extend([d.embedding for d in resp.data])
        return all_embeddings
    except Exception as e:
        logger.error("NVIDIA embedding failed: %s", e)
        return [[0.0] * 1024] * len(texts)


def _nvidia_rerank(query: str, documents: list[str], top_n: int = 5) -> list[dict]:
    """Rerank documents using NVIDIA cross-encoder."""
    from django.conf import settings

    api_key = getattr(settings, "NVIDIA_API_KEY", "") or os.getenv("NVIDIA_API_KEY", "")
    if not api_key or not documents:
        return [{"index": i, "text": d, "score": 0.0} for i, d in enumerate(documents[:top_n])]

    try:
        resp = requests.post(
            "https://integrate.api.nvidia.com/v1/retrieval/nvidia/nv-rerankqa-mistral-4b-v3/reranking",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "nvidia/nv-rerankqa-mistral-4b-v3",
                "query": {"text": query[:1000]},
                "passages": [{"text": d[:1500]} for d in documents],
            },
            timeout=30,
        )
        resp.raise_for_status()
        rankings = resp.json().get("rankings", [])
        results = []
        for r in rankings[:top_n]:
            idx = r["index"]
            results.append({
                "index": idx,
                "text": documents[idx],
                "score": r.get("logit", 0.0),
            })
        return results
    except Exception as e:
        logger.error("NVIDIA reranking failed: %s", e)
        return [{"index": i, "text": d, "score": 0.0} for i, d in enumerate(documents[:top_n])]


class HybridRAGEngine:
    """
    Hybrid RAG with BM25 sparse + dense vector + cross-encoder reranking.
    """

    def __init__(self):
        self.documents = []  # List of {"text": ..., "metadata": ...}

    def add_documents(self, documents: list[dict]):
        """
        Add documents to both BM25 and vector indices.

        Each document: {"text": "...", "metadata": {"case_number": "...", ...}}
        """
        global _bm25_index, _bm25_corpus, _bm25_doc_ids

        if not documents:
            return

        collection = _get_collection()

        # Prepare data
        new_texts = [d.get("text", "") for d in documents]
        new_ids = [f"doc_{collection.count() + i}" for i in range(len(documents))]
        new_metas = [d.get("metadata", {}) for d in documents]

        # 1. Add to vector store
        try:
            embeddings = _nvidia_embed(new_texts)
            collection.add(
                ids=new_ids,
                embeddings=embeddings,
                documents=new_texts,
                metadatas=new_metas,
            )
            logger.info("Added %d documents to vector store", len(new_texts))
        except Exception as e:
            logger.error("Failed to add to vector store: %s", e)

        # 2. Rebuild BM25 index
        self.documents.extend(documents)
        _bm25_corpus = [d.get("text", "") for d in self.documents]
        _bm25_doc_ids = list(range(len(self.documents)))
        tokenized = [text.lower().split() for text in _bm25_corpus]
        if tokenized:
            _bm25_index = BM25Okapi(tokenized)

    def query(self, query_text: str, top_k: int = 5) -> list[dict]:
        """
        Hybrid search: BM25 + dense vector + reranking.

        Returns list of {"text": ..., "score": ..., "metadata": ...}
        """
        if not query_text or not query_text.strip():
            return []

        collection = _get_collection()
        has_vectors = collection.count() > 0

        # --- Step 1: BM25 sparse search ---
        bm25_candidates = {}
        if _bm25_index is not None and _bm25_corpus:
            scores = _bm25_index.get_scores(query_text.lower().split())
            top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:50]
            for rank, idx in enumerate(top_indices):
                if scores[idx] > 0:
                    bm25_candidates[idx] = scores[idx]

        # --- Step 2: Dense vector search ---
        dense_candidates = {}
        if has_vectors:
            try:
                query_emb = _nvidia_embed([query_text])[0]
                n_results = min(50, collection.count())
                results = collection.query(
                    query_embeddings=[query_emb],
                    n_results=n_results,
                    include=["documents", "metadatas", "distances"],
                )
                if results and results["documents"] and results["documents"][0]:
                    for i, doc in enumerate(results["documents"][0]):
                        # Find matching doc in our corpus
                        for j, corpus_doc in enumerate(_bm25_corpus):
                            if corpus_doc == doc:
                                dense_candidates[j] = 1.0 - (results["distances"][0][i] if results["distances"] else 0)
                                break
            except Exception as e:
                logger.error("Dense search failed: %s", e)

        # --- Step 3: Reciprocal Rank Fusion ---
        if not bm25_candidates and not dense_candidates:
            # No index built yet — return simple keyword match
            return self._simple_search(query_text, top_k)

        rrf_scores = {}
        k = 60  # RRF constant

        bm25_ranked = sorted(bm25_candidates.keys(), key=lambda i: bm25_candidates[i], reverse=True)
        for rank, doc_id in enumerate(bm25_ranked):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1 / (k + rank + 1)

        dense_ranked = sorted(dense_candidates.keys(), key=lambda i: dense_candidates[i], reverse=True)
        for rank, doc_id in enumerate(dense_ranked):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1 / (k + rank + 1)

        merged = sorted(rrf_scores.keys(), key=lambda i: rrf_scores[i], reverse=True)[:20]

        if not merged:
            return self._simple_search(query_text, top_k)

        # --- Step 4: NVIDIA Cross-Encoder Reranking ---
        candidate_texts = [_bm25_corpus[i] for i in merged if i < len(_bm25_corpus)]
        reranked = _nvidia_rerank(query_text, candidate_texts, top_n=top_k)

        results = []
        for r in reranked:
            idx = merged[r["index"]] if r["index"] < len(merged) else 0
            meta = self.documents[idx].get("metadata", {}) if idx < len(self.documents) else {}
            results.append({
                "text": r["text"][:500],  # Truncate for response
                "score": round(r["score"], 4),
                "metadata": meta,
            })

        return results

    def _simple_search(self, query_text: str, top_k: int) -> list[dict]:
        """Simple keyword overlap search as ultimate fallback."""
        from collections import Counter

        query_tokens = Counter(query_text.lower().split())
        scored = []
        for doc in self.documents:
            text = doc.get("text", "")
            doc_tokens = Counter(text.lower().split())
            overlap = sum((query_tokens & doc_tokens).values())
            scored.append({
                "text": text[:500],
                "score": overlap,
                "metadata": doc.get("metadata", {}),
            })
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]
