<div align="center">

# ⚖️ NyayaDrishti — Legal Intelligence Platform

### From Court Judgments to Verified Action Plans

**Theme 11 — Centre for e-Governance, Government of Karnataka**

<!-- [Live Demo](#-deployed-url) · [Architecture](#-system-architecture) · [Setup Guide](#-getting-started) · [Evaluation](#-evaluation-criteria-mapping) -->

</div>

---

## Problem Statement

The **Court Case Monitoring System (CCMS)** — integrated with the High Court's CIS — automatically fetches judgment PDFs once a case is disposed. These judgments contain critical directives requiring timely administrative decisions: whether to comply, who is responsible, whether to appeal, and the limitation period.

**The challenge:** Judgments are lengthy, complex legal PDFs. Critical actions are buried in dense text, causing delays, missed deadlines, and non-compliance risk for government departments.

**NyayaDrishti solves this** by building an end-to-end AI pipeline that:
1. **Extracts** structured data from unstructured judgment PDFs
2. **Generates** AI-assisted action plans with appeal/comply recommendations
3. **Verifies** all outputs through a mandatory human-in-the-loop review
4. **Displays** only approved, trusted data on a decision-maker dashboard

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                      FRONTEND (React 19 + Vite)                      │
│  Dashboard │ Case List │ Case Overview │ Verify Actions │ Precedents  │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │ REST API (JWT Auth)
┌────────────────────────────────▼─────────────────────────────────────┐
│                      BACKEND (Django 5 + DRF)                        │
│                                                                      │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────────────┐ │
│  │ PDF Upload  │→ │  PyMuPDF4LLM │→ │  Bi-Directional Segmenter    │ │
│  │ & Storage   │  │  (Markdown)  │  │  (Header / Body / Operative) │ │
│  └─────────────┘  └──────────────┘  └──────────────┬───────────────┘ │
│                                                     │                │
│  ┌──────────────────────────────────────────────────▼─────────────┐  │
│  │              4-AGENT EXTRACTION PIPELINE                        │  │
│  │  Agent 1: Registry Clerk    → case metadata, parties           │  │
│  │  Agent 2: Legal Analyst     → facts, issues framed             │  │
│  │  Agent 3: Precedent Scholar → ratio decidendi, citations       │  │
│  │  Agent 4: Compliance Officer→ directives, deadlines, risk      │  │
│  └─────────────────────────────────────────────────────────────── ┘  │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │   AI RECOMMENDATION PIPELINE (Single-Agent or 4-Agent mode)     │  │
│  │                                                                  │  │
│  │   Hybrid RAG: InLegalBERT Dense + BM25 + RRF + Cross-Encoder   │  │
│  │   DuckDB Parquet Analytics  (win-rate stats, 431K+ chunks)      │  │
│  │                                                                  │  │
│  │   [Single-Agent mode — default, runs on any hardware]           │  │
│  │    → One reasoning pass: all context → APPEAL / COMPLY verdict  │  │
│  │                                                                  │  │
│  │   [4-Agent mode — available for high-compute deployments]       │  │
│  │    Agent 1: Precedent Researcher → trend analysis               │  │
│  │    Agent 2: Devil's Advocate     → pro/con arguments            │  │
│  │    Agent 3: Risk Auditor         → contempt/financial risk      │  │
│  │    Agent 4: Decision Synthesizer → final verdict                │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌────────────────┐  ┌──────────────────┐  ┌──────────────────────┐  │
│  │ Rules Engine   │  │ Contempt Risk    │  │ Court Hierarchy      │  │
│  │ (Limitation    │  │ Classifier       │  │ Logic (Appeal        │  │
│  │  Act deadlines)│  │ (Keyword-based   │  │  Forum Detection)    │  │
│  │                │  │  Deterministic)  │  │                      │  │
│  └────────────────┘  └──────────────────┘  └──────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  Data Layer : SQLite (Cases, Judgments, ActionPlans, Reviews)    │ │
│  │  Vector Store: ChromaDB  (InLegalBERT 768-dim embeddings)        │ │
│  │  Analytics  : DuckDB over Parquet (431K+ SC/HC judgment chunks)  │ │
│  └──────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

---

## End-to-End Flow

### Phase 1 — Extract (Understand the Judgment)

```
PDF Upload → PyMuPDF4LLM (layout-aware Markdown) → Bi-Directional Regex Segmenter
                                                          │
                                          ┌───────────────┼───────────────┐
                                       Header           Body          Operative
                                          │               │               │
                                    Agent 1 (fast)  Agent 2+3 (deep)  Agent 4 (fast)
                                    Registry Clerk  Analyst+Scholar    Compliance
                                          │               │               │
                                    Case metadata    Facts, Issues,   Directives,
                                    Parties, Date    Ratio, Citations  Contempt Risk
```

- **PDF Processor** (`pdf_processor.py`): Uses `PyMuPDF4LLM` for layout-aware text extraction to clean Markdown. Falls back to legacy `PyMuPDF` if needed.
- **Section Segmenter** (`section_segmenter.py`): Bi-directional regex scanning — top-down for narrative triggers (where facts begin), bottom-up for disposal triggers (where the operative order starts). 10% bidirectional overlap ensures no reasoning is lost at boundaries.
- **4-Agent Extraction** (`extractor.py`): Each agent receives only its relevant section with a Pydantic-enforced JSON schema, ensuring structured output.
- **Source Highlighting**: After extraction, `PyMuPDF` spatial search (`page.search_for()`) locates each directive's bounding box coordinates in the original PDF for visual verification.

### Phase 2 — Generate Action Plan (AI-Assisted Recommendation)

```
Extracted Judgment Data
        │
        ├─→ Hybrid RAG Engine ──→ Top-K similar precedents
        │     (BM25 + InLegalBERT + RRF + Cross-Encoder Reranking)
        │     Corpus: 431,722 chunks from 20 years of SC judgments
        │
        ├─→ DuckDB Parquet Analytics ──→ Win-rate statistics
        │     (50K+ SC + Karnataka HC Division Bench judgments)
        │
        ├─→ Rules Engine ──→ Statutory deadlines
        │     (Limitation Act §4, §12 + Court Calendar holidays)
        │
        ├─→ Court Hierarchy Logic ──→ Correct appellate forum
        │     (Single Judge → Division Bench → Supreme Court)
        │
        └─→ Recommendation Pipeline (open-source LLM)
              [Single-Agent] Default — lower compute, same reasoning quality
              [4-Agent]      Optional — Precedent Researcher → Devil's Advocate
                             → Risk Auditor → Decision Synthesizer
                    │
                    └─→ ActionPlan record saved to DB
                         (cached in full_rag_recommendation JSON field)
```

> **Pipeline modes:** The single-agent pipeline runs well on commodity hardware or cloud free tiers. The 4-agent pipeline is available for government servers with higher compute capacity. Both produce an **APPEAL / COMPLY** verdict with full reasoning.

### Phase 3 — Verify (Human-in-the-Loop — Mandatory)

The **Verify Actions** tab provides:
- Side-by-side view: extracted directives on the left, original PDF on the right
- **Source highlighting** with page numbers and bounding boxes from PyMuPDF
- **Confidence levels** (extraction_confidence field on each Judgment)
- Human reviewer can **Approve**, **Edit**, or **Reject** each action item
- Only verified records (`verification_status = approved`) move to the dashboard
- Multi-level review chain supported via `ReviewLog` model (L1/L2 approvals)

### Phase 4 — Dashboard (Trusted View)

- **Real-time stats** computed from database: total cases, pending review, high-risk count, upcoming deadlines
- **Deadline Heatmap**: 30-day calendar mapped from actual compliance/appeal deadlines
- **Risk Board**: Cases sorted by contempt risk and urgency
- **Recent Cases Table**: Live case listing with risk badges, status, and court info
- Department-wise filtering supported via the user role/department model

---

## 🔒 Data Privacy & Government Compliance (On-Premise Deployment)

A critical architectural advantage of **NyayaDrishti** is its design for strict data privacy and residency requirements for Indian digital public infrastructure.

The entire stack — Django backend, React frontend, InLegalBERT embeddings, ChromaDB vector store, and DuckDB analytics — is **fully open source**. The government can deploy NyayaDrishti entirely on their own **on-premise servers** with zero external dependencies:

* **100% Data Privacy**: Sensitive court documents, directives, and legal strategies never leave the government's internal network.
* **Air-gap compatible**: All ML models (InLegalBERT, cross-encoder) run locally. The open-source LLMs can be self-hosted via `vLLM` or `Ollama`.
* **No commercial cloud lock-in**: Zero reliance on external AI providers. Every component can be swapped for an open-source equivalent.

> The 4-agent pipeline is designed for government on-premise servers with adequate GPU/CPU resources, where rate limits and compute costs are not a constraint.

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------| 
| **Frontend** | React 19, TypeScript, Vite 6 | SPA with hot-reload |
| **Styling** | TailwindCSS 4, Framer Motion | Glassmorphism design, animations |
| **PDF Viewer** | react-pdf + pdfjs-dist | In-browser PDF rendering with source highlights |
| **Backend** | Django 5, Django REST Framework | REST API, ORM, migrations |
| **Auth** | SimpleJWT | Token-based authentication with role-based access |
| **PDF Parsing** | PyMuPDF4LLM | Layout-aware PDF → Markdown conversion |
| **LLM (Extraction)** | Open-source LLM (cloud API or self-hosted) | 4-agent structured extraction pipeline |
| **LLM (Recommendation)** | Open-source LLM (cloud API or self-hosted) | Single-agent or 4-agent RAG recommendation |
| **Embeddings** | **InLegalBERT** (`law-ai/InLegalBERT`) | 768-dim legal domain embeddings — runs fully locally |
| **Vector Store** | ChromaDB (persistent, local) | Dense vector similarity search |
| **Sparse Retrieval** | BM25Okapi (rank-bm25) | Keyword-based retrieval |
| **Reranking** | Cross-Encoder (open-source, local) | Final relevance reranking |
| **Fusion** | Reciprocal Rank Fusion (RRF) | Combines BM25 + dense scores |
| **Analytics** | DuckDB over Parquet | SQL queries over 431K+ case chunks |
| **Classifier** | Deterministic keyword matching | Contempt risk classification (High/Medium/Low) |
| **Domain Classification** | InLegalBERT zero-shot + K-Means | Legal domain classification (12 categories) |
| **Database** | SQLite (dev) / PostgreSQL (prod) | Relational data storage |

---

## Project Structure

```
Nyaya-Drishti/
├── backend/
│   ├── apps/
│   │   ├── accounts/          # Custom User model (roles: Reviewer, Dept Officer, Dept Head)
│   │   ├── cases/             # Case, Judgment, Citation models
│   │   │   └── services/
│   │   │       ├── pdf_processor.py        # PyMuPDF4LLM text extraction
│   │   │       ├── section_segmenter.py    # Bi-directional regex segmenter
│   │   │       └── extractor.py            # 4-agent LLM extraction pipeline
│   │   ├── action_plans/      # ActionPlan, LimitationRule, CourtCalendar models
│   │   │   └── services/
│   │   │       ├── recommendation_pipeline.py  # Single-agent + 4-agent RAG recommendation
│   │   │       ├── rag_engine.py               # Hybrid RAG (BM25+Dense+RRF+CrossEncoder)
│   │   │       ├── rules_engine.py             # Limitation Act deadline computation
│   │   │       ├── risk_classifier.py          # Contempt risk (BERT + keywords)
│   │   │       └── appeal_strategist.py        # Appeal strategy generation
│   │   ├── rag/               # Embedding & vector infrastructure
│   │   │   ├── embedder.py                # InLegalBERT ChromaDB embedding function
│   │   │   ├── parquet_store.py           # DuckDB analytics over parquet files
│   │   │   └── classifier.py             # Zero-shot legal domain classifier
│   │   ├── reviews/           # ReviewLog model (human verification chain)
│   │   ├── dashboard/         # Dashboard aggregation API
│   │   ├── notifications/     # Alert system
│   │   └── translation/       # Multi-language support
│   ├── config/                # Django settings, root URLs
│   ├── data/
│   │   ├── chroma_db/         # ChromaDB persistent vector store  ← download required
│   │   └── parquet/           # Pre-computed SC/HC judgment embeddings  ← download required
│   ├── media/judgments/       # Uploaded PDF files
│   ├── train_contempt_classifier.py       # InLegalBERT fine-tuning script
│   ├── kaggle_embedding_pipeline.py       # GPU embedding pipeline for 50K+ cases
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.tsx      # Live stats, heatmap, risk board (DB-driven)
│   │   │   ├── CaseList.tsx       # Case listing with search and filters
│   │   │   ├── CaseOverview.tsx   # Extracted data + AI analysis display
│   │   │   ├── CaseHeader.tsx     # Case metadata header bar
│   │   │   ├── VerifyActions.tsx  # Human-in-the-loop verification + PDF viewer
│   │   │   ├── Precedents.tsx     # Citation network and precedent analysis
│   │   │   └── Sidebar.tsx        # Collapsible navigation sidebar
│   │   ├── api/client.ts          # API client with JWT interceptor
│   │   ├── context/AuthContext.tsx # Authentication state management
│   │   ├── App.tsx                # Main app with routing and state
│   │   └── LoginPage.tsx          # Authentication UI
│   ├── vite.config.ts             # Vite config with /media proxy
│   └── package.json
│
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20+
- API keys for at least one open-source LLM provider (cloud) **or** a self-hosted LLM via `vLLM` / `Ollama`

### 1. Download Required Data Files

The RAG vector store and pre-computed embeddings are hosted on Hugging Face and **must be downloaded before running the backend**.

**Dataset:** [Harsh2005/nyaya-drishti-data](https://huggingface.co/datasets/Harsh2005/nyaya-drishti-data/tree/main)

Download the following and place them in your backend directory:

```
backend/
├── data/
│   ├── chroma_db/          ← Download the chroma_db folder from HuggingFace
│   └── parquet/
│       └── sc_embeddings.parquet   ← Download sc_embeddings.parquet from HuggingFace
```

You can download manually from the link above, or use the Hugging Face CLI:

```bash
pip install huggingface_hub

# Download the parquet embeddings
huggingface-cli download Harsh2005/nyaya-drishti-data sc_embeddings.parquet \
  --repo-type dataset --local-dir backend/data/parquet/

# Download the ChromaDB vector store
huggingface-cli download Harsh2005/nyaya-drishti-data --repo-type dataset \
  --local-dir backend/data/ --include "chroma_db/*"
```

> **Note:** Without these files the app will still run, but the Similar Cases (RAG precedents) section will return no results.

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-ml.txt  # For InLegalBERT, torch, transformers

# Configure environment
cp .env.example .env
# Edit .env and fill in:
#   DJANGO_SECRET_KEY=<generate-a-secret>
#   GROQ_API_KEY=<your-groq-key>          # or any open-source LLM API
#   NVIDIA_API_KEY=<your-nvidia-nim-key>  # optional, for 4-agent mode

# Run migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# (Optional) Seed sample data
python seed_data.py

# Start backend server
python manage.py runserver
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
# → http://localhost:3000
```

### 4. (Optional) Rebuild RAG Corpus from Scratch

If you want to re-generate the embeddings rather than downloading the pre-built files:

```bash
# Run on Kaggle with GPU (T4/P100):
# Upload kaggle_embedding_pipeline.py → generates sc_embeddings.parquet

# Then import locally:
python manage.py import_kaggle_embeddings --path /path/to/downloaded/
```

## Deployed URL

> **Live Demo:** [Nyaya Drishti Portal](https://nyaya-drishti.onrender.com/)
>

---

## Evaluation Criteria Mapping

### 1. Accuracy of Extraction

| Technique | How We Achieve It |
|-----------|-------------------|
| **Layout-aware PDF parsing** | `PyMuPDF4LLM` converts PDFs to clean Markdown preserving structure, tables, and formatting — far superior to raw text extraction |
| **Bi-directional regex segmenter** | Intelligently splits judgments into Header/Body/Operative sections using 37+ legal trigger patterns specific to Indian HC judgments |
| **4 specialized LLM agents** | Each agent receives only its relevant section with a strict Pydantic schema, reducing hallucination and improving field-level accuracy |
| **Open-source LLM strategy** | Fast models for structured metadata extraction; larger models for complex legal reasoning — fully swappable with self-hosted alternatives |
| **Source location annotation** | PyMuPDF spatial search maps each extracted directive back to its exact page/coordinates in the PDF for verification |
| **Confidence scoring** | Each extraction carries an `extraction_confidence` score; the classifier reports confidence levels for risk assessment |
| **Fallback chains** | Every LLM call has retry logic with automatic fallback ensuring extraction never fails silently |

### 2. Quality of Action Plan Generation

| Technique | How We Achieve It |
|-----------|-------------------|
| **Hybrid RAG retrieval** | BM25 (sparse) + **InLegalBERT** (dense) + Reciprocal Rank Fusion + Cross-Encoder reranking — 4-stage retrieval for maximum relevance |
| **431K+ chunk corpus** | Pre-embedded Supreme Court judgments (20 years) provide statistical grounding for precedent matching |
| **DuckDB analytics** | Instant SQL queries over parquet files compute real win-rate statistics (allowed/dismissed/partly allowed rates) |
| **Dual pipeline modes** | Single-agent (default, low compute) and 4-agent adversarial mode (for government on-premise servers) — both produce APPEAL/COMPLY with full reasoning |
| **Deterministic rules engine** | Limitation Act §4, §12 deadline computation with court calendar holiday awareness — no LLM guesswork for legal deadlines |
| **Court hierarchy logic** | Automatic detection of correct appellate forum (Single Judge → Division Bench → Supreme Court) based on case type and bench composition |
| **Contempt risk classification** | Deterministic keyword classifier — 22 High-risk phrases + 14 Medium-risk phrases matched against the operative order text |
| **Result caching** | Full recommendation JSON cached in `full_rag_recommendation` field — no redundant LLM calls on revisit |

### 3. Effectiveness of Human Verification

| Feature | How We Achieve It |
|---------|-------------------|
| **Side-by-side PDF viewer** | `react-pdf` renders the original judgment alongside extracted data for visual cross-referencing |
| **Source highlighting** | Each directive links to its exact page and bounding box in the PDF via PyMuPDF spatial annotations |
| **Confidence indicators** | Extraction confidence and contempt risk levels are prominently displayed for reviewer attention |
| **Approve/Edit/Reject workflow** | Each action item can be individually verified; only approved records proceed to the dashboard |
| **Multi-level review chain** | `ReviewLog` model supports L1/L2 review levels with full audit trail (reviewer, timestamp, notes) |
| **Verification status tracking** | `verification_status` field on ActionPlan ensures only human-approved data reaches decision-makers |

### 4. Clarity and Usability of Dashboard

| Feature | How We Achieve It |
|---------|-------------------|
| **Premium glassmorphism UI** | Dark theme with backdrop blur, gradient accents, and smooth Framer Motion animations |
| **Live database-driven stats** | Dashboard fetches real case data — total cases, pending review, high-risk count, upcoming deadlines |
| **30-day deadline heatmap** | Visual calendar showing deadline density from actual compliance/appeal dates |
| **Risk board** | Priority-sorted cases by contempt risk and days remaining |
| **Collapsible sidebar** | Hamburger toggle with smooth 280px → 72px animation for maximum content area |
| **Role-based access** | User model with Reviewer, Dept Officer, Dept Head, Legal Advisor roles |
| **Responsive design** | Grid layouts with breakpoints for desktop, tablet, and mobile views |
| **JWT authentication** | Secure token-based auth with automatic token refresh |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/register/` | User registration |
| `POST` | `/api/auth/login/` | JWT login (returns access + refresh tokens) |
| `GET` | `/api/cases/` | List all cases |
| `POST` | `/api/cases/extract/` | Upload PDF → trigger full extraction pipeline |
| `GET` | `/api/cases/{uuid}/` | Case detail with judgments and action plans |
| `GET` | `/api/cases/{uuid}/status/` | Processing status of a case |
| `GET` | `/api/cases/{uuid}/action-plan/` | Get action plan for a case |
| `POST` | `/api/cases/action-plans/{id}/review/` | Submit human review (approve/edit/reject) |
| `POST` | `/api/action-plans/recommend/` | Trigger recommendation pipeline |
| `POST` | `/api/cases/{case}/judgments/{judgment}/appeal-strategy/` | Generate appeal strategy |
| `GET` | `/api/cases/judgments/{uuid}/pdf/` | Serve judgment PDF |

---

## ML Models Used

| Model | Source | Purpose | Runs On |
|-------|--------|---------|---------| 
| **Open-source LLM (fast)** | Cloud API or self-hosted | Structured extraction (Agents 1 & 4) | Cloud API / Local |
| **Open-source LLM (large)** | Cloud API or self-hosted | Complex legal reasoning (Agents 2 & 3) | Cloud API / Local |
| **InLegalBERT** | `law-ai/InLegalBERT` (HuggingFace) | Legal embeddings (768-dim), trained on 5.4M Indian legal docs | Local (CPU/GPU) |
| **Keyword Classifier** | Custom rule-based | Contempt risk classification (22 high-risk + 14 medium-risk legal phrases) | Local (no GPU needed) |
| **Cross-Encoder (open-source)** | HuggingFace | Cross-encoder reranking for RAG | Local (CPU) |
| **BM25Okapi** | `rank-bm25` | Sparse keyword retrieval | Local (CPU) |

---

## Team

Built for the **Centre for e-Governance Hackathon** — Theme 11: Court Judgments to Verified Action Plans.

---

## License

This project is licensed under the MIT License.
