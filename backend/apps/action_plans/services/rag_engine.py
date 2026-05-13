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
from rank_bm25 import BM25Okapi

from apps.rag.embedder import InLegalBERTEmbeddingFunction
from apps.rag.parquet_store import DuckDBStore

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
        base_data_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "data"
        )

        # Prefer the canonical store at data/chroma_db/ (per README + HF dataset layout),
        # then fall back to data/chroma_db_export/ (start.sh unzip target), then to data/
        # itself (zip extracted at the root). Pick the first candidate whose sqlite file
        # is non-empty, so a stray empty chroma.sqlite3 can't shadow the real store.
        candidates = [
            os.path.join(base_data_path, "chroma_db"),
            os.path.join(base_data_path, "chroma_db_export"),
            base_data_path,
        ]
        db_path = None
        for c in candidates:
            sqlite_path = os.path.join(c, "chroma.sqlite3")
            if os.path.exists(sqlite_path) and os.path.getsize(sqlite_path) > 1024 * 100:
                db_path = c
                logger.info(f"ChromaDB store selected: {db_path}")
                break
        if db_path is None:
            db_path = candidates[0]
            logger.warning(f"No populated ChromaDB store found; creating empty store at {db_path}")

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
    base_data_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "data",
    )
    # Match _get_collection() — prefer chroma_db/, then chroma_db_export/, then data/.
    db_path = next(
        (
            c for c in (
                os.path.join(base_data_path, "chroma_db"),
                os.path.join(base_data_path, "chroma_db_export"),
                base_data_path,
            )
            if os.path.exists(os.path.join(c, "chroma.sqlite3"))
        ),
        os.path.join(base_data_path, "chroma_db"),
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
            logger.warning(f"ChromaDB returned 0 chunks for query (first 60 chars): {query[:60]!r}")
            return []
        logger.warning(f"ChromaDB returned {len(dense_res['ids'][0])} chunks for query (first 60 chars): {query[:60]!r}")
        
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
        
        # NOTE: Cross-encoder reranking was disabled because it fought the
        # cosine similarity threshold in recommendation_pipeline.py — CE would
        # promote chunks with low cosine sim to the top, and those chunks then
        # got dropped by the cosine filter, leaving zero precedents.
        # Results are returned in raw cosine similarity order (ChromaDB default).
        return results[:top_k]

    def fetch_neighbor_chunks(self, case_id: str, center_index: int, window: int = 2) -> list[dict]:
        """Fetch chunks for a case in a window around center_index.

        Returns chunks ordered by chunk_index. Used to stitch together a
        contiguous paragraph rather than relying on a single 500-char chunk
        which is usually cut mid-sentence.
        """
        if not case_id:
            return []
        try:
            res = self.collection.get(
                where={"case_id": case_id},
                include=["documents", "metadatas"],
                limit=50,
            )
        except Exception as e:
            logger.warning(f"fetch_neighbor_chunks failed for {case_id}: {e}")
            return []

        items = []
        for cid, doc, meta in zip(res.get("ids", []), res.get("documents", []), res.get("metadatas", [])):
            try:
                idx = int(meta.get("chunk_index", -1))
            except (TypeError, ValueError):
                idx = -1
            if idx < 0:
                continue
            if abs(idx - center_index) <= window:
                items.append({"id": cid, "chunk_index": idx, "text": doc, "metadata": meta})

        items.sort(key=lambda x: x["chunk_index"])
        return items

    def stitch_precedent_text(self, case_id: str, center_index: int, max_chars: int = 1800) -> str:
        """Return a contiguous text window around `center_index` for `case_id`.

        Joins neighbor chunks with separators so the LLM sees a paragraph-level
        view of the cited precedent instead of a half-cut sentence.
        """
        neighbors = self.fetch_neighbor_chunks(case_id, center_index, window=2)
        if not neighbors:
            return ""
        joined = " ".join(n["text"] for n in neighbors)
        # Trim from both ends to clean partial-sentence artefacts.
        if len(joined) > max_chars:
            joined = joined[:max_chars] + "..."
        return joined

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
