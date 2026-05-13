# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**NyayaDrishti** is a legal intelligence platform that converts Indian court judgment PDFs into verified, actionable plans for government departments. Pipeline: PDF upload → layout-aware extraction → 4-agent structured LLM extraction → hybrid RAG-backed APPEAL/COMPLY recommendation → mandatory human verification → dashboard.

Two-tier codebase:
- `backend/` — Django 5 + DRF, SQLite (dev) / Postgres (prod), JWT auth.
- `frontend/` — React 19 + TypeScript + Vite 6 + Tailwind 4.

## Common Commands

### Backend (run from `backend/`)

```bash
# Setup (one-time)
python -m venv .venv
.venv\Scripts\activate              # Windows (PowerShell)
pip install -r requirements.txt
pip install -r requirements-ml.txt  # InLegalBERT / torch / transformers — heavy

# Database
python manage.py migrate
python manage.py createsuperuser
python seed_data.py                 # optional sample data

# Dev server
python manage.py runserver          # http://127.0.0.1:8000

# Custom management commands
python manage.py import_kaggle_embeddings --path /path/to/parquet/
python manage.py build_vectors
python manage.py rebuild_chromadb
python manage.py download_parquet
python manage.py classify_parquet
python manage.py export_for_merge
python manage.py import_merged_data
python manage.py reconcile_citations

# Ad-hoc test scripts (not pytest — run directly with Python)
python test_extraction.py
python test_rag.py
python test_recommendation.py
python test_e2e.py
# (similar pattern for test_pipeline.py, test_rules.py, test_seg.py, etc.)

# Production entrypoint
./start.sh                          # downloads HF dataset, migrates, starts gunicorn
```

### Frontend (run from `frontend/`)

```bash
npm install
npm run dev                         # http://localhost:3000 — proxies /media to backend:8000
npm run build
npm run lint                        # tsc --noEmit — there is no eslint
```

### Required external data

The RAG store is NOT in git. Without it, the pipeline runs but Similar Cases returns empty.

```
backend/data/chroma_db/             # ChromaDB persistent store
backend/data/parquet/sc_embeddings.parquet
```

Download from HuggingFace dataset `Harsh2005/nyaya-drishti-data` (see `README.md` §1 for `huggingface-cli` commands, or `start.sh` for the deployment-side download script driven by `HF_DATASET_ID`).

### Required env vars (`backend/.env`)

`DJANGO_SECRET_KEY`, `GROQ_API_KEY` (Agents 1 & 4 — fast), `NVIDIA_API_KEY` (Agents 2 & 3 — 70B reasoning), `GEMINI_API_KEY` (optional, used as final-agent fallback in 4-agent recommendation mode). `LLM_PROVIDER` defaults to `nvidia`. `DATABASE_URL` switches to Postgres if set.

## Architecture

### Request flow (end-to-end)

```
POST /api/cases/extract/  (PDF)
   └─► apps/cases/services/
         pdf_processor.py        — PyMuPDF4LLM → Markdown
         section_segmenter.py    — bi-directional regex → {header, body, operative}
         extractor.py            — 4-agent extraction (Groq 8B + NVIDIA 70B)
                                   • Agent 1 RegistryExtraction   → header
                                   • Agent 2 AnalystExtraction    → body
                                   • Agent 3 ScholarExtraction    → body
                                   • Agent 4 ComplianceExtraction → operative
   └─► persists Case + Judgment + Citation rows; spatial-search annotates each
       directive with PDF bbox for source highlighting

POST /api/action-plans/recommend/   (or /api/action-plans/<uuid>/recommend/)
   └─► apps/action_plans/services/
         rag_engine.py             — HybridRAGEngine: BM25 + InLegalBERT dense
                                     → Reciprocal Rank Fusion → Cross-Encoder rerank
                                     (corpus: ChromaDB + DuckDB over parquet, ~431K chunks)
         rules_engine.py           — Limitation Act §4/§12 + court calendar
         risk_classifier.py        — deterministic keyword contempt classifier
         recommendation_pipeline.py — Single-Agent (default) OR 4-Agent
                                      (Researcher → Devil's Advocate → Risk Auditor →
                                      Synthesizer, Gemini 2.5 Pro final w/ Llama fallback)
         appeal_strategist.py      — appeal strategy generation
   └─► ActionPlan row; full JSON cached in full_rag_recommendation

Human verification (Verify Actions tab)
   └─► POST /api/cases/action-plans/<id>/review/  → ActionPlan.verification_status
       Only approved rows reach the Dashboard aggregator (apps/dashboard/).
```

### Apps and what they own

| App | Domain |
|---|---|
| `apps/accounts/` | Custom `User` (`AUTH_USER_MODEL = "accounts.User"`) with roles: Reviewer, Dept Officer, Dept Head, Legal Advisor. JWT via SimpleJWT. |
| `apps/cases/` | `Case`, `Judgment`, `Citation`. Owns PDF processing + extraction services. `Case.appealed_from_case` is self-referential — the appeal lineage graph. `matter_id` groups trial+HC+SC stages. |
| `apps/action_plans/` | `ActionPlan`, `LimitationRule`, `CourtCalendar`. Owns RAG engine, rules engine, recommendation + appeal strategist services. |
| `apps/rag/` | Shared embedding & retrieval infra: `embedder.py` (InLegalBERT 768-dim ChromaDB EF), `parquet_store.py` (DuckDB analytics), `classifier.py` (zero-shot legal domain). Not a model app — provides services to `cases` and `action_plans`. |
| `apps/reviews/` | `ReviewLog` — L1/L2 human review chain with audit trail. |
| `apps/dashboard/` | Aggregation endpoints (live stats, deadline heatmap, risk board). Reads only `verification_status=approved` records. |
| `apps/notifications/`, `apps/translation/` | Alert and multi-language support. |

URL mounts (see `backend/config/urls.py`): `/api/auth/`, `/api/cases/`, `/api/action-plans/`, `/api/reviews/`, `/api/translate/`, `/api/notifications/`, `/api/dashboard/`, plus `/media/` for PDFs.

### LLM provider abstraction (important when editing)

`extractor.py` and `recommendation_pipeline.py` both implement provider-specific call functions with retry/backoff:
- `_call_agent_8b` → Groq `llama-3.1-8b-instant` (fast, Agents 1 & 4)
- `_call_agent_70b` → NVIDIA NIM `meta/llama-3.3-70b-instruct` (reasoning, Agents 2 & 3)
- Final synthesis in 4-agent recommendation mode → Gemini 2.5 Pro with Llama 70B fallback

Every call enforces a Pydantic schema via `response_format={"type": "json_object"}` and a schema-in-prompt fence. Rate limits (HTTP 429/503) are retried with linear backoff — preserve that behavior when adding providers.

### Frontend structure (`frontend/src/`)

Top-level `App.tsx` owns routing + auth state. Major screens: `Dashboard`, `CaseList`, `CaseOverview`, `VerifyActions` (side-by-side PDF viewer using `react-pdf` + bbox highlights from extractor), `Precedents`. JWT is attached by `api/client.ts`; `vite.config.ts` proxies `/media` → `127.0.0.1:8000` in dev. Gemini key is exposed as `process.env.GEMINI_API_KEY` via `vite.config.ts` `define` (used by frontend Gemini features only).

## Conventions worth knowing

- **No pytest harness.** Backend `test_*.py` files at repo top of `backend/` are standalone scripts that hit the dev server or services directly. Run them with `python test_<name>.py`, not `pytest`.
- **UUID primary keys** on `Case` and `Judgment` — API routes use `<uuid:pk>`. `ActionPlan` URLs in `apps/action_plans/urls.py` use `<uuid:pk>`, but the review endpoint under `apps/cases/urls.py` uses `<int:pk>` — these are two different lookups; don't conflate.
- **Self-hosted-friendly invariant.** Every ML component (embeddings, reranker, BM25, analytics) runs locally. Cloud LLM keys are the only external dependency, and they're swappable with `vLLM` / `Ollama` via the OpenAI-compatible base-URL pattern. Don't introduce hard dependencies on a specific commercial API.
- **Caching.** Full recommendation JSON lives in `ActionPlan.full_rag_recommendation`. Revisits should read the cache instead of re-running the pipeline — check before adding new LLM calls.
- **`TIME_ZONE = "Asia/Kolkata"`** with `USE_TZ = True`. The rules engine relies on this for Limitation Act / court holiday math — don't change the project timezone casually.
