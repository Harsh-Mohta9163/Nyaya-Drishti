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
_embedder = None
_bm25_index = None
_bm25_corpus = []
_bm25_doc_ids = []


def _get_embedder():
    """Lazy-load the InLegalBERT embedding function for manual query embedding."""
    global _embedder
    if _embedder is None:
        _embedder = InLegalBERTEmbeddingFunction()
    return _embedder


def _get_collection():
    """Get or create the ChromaDB collection.
    Opens WITHOUT an embedding function to be compatible with Kaggle-created
    collections that store pre-computed embeddings. Query embedding is done
    manually via _get_embedder() before calling collection.query().
    No API key needed — runs 100% locally."""
    global _chroma_client, _collection
    if _collection is None:
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "data", "chroma_db",
        )
        os.makedirs(db_path, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=db_path)
        
        # Open WITHOUT embedding_function to avoid conflict with Kaggle-imported data.
        # Pre-computed embeddings are already stored; we embed queries manually.
        _collection = _chroma_client.get_or_create_collection(
            name="karnataka_hc_judgments",
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"ChromaDB collection loaded: {_collection.count()} chunks")
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
        
    _collection = _chroma_client.get_or_create_collection(
        name="karnataka_hc_judgments",
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
        Fast retrieval: Dense vector search (ChromaDB) → Cross-Encoder reranking.
        Skips BM25 to avoid loading 400k+ documents into memory.
        """
        # Embed query manually with InLegalBERT
        embedder = _get_embedder()
        query_embedding = embedder([query])[0]
        
        # Build query kwargs
        n_candidates = min(100, max(top_k * 5, 50))  # Fetch more candidates for reranking
        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": n_candidates,
            "include": ["documents", "metadatas", "distances"],
        }
        
        # Apply metadata filters if any
        if filters:
            safe_filters = {}
            # DuckDB pre-filtering for area_of_law (optional optimization)
            if "area_of_law" in filters:
                try:
                    store = DuckDBStore()
                    df = store.filter_cases(area_of_law=filters["area_of_law"], limit=5000)
                    if not df.empty:
                        candidate_cnrs = df['cnr'].dropna().astype(str).tolist()
                        if candidate_cnrs:
                            safe_filters["case_id"] = {"$in": candidate_cnrs[:100]}
                except Exception as e:
                    logger.warning(f"DuckDB pre-filter failed: {e}")
            
            # Pass through other filters
            for k, v in filters.items():
                if k != "area_of_law":
                    safe_filters[k] = v
            
            if safe_filters:
                kwargs["where"] = safe_filters

        # Dense retrieval via ChromaDB
        try:
            dense_res = self.collection.query(**kwargs)
        except Exception as e:
            logger.error(f"ChromaDB query failed: {e}")
            return []
        
        if not dense_res["ids"] or not dense_res["ids"][0]:
            return []
        
        # Build result list from dense retrieval
        results = []
        for i, (doc_id, doc, meta, dist) in enumerate(zip(
            dense_res["ids"][0],
            dense_res["documents"][0],
            dense_res["metadatas"][0],
            dense_res["distances"][0],
        )):
            results.append({
                "id": doc_id,
                "text": doc,
                "metadata": meta,
                "score": 1.0 - dist,  # Convert cosine distance to similarity
            })
        
        # Cross-encoder reranking (optional, on small candidate set only)
        # NOTE: We use the cross-encoder ONLY for reranking order, NOT for
        # replacing the cosine similarity score. ms-marco is trained on web
        # search and assigns negative scores to most legal text, which would
        # cause the pipeline's score threshold to drop valid results.
        if _cross_encoder is not None and len(results) > 0:
            try:
                pairs = [[query[:512], r["text"][:512]] for r in results]  # Truncate for speed
                cross_scores = _cross_encoder.predict(pairs)
                # Attach cross-encoder score for reranking, but keep cosine similarity
                for idx, ce_score in enumerate(cross_scores):
                    results[idx]["ce_score"] = float(ce_score)
                # Sort by cross-encoder score (better semantic reranking)
                results.sort(key=lambda r: r.get("ce_score", 0), reverse=True)
                logger.info(f"Cross-encoder reranked {len(results)} results (scores kept as cosine similarity)")
            except Exception as e:
                logger.warning(f"Cross-encoder reranking failed, using raw scores: {e}")
        
        return results[:top_k]

    def retrieve_for_case(self, case_context: dict, domain_key: str, top_k: int = 15, filters: dict = None) -> list[dict]:
        from apps.action_plans.services.domain_prompts import DOMAIN_RAG_KEYWORDS
        
        domain_keywords = DOMAIN_RAG_KEYWORDS.get(domain_key, DOMAIN_RAG_KEYWORDS["GENERAL"])
        
        ratio = case_context.get("ratio_decidendi", "")
        operative = case_context.get("operative_order_text", "")
        case_text = case_context.get("case_text", "")
        
        q1_text = ratio[:350] if ratio else (operative[:350] if operative else case_text[:350])
        query1 = f"{domain_keywords} {q1_text}"
        
        primary_statute = case_context.get("primary_statute", " ".join(case_context.get("issues", [])[:1]))
        area = case_context.get("area_of_law", "")
        disposition = case_context.get("disposition", "")
        query2 = f"{primary_statute} {area} {disposition} government"
        
        issues = case_context.get("issues", [])
        query3 = ""
        if issues:
            query3 = f"{issues[0][:300]} {issues[1][:150] if len(issues)>1 else ''}"
        else:
            query3 = case_text[:450]
            
        queries = [query1, query2, query3]
        all_results = []
        
        for q in queries:
            if not q.strip(): continue
            res = self.retrieve(q, top_k=top_k, filters=filters)
            all_results.extend(res)
            
        return all_results
