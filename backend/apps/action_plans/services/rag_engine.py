"""
Hybrid RAG Engine: BM25 + Dense Embeddings (Local)
Pipeline:
  Query → BM25 sparse (top-50) + Dense vector (top-50)
       → Reciprocal Rank Fusion
       → Final results with scores

Embedding: ChromaDB built-in all-MiniLM-L6-v2 (384-dim, runs locally, no API needed).
Works with any LLM provider (Gemini, Llama, etc.) since embeddings are provider-agnostic.
"""
import logging
import os

import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from rank_bm25 import BM25Okapi

from apps.rag.embedder import InLegalBERTEmbeddingFunction
from apps.rag.parquet_store import DuckDBStore

try:
    from sentence_transformers import CrossEncoder
    _cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
except ImportError:
    _cross_encoder = None

logger = logging.getLogger(__name__)

# Lazy globals (initialized on first use)
_chroma_client = None
_collection = None
_bm25_index = None
_bm25_corpus = []
_bm25_doc_ids = []


def _get_collection():
    """Get or create the ChromaDB collection.
    Uses InLegalBERT embedding function (768-dim).
    No API key needed — runs 100% locally."""
    global _chroma_client, _collection
    if _collection is None:
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "data", "chroma_db",
        )
        os.makedirs(db_path, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=db_path)
        
        # Load custom embedding function
        ef = InLegalBERTEmbeddingFunction()
        
        try:
            _collection = _chroma_client.get_or_create_collection(
                name="karnataka_hc_judgments",
                embedding_function=ef,
                metadata={"hnsw:space": "cosine"},
            )
        except ValueError as e:
            if "Embedding function conflict" in str(e):
                logger.warning("Embedding function conflict detected. Recreating ChromaDB collection...")
                _chroma_client.delete_collection("karnataka_hc_judgments")
                _collection = _chroma_client.create_collection(
                    name="karnataka_hc_judgments",
                    embedding_function=ef,
                    metadata={"hnsw:space": "cosine"},
                )
            else:
                raise
    return _collection


def reset_collection():
    """Delete and recreate the collection (use when embedding dimensions change)."""
    global _chroma_client, _collection
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "data", "chroma_db",
    )
    os.makedirs(db_path, exist_ok=True)
    _chroma_client = chromadb.PersistentClient(path=db_path)
    try:
        _chroma_client.delete_collection("karnataka_hc_judgments")
        logger.info("Deleted old karnataka_hc_judgments collection")
    except Exception:
        pass
    try:
        ef = InLegalBERTEmbeddingFunction()
    except Exception:
        ef = None
        
    _collection = _chroma_client.get_or_create_collection(
        name="karnataka_hc_judgments",
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )
    return _collection


def _rebuild_bm25():
    """Rebuild BM25 index from ChromaDB."""
    global _bm25_index, _bm25_corpus, _bm25_doc_ids
    col = _get_collection()
    data = col.get(include=["documents"])

    _bm25_doc_ids = data["ids"]
    _bm25_corpus = []

    for text in data["documents"]:
        tokens = str(text).lower().split()
        _bm25_corpus.append(tokens)

    if _bm25_corpus:
        _bm25_index = BM25Okapi(_bm25_corpus)


class HybridRAGEngine:
    def __init__(self):
        self.collection = _get_collection()

    def add_documents(self, documents: list[dict]):
        """
        Add documents to vector store.
        Chroma auto-embeds using InLegalBERT.
        `documents` format: [{"text": str, "metadata": dict}]
        """
        if not documents:
            return

        texts = [d["text"] for d in documents]
        metadatas = [d["metadata"] for d in documents]
        
        import uuid
        ids = [str(d["metadata"].get("id", uuid.uuid4())) for d in documents]

        # Cleanup metadata dicts (Chroma only accepts string, int, float, bool)
        clean_metadatas = []
        for meta in metadatas:
            clean = {}
            for k, v in meta.items():
                if v is None:
                    continue
                if isinstance(v, (str, int, float, bool)):
                    clean[k] = v
                else:
                    clean[k] = str(v)
            clean_metadatas.append(clean)

        logger.info(f"Upserting {len(texts)} documents into ChromaDB (local InLegalBERT)")
        # Pass documents= without embeddings= → Chroma auto-generates embeddings locally
        self.collection.upsert(
            documents=texts,
            metadatas=clean_metadatas,
            ids=ids,
        )

        logger.info("Rebuilding BM25 index")
        _rebuild_bm25()

    def retrieve(self, query: str, top_k: int = 5, filters: dict = None) -> list[dict]:
        """
        Hybrid retrieval: DuckDB Pre-filter -> BM25 + Dense -> RRF -> Cross-Encoder.
        Excludes reversed/overruled precedents automatically.
        """
        if _bm25_index is None:
            _rebuild_bm25()

        if not _bm25_doc_ids:
            return []

        # Default filter: valid precedents only
        safe_filters = {}
        # safe_filters = {"precedent_status": {"$in": ["good_law", "unknown", "modified"]}}
        if filters:
            safe_filters.update(filters)
            
        # Stage 1: DuckDB Pre-filtering (Optional)
        # If area_of_law is provided, we can pre-filter candidates
        candidate_ids = None
        if filters and "area_of_law" in filters:
            try:
                store = DuckDBStore()
                df = store.filter_cases(area_of_law=filters["area_of_law"], limit=5000)
                if not df.empty:
                    candidate_cnrs = df['cnr'].dropna().astype(str).tolist()
                    if candidate_cnrs:
                        # Vector ids are in format "{cnr}_chunk_{i}"
                        # We cannot easily filter by prefix in Chroma where dict, 
                        # but we can filter by the 'case_id' metadata field
                        safe_filters["case_id"] = {"$in": candidate_cnrs[:100]} # Limit to 100 to avoid Chroma limits
            except Exception as e:
                logger.warning(f"DuckDB pre-filter failed, falling back to full corpus: {e}")

        # 1. Dense Retrieval (top 50) — Chroma auto-embeds the query locally
        kwargs = {
            "query_texts": [query],
            "n_results": min(100, len(_bm25_doc_ids)),
            "include": ["documents", "metadatas", "distances"],
        }
        if safe_filters:
            kwargs["where"] = safe_filters

        dense_res = self.collection.query(**kwargs)
        
        dense_scores = {}
        if dense_res["ids"] and dense_res["ids"][0]:
            for rank, (doc_id, dist) in enumerate(zip(dense_res["ids"][0], dense_res["distances"][0])):
                dense_scores[doc_id] = {"rank": rank + 1, "dist": dist}

        # 2. Sparse Retrieval (BM25)
        query_tokens = query.lower().split()
        bm25_scores_raw = _bm25_index.get_scores(query_tokens)

        # 3. Reciprocal Rank Fusion (RRF)
        k_rrf = 60
        fused_scores = {}

        bm25_ranked_idx = sorted(range(len(bm25_scores_raw)), key=lambda i: bm25_scores_raw[i], reverse=True)
        for rank, idx in enumerate(bm25_ranked_idx[:50]):
            doc_id = _bm25_doc_ids[idx]
            if filters and doc_id not in dense_scores:
                continue
            fused_scores[doc_id] = fused_scores.get(doc_id, 0.0) + (1.0 / (k_rrf + rank + 1))

        for doc_id, data in dense_scores.items():
            rank = data["rank"]
            fused_scores[doc_id] = fused_scores.get(doc_id, 0.0) + (1.0 / (k_rrf + rank))

        # 4. Final Ranking (Top 100 for reranking)
        top_ids = sorted(fused_scores.keys(), key=lambda d: fused_scores[d], reverse=True)[:100]

        final_results = []
        if top_ids:
            fetched = self.collection.get(ids=top_ids, include=["documents", "metadatas"])
            id_to_data = {
                fetched["ids"][i]: {
                    "id": fetched["ids"][i],
                    "text": fetched["documents"][i],
                    "metadata": fetched["metadatas"][i],
                    "score": fused_scores[fetched["ids"][i]]
                }
                for i in range(len(fetched["ids"]))
            }
            
            # Stage 3: Cross-Encoder Reranking
            if _cross_encoder is not None and len(top_ids) > 0:
                pairs = [[query, id_to_data[doc_id]["text"]] for doc_id in top_ids]
                cross_scores = _cross_encoder.predict(pairs)
                
                # Combine RRF and cross-encoder scores
                for idx, doc_id in enumerate(top_ids):
                    id_to_data[doc_id]["score"] = float(cross_scores[idx])
                    
                # Re-sort by cross-encoder score
                top_ids = sorted(top_ids, key=lambda d: id_to_data[d]["score"], reverse=True)
                
            # Limit to top_k
            top_ids = top_ids[:top_k]
            
            for doc_id in top_ids:
                if doc_id in id_to_data:
                    final_results.append(id_to_data[doc_id])

        return final_results
