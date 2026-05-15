<div align="center">

# NyayaDrishti — Court Case Monitoring System (CCMS)

### From Court Judgments to Verified, Routed, Executable Action Plans

**Theme 11 — Centre for e-Governance, Government of Karnataka**

[Problem](#problem-statement) · [Workflow](#how-it-fits-the-karnataka-ccms-workflow) · [Architecture](#system-architecture) · [Agents](#agentic-workflow) · [Setup](#local-setup) · [Demo](#demo-runbook)

</div>

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Solution at a Glance](#solution-at-a-glance)
3. [How It Fits the Karnataka CCMS Workflow](#how-it-fits-the-karnataka-ccms-workflow)
4. [The 48-Department Routing Layer](#the-48-department-routing-layer)
5. [Role-Based Workspaces](#role-based-workspaces)
6. [System Architecture](#system-architecture)
7. [End-to-End Pipeline (5 Phases)](#end-to-end-pipeline-5-phases)
8. [Agentic Workflow](#agentic-workflow)
9. [PDF Source-Highlighting (Verifier Trust)](#pdf-source-highlighting-verifier-trust)
10. [Hybrid RAG Engine](#hybrid-rag-engine)
11. [Data Privacy & On-Premise Deployment](#data-privacy--on-premise-deployment)
12. [Tech Stack](#tech-stack)
13. [Local Setup](#local-setup)
14. [Demo Runbook](#demo-runbook)
15. [Project Structure](#project-structure)
16. [API Endpoints](#api-endpoints)
17. [Management Commands](#management-commands)
18. [ML Models](#ml-models)
19. [Evaluation Criteria Mapping](#evaluation-criteria-mapping)
20. [License & Team](#license--team)

---

## Problem Statement

The Government of Karnataka faces ~24,000 active litigations per year across 48 secretariat departments. The **Court Case Monitoring System (CCMS)** — which sits between the Karnataka High Court and the state secretariat — must convert judgment PDFs into actionable compliance steps before the **30-day Limitation Act deadline** expires.

### The realities on the ground today

| Problem | Why it happens | Impact |
|---|---|---|
| Judgments are 30–200 page legal PDFs | Operative directives are buried in dense reasoning | Officers miss critical instructions |
| No automated dept routing | A judgment naming "The State of Karnataka" doesn't tell you which dept must act | Files sit on the wrong desks |
| Manual deadline tracking | Limitation Act §4 & §12 math is non-trivial; vacation calendars complicate it | Contempt notices, missed appeals |
| Each role needs a different view | HLC verifies; LCO executes; Nodal Officer tracks deadlines | One dashboard cannot serve all |
| AI hallucination risk | Off-the-shelf LLMs invent treasury forms / refund codes / deadlines that don't exist | Loss of verifier trust |

### What NyayaDrishti delivers

```
PDF in  →  AI extracts directives  →  Classifier routes to right dept dashboard
        →  HLC verifies side-by-side with the highlighted PDF
        →  AI generates a GOVERNMENT-PERSPECTIVE action plan
        →  LCO executes; Nodal Officer watches deadlines
        →  Central Law sees the state-wide aggregate
```

A complete legal-intelligence platform built around the actual roles, deadlines, and constraints of the Karnataka State Secretariat.

---

## Solution at a Glance

NyayaDrishti is an **end-to-end AI pipeline + multi-role workflow application** that:

1. **Ingests** judgment PDFs (manual upload — 48-hour officer SLA; designed to plug into a CIS API when available)
2. **Extracts** structured data via a 4-agent LLM pipeline (one agent per logical section)
3. **Classifies** the responsible department from the 48-department taxonomy automatically
4. **Routes** the case to that department's dashboard (with verifier override available)
5. **Enriches** every directive with a government-perspective implementation plan
6. **Verifies** all outputs via a mandatory Head-of-Legal-Cell (HLC) review against the source PDF
7. **Executes** approved directives through a Litigation Conducting Officer (LCO) workflow
8. **Monitors** statutory deadlines for the Nodal Officer
9. **Aggregates** state-wide compliance at the Central Law / State Monitoring level

Everything runs on free or near-free open-source ML (InLegalBERT, ChromaDB, BM25, cross-encoder, DuckDB). LLM calls are routed through a cost-controlled cascade (OpenRouter Llama 8B + NVIDIA NIM Llama 70B + OpenRouter Gemini 2.5 Pro) — fully replaceable with self-hosted models for air-gapped deployments.

---

## How It Fits the Karnataka CCMS Workflow

The state CCMS doctrine defines 6 phases. NyayaDrishti implements them as follows:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ KARNATAKA CCMS PHASE                  │ NYAYADRISHTI IMPLEMENTATION          │
├───────────────────────────────────────┼──────────────────────────────────────┤
│ 1. INGESTION                          │ POST /api/cases/extract/  (manual    │
│    (CIS API OR 48-hr manual upload)   │  upload). SHA-256 hash dedup. The    │
│                                       │  same endpoint can be triggered by a │
│                                       │  CIS push when available.            │
├───────────────────────────────────────┼──────────────────────────────────────┤
│ 2. AI PROCESSING & AUTO-ROUTING       │ 4 extraction agents + LLM-first      │
│    Identify respondent → map dept     │  dept classifier (48 secretariat     │
│    Extract directives                 │  dept catalogue) writes Case.        │
│    Generate draft action plan         │  primary_department FK. Routing      │
│                                       │  filters every dashboard query.      │
├───────────────────────────────────────┼──────────────────────────────────────┤
│ 3. VERIFICATION (HLC)                 │ Verify Actions tab — side-by-side    │
│    HLC compares vs. highlighted PDF   │  PDF viewer with PyMuPDF source-     │
│    Approve / Edit / Reject            │  paragraph highlighting. HLC can     │
│    Provide appeal vs comply opinion   │  edit verbatim text, govt summary,   │
│                                       │  and per-directive implementation    │
│                                       │  steps. Backend 403s non-HLC writes. │
├───────────────────────────────────────┼──────────────────────────────────────┤
│ 4. EXECUTIVE DECISION                 │ HLC recommendation (APPEAL/COMPLY)   │
│    (Head of Dept convenes DRB)        │  surfaces on Head of Dept's view.    │
│                                       │  DRB workflow is plan roadmap (out   │
│                                       │  of MVP scope).                      │
├───────────────────────────────────────┼──────────────────────────────────────┤
│ 5. EXECUTION (LCO)                    │ LCO Execution dashboard — only       │
│    Physical implementation of tasks   │  HLC-verified, government-action     │
│                                       │  directives appear. Mark status,     │
│                                       │  upload proof file, record notes.    │
├───────────────────────────────────────┼──────────────────────────────────────┤
│ 6. MONITORING (Nodal Officer)         │ Nodal Deadline Monitor — sorts       │
│    Watch limitation deadlines         │  approved plans by urgency           │
│                                       │  (overdue / critical ≤3d /           │
│                                       │  warning ≤14d / safe). Computed      │
│                                       │  by rules_engine.py from Limitation  │
│                                       │  Act §4 & §12 + court calendar.      │
└───────────────────────────────────────┴──────────────────────────────────────┘
```

### Replacing the CIS API

Most state High Courts do not expose a public CIS API. NyayaDrishti is built so this isn't a blocker:

- **Primary path: manual upload** (the 48-hour officer SLA mandated by govt rules). Any departmental officer with an account can upload a judgment PDF; the AI handles the rest.
- **Bulk ingestion** via `python manage.py bulk_ingest --dir /path/to/pdfs/` for back-filling old judgments.
- **Future CIS hook**: the same `CaseExtractView` endpoint is callable by a CIS push job — no architectural change needed, only a credentials handshake.

---

## The 48-Department Routing Layer

Karnataka's Secretariat is 48 departments organised into 9 sectors. NyayaDrishti ships the full taxonomy:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ SECTOR                              │ EXAMPLE DEPARTMENTS                   │
├─────────────────────────────────────┼───────────────────────────────────────┤
│ Finance, Law & Core Administration  │ FINANCE, LAW, DPAR, REVENUE, IPR …    │
│ Home, Defence & Justice             │ HOME, EXCISE                          │
│ Health, Environment & Culture       │ HEALTH, AYUSH, MED_EDU, KANNADA_CULT  │
│ Education & Skill                   │ HIGHER_EDU, SCHOOL_EDU, TECH_EDU, …   │
│ Infrastructure & Public Works       │ PWD, INFRA_DEV, ENERGY, URBAN_DEV …   │
│ Agriculture & Allied                │ AGRICULTURE, HORTICULTURE, AHVS, …    │
│ Industries, Trade & Commerce        │ INDUSTRIES, IT_BT, COOPERATION, …     │
│ Social Welfare                      │ SOCIAL_WELFARE, MINORITIES, WCD, …    │
│ Rural Development & Panchayat Raj   │ RDPR, FOOD_CIVIL                      │
└─────────────────────────────────────┴───────────────────────────────────────┘
```

### How a case lands on the right dashboard

```
[Any user uploads PDF]
       │
       ▼
[4-agent extractor extracts parties / entities / operative text]
       │
       ▼
[dept_classifier.py — single NVIDIA NIM 70B call with the 48-dept catalogue]
       │  Returns: { primary: "FINANCE", secondary: ["REVENUE"], confidence: 0.9 }
       │
       ▼
[Case.primary_department FK set + secondary_departments M2M set]
       │
       ▼
[DepartmentScopedQuerysetMixin filters every list endpoint by user.department]
       │
       ▼
[Case appears ONLY in the AI-tagged department's dashboard]
[Central Law / State Monitoring see the cross-department aggregate]
```

### Verifier override

If the AI gets it wrong, the **HLC or Central Law role** can re-route the case via the override modal on the Case Overview screen. Each override writes a `ReviewLog` audit row (`action="department_override"`, reviewer, old → new primary, secondary changes).

### Karnataka-specific routing rules (baked into the classifier prompt)

| Subject matter | Department | Rationale |
|---|---|---|
| GST / VAT / commercial taxes | `FINANCE` | Commercial Taxes is a sub-bureau of Finance in Karnataka |
| Land acquisition / mutation / khata | `REVENUE` | Statutorily Revenue's domain |
| KPTCL / BESCOM / HESCOM / MESCOM | `ENERGY` | Electricity utilities |
| Karnataka Housing Board / KHB | `HOUSING` | Even when respondent is "Asst. Commissioner" |
| Criminal prosecution (IPC / CrPC) | `HOME` | Police / state prosecution |
| Medical negligence / drug control | `HEALTH` | Not MED_EDU which handles colleges |
| Motor Vehicles Act / claims | `TRANSPORT` | Finance as secondary if monetary award |
| Kannada language / state symbols | `KANNADA_CULTURE` | Cultural / regional |

---

## Role-Based Workspaces

NyayaDrishti ships dedicated workspaces for each statutory role, with permission-gated read/write access:

```
┌──────────────────────────────┬────────────────────────────────────────────────┐
│ ROLE                         │ LANDING VIEW & PERMISSIONS                     │
├──────────────────────────────┼────────────────────────────────────────────────┤
│ Head of Legal Cell (HLC)     │ Dashboard → Verify Actions tab                 │
│                              │ • Case Overview — dept assignment, case meta,  │
│                              │   AI Recommendation (APPEAL/COMPLY + contempt  │
│                              │   risk + deadline heatmap + similar cases)     │
│                              │ • Court Directions panel — timeline with        │
│                              │   urgency-coloured deadline pills, per-         │
│                              │   direction responsible-party footer, progress  │
│                              │   bar, verification node indicators             │
│                              │ • Verification & Final Decision banner —        │
│                              │   verified-by meta, order source, comply/appeal │
│                              │   decision lock with change option              │
│                              │ • Verify Actions tab — side-by-side PDF viewer  │
│                              │ • Approve / Edit / Reject each directive        │
│                              │ • Edit AI-generated implementation steps        │
│                              │ • Re-route case to another dept if needed       │
├──────────────────────────────┼────────────────────────────────────────────────┤
│ Litigation Conducting Officer│ Execution Dashboard (auto-landing)             │
│ (LCO)                        │ • Only HLC-verified, government-action items   │
│                              │ • Status: Pending / In-Progress / Completed /  │
│                              │   Blocked                                      │
│                              │ • Upload proof-of-compliance file              │
│                              │ • Add execution notes                          │
│                              │ • Read-only on Verify tab (cannot approve)     │
├──────────────────────────────┼────────────────────────────────────────────────┤
│ Nodal Officer                │ Deadline Monitor (auto-landing)                │
│                              │ • Approved Action Plans sorted by urgency      │
│                              │ • Overdue / Critical(≤3d) / Warning(≤14d)/Safe │
│                              │ • Limitation Act §4/§12 + court holidays       │
│                              │ • Read-only on Verify tab                      │
├──────────────────────────────┼────────────────────────────────────────────────┤
│ Central Law Department       │ Central View (auto-landing) — 48-tile grid     │
│                              │ • Total cases / high-risk / pending per dept   │
│                              │ • Drill into any dept's case list              │
│                              │ • Full Case Overview access across all depts    │
│                              │ • Can override department routing              │
│                              │ • Can verify (override authority)              │
├──────────────────────────────┼────────────────────────────────────────────────┤
│ State Monitoring Committee   │ Central View (same as Central Law) — audit     │
│                              │ • Read-only state-wide stats                   │
├──────────────────────────────┼────────────────────────────────────────────────┤
│ Head of Department           │ Dashboard for their dept (DRB roadmap)         │
└──────────────────────────────┴────────────────────────────────────────────────┘
```

### Server-side gating

All role gates are enforced **at the backend**, not just in the UI:

- `DepartmentScopedQuerysetMixin` filters every list endpoint by `user.department_id` (or no-op for global roles)
- `user_can_verify()` → only HLC and Central Law can POST to `/api/cases/action-plans/<id>/review/`
- `JudgmentUpdateView.update()` 403s non-verifier PATCH attempts
- `LCOExecutionListView` requires `gov_action_required=True AND isVerified=True` by default

Frontend reflects these gates with read-only badges and hidden buttons — but they're cosmetic on top of the backend enforcement.

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                      FRONTEND (React 19 + Vite 6 + Tailwind 4)               │
│                                                                              │
│  ┌────────────┐  ┌──────────┐  ┌──────────────┐  ┌────────────┐  ┌────────┐  │
│  │ Dashboard  │  │  Case    │  │   Verify     │  │ Execution  │  │Deadline│  │
│  │  (HLC)     │  │  List    │  │   Actions    │  │  (LCO)     │  │(Nodal) │  │
│  └────────────┘  └──────────┘  └──────────────┘  └────────────┘  └────────┘  │
│  ┌──────────────────────┐  ┌────────────────────┐                            │
│  │ Central View         │  │ Dept Override      │                            │
│  │ (48-tile grid)       │  │ Modal              │                            │
│  └──────────────────────┘  └────────────────────┘                            │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   │ REST API + JWT (with role + dept claims)
┌──────────────────────────────────▼───────────────────────────────────────────┐
│                     BACKEND (Django 5 + DRF + SimpleJWT)                     │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  INGESTION                                                          │    │
│  │  POST /api/cases/extract/   →  SHA-256 dedup  →  PyMuPDF4LLM        │    │
│  │  bulk_ingest mgmt command   →  Section Segmenter (bi-directional)   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  4-AGENT EXTRACTION (extractor.py)                                  │    │
│  │  Agent 1 — Registry Clerk    →  metadata    (OpenRouter Llama 8B)  │    │
│  │  Agent 2 — Legal Analyst     →  facts/issues(NVIDIA NIM 70B)        │    │
│  │  Agent 3 — Precedent Scholar →  ratio/cites (NVIDIA NIM 70B)        │    │
│  │  Agent 4 — Compliance Officer→  directives  (NVIDIA NIM 70B)        │    │
│  │  ≥25-page PDFs route all 4 via OpenRouter Llama 3.3 70B             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  DEPARTMENT CLASSIFIER (dept_classifier.py)                         │    │
│  │  NVIDIA NIM 70B + 48-dept catalogue + Karnataka routing rules       │    │
│  │  Falls back to keyword pass if LLM unavailable                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  DIRECTIVE ENRICHER (directive_enricher.py)                         │    │
│  │  OpenRouter Gemini 2.5 Pro with anti-hallucination guardrails       │    │
│  │  Tags actor_type, gov_action_required, implementation_steps         │    │
│  │  NVIDIA NIM 70B fallback                                            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  HYBRID RAG + RECOMMENDATION                                        │    │
│  │  BM25 + InLegalBERT dense → RRF → Cross-Encoder rerank              │    │
│  │  Corpus: ChromaDB + DuckDB-over-Parquet (~431K SC chunks)           │    │
│  │  Recommendation: single-agent OR 4-agent (Researcher → Devil's Adv  │    │
│  │  → Risk Auditor → Synthesizer)                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────┐  ┌──────────────────────┐  ┌────────────────────┐  │
│  │ Rules Engine        │  │ Contempt Risk        │  │ Court Hierarchy    │  │
│  │ Limitation Act §4/§12│ │ Classifier           │  │ Appeal Forum Logic │  │
│  │ + court calendar    │  │ (deterministic kw)   │  │                    │  │
│  └─────────────────────┘  └──────────────────────┘  └────────────────────┘  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  DATA LAYER                                                         │    │
│  │  PostgreSQL (prod) / SQLite (dev) — Case, Judgment, ActionPlan,    │    │
│  │     Department, ReviewLog, DirectiveExecution, User                 │    │
│  │  ChromaDB (persistent, local) — InLegalBERT 768-d vectors           │    │
│  │  DuckDB over Parquet — 431K+ SC judgment chunks                     │    │
│  │  Filesystem — judgment PDFs + LCO proof uploads                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## End-to-End Pipeline (5 Phases)

### Phase 1 — Ingestion

```
PDF Upload  →  SHA-256 Hash Check  ←  Existing? Return dedup hit (HTTP 200, no LLM cost)
                       │
                       │ New file
                       ▼
              Save to media/judgments/
                       │
                       ▼
              PyMuPDF4LLM → Layout-aware Markdown
                       │
                       ▼
              Section Segmenter (bi-directional regex)
                       │
              ┌────────┼────────┐
              ▼        ▼        ▼
            Header    Body   Operative
```

Key files: `services/pdf_processor.py`, `services/section_segmenter.py`. The segmenter uses 37+ legal trigger patterns specific to Indian HC judgment style, with 10% bidirectional overlap so no reasoning is lost at boundaries.

### Phase 2 — 4-Agent Extraction

Each agent receives **only its relevant section** with a strict Pydantic schema. See [Agentic Workflow](#agentic-workflow) for full details.

### Phase 3 — Routing + Enrichment

```
Extracted directives
       │
       ▼
[dept_classifier]  →  primary_department FK + secondary M2M
       │
       ▼
[directive_enricher] →  per-directive enrichment:
                          • actor_type (gov_dept / court / accused / 3rd-party / informational)
                          • gov_action_required (bool)
                          • implementation_steps (LCO-actionable bullets)
                          • display_note (for non-gov directives)
                          • govt_summary (one-liner for HLC scanning)
       │
       ▼
[PyMuPDF spatial annotation] → per-directive sourceLocation:
                                 • page number
                                 • line-level rects covering the FULL paragraph block
```

### Phase 4 — Human Verification (HLC, mandatory)

```
Verify Actions tab
       │
       ▼
Left: PDF viewer (react-pdf) with paragraph-level highlights
Right: Cards per directive
       │
       ▼
HLC actions per card:
       • Tick "Verified" checkbox
       • Edit verbatim text / govt summary / implementation steps
       • Delete spurious directives
       • "Show in PDF" button — explicit scroll to source paragraph
       │
       ▼
Cards sorted government-actions first, informational below (muted)
       │
       ▼
On Approve plan-level → verification_status = "approved"
                       → Only verified-AND-gov directives reach LCO Execution
```

### Phase 5 — Execute + Monitor

```
LCO EXECUTION                    NODAL DEADLINE MONITOR
─────────────                    ────────────────────────
For each verified gov-action     For each approved plan:
directive:                         compute next deadline =
  • Read implementation steps        min(internal_compliance_buffer,
  • Mark Pending → In Progress           compliance_deadline,
    → Completed                          internal_appeal_buffer,
  • Upload proof file                    statutory_appeal_deadline)
  • Add notes                       sort by urgency:
  • DirectiveExecution row             • overdue
    captures executed_by + ts          • critical (≤3d)
                                        • warning  (≤14d)
                                        • safe
                                        • unknown
```

---

## Agentic Workflow

NyayaDrishti uses LLM **agents** in three places: extraction, recommendation, and enrichment.

### A. 4-Agent Extraction Pipeline

The judgment PDF is segmented into 3 logical regions; each agent has a single responsibility and a Pydantic schema enforced via `response_format={"type": "json_object"}`:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ AGENT          │ INPUT       │ OUTPUT (Pydantic)            │ MODEL          │
├────────────────┼─────────────┼──────────────────────────────┼────────────────┤
│ 1. Registry    │ Header      │ case_number, court_name,     │ OpenRouter     │
│    Clerk       │ section     │ bench, judges, parties,      │ Llama 3.1 8B   │
│                │             │ date_of_order, appeal_type,  │ (cheap, fast)  │
│                │             │ lower_court_info             │                │
├────────────────┼─────────────┼──────────────────────────────┼────────────────┤
│ 2. Legal       │ Body        │ summary_of_facts,            │ NVIDIA NIM     │
│    Analyst     │ section     │ issues_framed[]              │ Llama 3.3 70B  │
├────────────────┼─────────────┼──────────────────────────────┼────────────────┤
│ 3. Precedent   │ Body        │ ratio_decidendi, area_of_law │ NVIDIA NIM     │
│    Scholar     │ section     │ primary_statute,             │ Llama 3.3 70B  │
│                │             │ citations[] with context,    │                │
│                │             │ entities[]                   │                │
├────────────────┼─────────────┼──────────────────────────────┼────────────────┤
│ 4. Compliance  │ Operative   │ disposition, winning_party,  │ NVIDIA NIM     │
│    Officer     │ order       │ operative_order_summary,     │ Llama 3.3 70B  │
│                │ section     │ court_directions[] (each     │ (most critical │
│                │             │   with text, responsible_    │  agent)        │
│                │             │   entity, action_required,   │                │
│                │             │   financial_details),        │                │
│                │             │ contempt_risk, financial[]   │                │
└────────────────┴─────────────┴──────────────────────────────┴────────────────┘
```

**Why 4 agents instead of one big call?**
- **Focused schemas** → fewer JSON parse failures and missed fields
- **Section-scoped input** → smaller per-call token budget; faster + cheaper
- **Independent retry** → if Agent 3's citations fail, Agents 1, 2, 4 still succeed
- **Cost shaping** → only the simple metadata agent uses the cheap 8B model; the three reasoning-heavy agents use the strong 70B model

**Large-PDF routing:** PDFs with ≥25 pages route **all 4 agents** through OpenRouter Llama 3.3 70B (which has larger context windows and no NIM rate limits). Threshold is configurable via `OPENROUTER_LARGE_PDF_THRESHOLD` env var.

### B. Department Classifier (single-shot)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ INPUT  : operative_text + body_text + entities + parties (concat ≤6K ch) │
│ MODEL  : NVIDIA NIM Llama 3.3 70B                                        │
│ PROMPT : full 48-dept catalogue + Karnataka routing rules                │
│ OUTPUT : { primary_code, secondary_codes[], rationale }                  │
│ FALLBK : keyword-scoring pass (deterministic) if LLM unreachable         │
└──────────────────────────────────────────────────────────────────────────┘
```

The prompt encodes domain knowledge like "GST → FINANCE (Commercial Taxes sits under Finance in Karnataka)" and "KPTCL service matters → ENERGY". Built-in negative examples prevent the model defaulting to HOME or TECH_EDU for ambiguous cases.

### C. Directive Enricher (the government-perspective lens)

Agent 4 extracts directives **verbatim** — that's the source-of-truth record. But a department officer needs an additional translation: *"is this for ME?"* and *"if so, what do I actually do?"*

```
┌──────────────────────────────────────────────────────────────────────────┐
│ INPUT  : case metadata + all extracted directives                        │
│ MODEL  : OpenRouter google/gemini-2.5-pro                                │
│          (Gemini chosen for stronger instruction-following — Llama 70B   │
│           confidently fabricates form numbers when pushed)               │
│ FALLBK : NVIDIA NIM Llama 3.3 70B                                        │
│                                                                          │
│ OUTPUT (per directive):                                                  │
│  • actor_type ∈ { government_department, court_or_registry,              │
│                   accused_or_petitioner, third_party, informational }    │
│  • gov_action_required: bool                                             │
│  • govt_summary: 1-line plain-English restatement                        │
│  • implementation_steps[]: 2-4 LCO-actionable bullets (gov only)         │
│  • display_note: "no action required because X" (non-gov only)           │
└──────────────────────────────────────────────────────────────────────────┘
```

**Anti-hallucination guardrails baked into the prompt:**

1. NEVER invent procedural specifics (form numbers, treasury codes, internal file IDs, deadlines) that aren't named in the operative order
2. Distinguish what the court ordered:
   - **Quashed an admin order** → reverse that administrative state (e.g. unblock GST ledger) — NOT a refund
   - **Declared a status** (exempt, eligible) → update assessment records — NOT a refund
   - **Directed payment** → only THEN process a payment
   - **Remanded** → reconsider afresh, NOT auto-grant relief
   - **Modified award with explicit math** → recalculate per the formula AND disburse
3. When in doubt, stay general ("update assessment records") rather than fabricate ("Form TCR-3")

### D. RAG Recommendation Pipeline (single-agent or 4-agent)

For the APPEAL-vs-COMPLY recommendation:

```
Case context
   │
   ▼
[Hybrid RAG]  →  Top-K legally-similar precedents (BM25 + InLegalBERT + RRF + Cross-Encoder)
   │
   ▼
[Rules Engine]  →  Statutory appeal deadline (Limitation Act + holidays)
   │
   ▼
[Recommendation Agents]
   ├─── Single-agent mode (default — cheap, fast)
   │     One reasoning pass over all context → APPEAL/COMPLY + confidence + rationale
   │
   └─── 4-agent mode (deeper, costlier)
         Agent 1 — Precedent Researcher → win-rate trend analysis
         Agent 2 — Devil's Advocate     → pro/con arguments
         Agent 3 — Risk Auditor         → contempt + financial risk
         Agent 4 — Decision Synthesizer → final verdict
         (final synthesis can use Gemini 2.5 Pro for strongest reasoning)
   │
   ▼
ActionPlan.full_rag_recommendation JSON (cached — revisits skip re-computation)
```

---

## PDF Source-Highlighting (Verifier Trust)

A verifier cannot trust an AI extraction without seeing the source. NyayaDrishti highlights **the full paragraph block** the directive came from:

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ALGORITHM (apps/cases/views.py :: _annotate_source_locations)            │
├──────────────────────────────────────────────────────────────────────────┤
│ 1. Build ranked snippet list from the directive text:                    │
│      • Longest start-of-text first (140, 100, 70, 45, 28 chars)          │
│      • Mid-text samples at offsets 50, 100, 180                          │
│      • Tail snippet (last 80 chars)                                      │
│                                                                          │
│ 2. For each snippet (in rank order):                                     │
│      For each PDF page (LAST page first — operative orders are at end):  │
│         try page.search_for(snippet)                                     │
│         on first match → use this as the anchor                          │
│                                                                          │
│ 3. Resolve anchor rect to its containing TEXT BLOCK via                  │
│    page.get_text("dict") — gives line-level bboxes                       │
│                                                                          │
│ 4. Return line rects for the ENTIRE block (the full paragraph).          │
│    If the directive overflows the block, walk forward to the next        │
│    adjacent block (gap < 60pt) until coverage > 55%.                     │
└──────────────────────────────────────────────────────────────────────────┘
```

**Why snippet-outer instead of page-outer?** If a directive's paragraph spans two pages, page-outer + reverse order causes the *tail* snippet on page N+1 to win before the *start* snippet on page N gets a chance — anchoring on the wrong page. Snippet-outer (earliest text first) fixes this.

**Frontend rendering** (`HighlightOverlay` in `VerifyActions.tsx`) takes the line rects, computes min/max bbox, clamps to standard text margins, and renders a yellow paragraph band with a side-bracket indicator. The "Show in PDF" button on each card explicitly scrolls the PDF viewer to that page.

---

## Hybrid RAG Engine

Built for legal-domain semantic search over 20 years of Supreme Court judgments:

```
┌──────────────────────────────────────────────────────────────────────────┐
│ STAGE                  │ TECHNOLOGY              │ PURPOSE                │
├────────────────────────┼─────────────────────────┼────────────────────────┤
│ 1. Sparse retrieval    │ BM25Okapi (rank-bm25)   │ Catch exact statute,   │
│                        │                         │ citation, party names  │
├────────────────────────┼─────────────────────────┼────────────────────────┤
│ 2. Dense retrieval     │ InLegalBERT (768-d)     │ Semantic match on      │
│                        │ via ChromaDB            │ legal reasoning        │
├────────────────────────┼─────────────────────────┼────────────────────────┤
│ 3. Fusion              │ Reciprocal Rank Fusion  │ Combine sparse+dense   │
│                        │ (RRF, k=60)             │ without score scaling  │
├────────────────────────┼─────────────────────────┼────────────────────────┤
│ 4. Rerank              │ Open-source             │ Final precision rank   │
│                        │ cross-encoder           │                        │
├────────────────────────┼─────────────────────────┼────────────────────────┤
│ 5. Analytics           │ DuckDB over Parquet     │ Win-rate stats across  │
│                        │                         │ ~431K case chunks      │
└────────────────────────┴─────────────────────────┴────────────────────────┘
```

Files: `apps/action_plans/services/rag_engine.py`, `apps/rag/embedder.py`, `apps/rag/parquet_store.py`.

---

## Data Privacy & On-Premise Deployment

NyayaDrishti is designed for the strict data-residency requirements of Indian digital public infrastructure:

| Component | Privacy posture |
|---|---|
| Django backend + PostgreSQL | Government datacenter |
| React frontend (static build) | Government datacenter or CDN |
| InLegalBERT (`law-ai/InLegalBERT`) | Runs **fully local** (CPU or GPU) |
| ChromaDB vector store | Local persistent volume |
| DuckDB analytics | Local files only |
| Cross-encoder reranker | Runs local |
| PDF storage | Local `media/judgments/` (or S3/MinIO) |
| LLM calls (current cloud setup) | OpenRouter + NVIDIA NIM — swappable |
| LLM (air-gapped option) | Self-host via `vLLM`, `Ollama`, or NVIDIA NIM private deployment — same OpenAI-compatible interface |

**Zero commercial-cloud lock-in.** Every external API uses the OpenAI-compatible chat-completions interface, so any cloud LLM provider can be swapped for a locally-hosted Llama / Mistral / Qwen / Gemma model with one environment-variable change.

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend SPA** | React 19, TypeScript, Vite 6 | Hot-reload dev, optimized production build |
| **Styling** | Tailwind 4 (Material 3 tokens), Framer Motion | Glassmorphism dark theme, smooth transitions |
| **PDF Viewer** | react-pdf + pdfjs-dist | In-browser rendering with paragraph highlights |
| **State** | React Context + hooks | Auth, theme, view routing |
| **Backend** | Django 5, Django REST Framework | REST API + ORM + migrations |
| **Auth** | SimpleJWT | JWT with custom claims (role + dept_id + dept_code) |
| **Database** | PostgreSQL (prod) / SQLite (dev) | Relational data |
| **PDF Parsing** | PyMuPDF4LLM + PyMuPDF | Layout-aware Markdown + spatial highlights |
| **LLM cascade (extraction)** | OpenRouter Llama 8B + NVIDIA NIM Llama 70B | Cost-shaped per-agent routing |
| **LLM (enrichment)** | OpenRouter Gemini 2.5 Pro | Strong instruction-following for anti-hallucination |
| **LLM (recommendation)** | NVIDIA NIM Llama 70B (default) / Gemini 2.5 Pro (4-agent final synth) | RAG-grounded reasoning |
| **Large PDF fallback** | OpenRouter Llama 3.3 70B | Pages ≥25 route all 4 extractors here |
| **Legal embeddings** | InLegalBERT (`law-ai/InLegalBERT`) | 768-d, trained on 5.4M Indian legal docs |
| **Vector store** | ChromaDB (persistent, local) | Dense similarity search |
| **Sparse retrieval** | BM25Okapi (`rank-bm25`) | Keyword/citation match |
| **Reranking** | Open-source cross-encoder | Final precision pass |
| **Fusion** | Reciprocal Rank Fusion | Sparse-dense score combination |
| **Analytics** | DuckDB over Parquet | SQL over ~431K judgment chunks |
| **Contempt risk** | Deterministic keyword classifier | No LLM guesswork on legal definitions |

---

## Local Setup

### Prerequisites

- **Python 3.12+**
- **Node.js 20+**
- **PostgreSQL 14+** (optional — SQLite works fine in dev)
- **8 GB RAM minimum** (16 GB recommended for InLegalBERT + cross-encoder)
- **~3 GB free disk** for the RAG corpus and ChromaDB store

### API keys required (one or more)

| Key | Used for | How to get it |
|---|---|---|
| `OPENROUTER_API_KEY` | Agent 1 (8B), large-PDF routing, directive enricher (Gemini 2.5 Pro) | https://openrouter.ai/ — free $1 credit on signup |
| `NVIDIA_API_KEY` | Agents 2/3/4 (70B), dept classifier | https://build.nvidia.com/ — free 1K req tier |
| `GEMINI_API_KEY` (optional) | 4-agent recommendation final synthesis | https://aistudio.google.com/ |
| `GROQ_API_KEY` (legacy) | No longer required — extraction has migrated off Groq | — |



### Step 1 — Clone & enter the repo

```bash
git clone https://github.com/Harsh-Mohta9163/Nyaya-Drishti.git
cd Nyaya-Drishti
```

### Step 2 — Download RAG data from Hugging Face

The 431K-chunk RAG corpus and pre-built ChromaDB store are **not** in git — they live on Hugging Face:

**Dataset:** [Harsh2005/nyaya-drishti-data](https://huggingface.co/datasets/Harsh2005/nyaya-drishti-data/tree/main)

```bash
pip install huggingface_hub

# Parquet embeddings (~280 MB)
huggingface-cli download Harsh2005/nyaya-drishti-data sc_embeddings.parquet \
  --repo-type dataset --local-dir backend/data/parquet/

# ChromaDB vector store (~1.8 GB)
huggingface-cli download Harsh2005/nyaya-drishti-data --repo-type dataset \
  --local-dir backend/data/ --include "chroma_db/*"
```

After download, your layout should look like:

```
backend/
└── data/
    ├── chroma_db/
    │   ├── chroma.sqlite3
    │   └── <uuid-folder>/
    │       ├── data_level0.bin
    │       ├── header.bin
    │       ├── length.bin
    │       └── link_lists.bin
    └── parquet/
        └── sc_embeddings.parquet
```

> Without these files the app still works, but the Similar Cases / Precedents tab will return empty results.

### Step 3 — Backend setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate           # Windows PowerShell
# source .venv/bin/activate      # Linux / macOS

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-ml.txt    # Heavy: torch, transformers, InLegalBERT

# Configure environment
cp .env.example .env
# Edit backend/.env and fill in:
#   DJANGO_SECRET_KEY=<run: python -c "import secrets; print(secrets.token_urlsafe(50))">
#   OPENROUTER_API_KEY=sk-or-...
#   NVIDIA_API_KEY=nvapi-...
#   GEMINI_API_KEY=...           (optional)
#   DATABASE_URL=postgresql://...  (optional — defaults to SQLite)

# Migrations
python manage.py migrate

# Seed the 48 departments + 13 demo user accounts
python manage.py seed_demo_data

# (Optional) Create your own Django admin user
python manage.py createsuperuser

# Start the dev server
python manage.py runserver 127.0.0.1:8000
```

### Step 4 — Frontend setup

```bash
cd frontend
npm install
npm run dev          # → http://localhost:3000
```

The frontend dev server proxies `/api/` and `/media/` to the backend at `127.0.0.1:8000`. JWT tokens are stored in `localStorage`.

### Step 5 — Verify the setup

Open `http://localhost:3000` and log in with one of the demo accounts (all use password `demo123`):

| Email | Role | What you'll see |
|---|---|---|
| `central_law@demo.local` | Central Law | Central View — 48-tile grid |
| `health_hlc@demo.local` | HLC | Health dept dashboard |
| `health_lco@demo.local` | LCO | Execution dashboard (Health) |
| `health_nodal@demo.local` | Nodal | Deadline monitor (Health) |
| `finance_lco@demo.local` | LCO | Execution dashboard (Finance) |
| `energy_lco@demo.local` | LCO | Execution dashboard (Energy) |

If you see the Central View load with 48 tiles, the backend + frontend + DB are all wired correctly.

---

## Demo Runbook

### Loading demo PDFs

The repo includes 6 anonymized High Court judgment PDFs in `backend/testcases/`:

```
backend/testcases/
├── constitutional_law.pdf       (Kannada cultural — dismissed)
├── crimial_law_1.PDF            (GST Rule 86A — K-9 Enterprises)
├── criminal_law.pdf             (Criminal IPC — Dr Renuka Prasad)
├── land_aquisition.pdf          (Land Acquisition + KHB)
├── service_law.pdf              (KPTCL service / increment)
└── tax_law.pdf                  (GST exemption — Taghar Vasudeva)
```

### Method 1 — Bulk ingest via CLI (recommended)

```bash
cd backend
.venv\Scripts\activate

# Walk every PDF in testcases/ sequentially with 8s sleep between
# (keeps you under NVIDIA NIM rate limits). SHA-256 hash dedup avoids
# re-extraction of files already in the DB.
python manage.py bulk_ingest --dir testcases/

# Options:
#   --sleep 4          # shorter delay if your NIM quota is healthy
#   --skip-dedup       # force re-extraction even if a hash already exists
```

Each PDF passes through:
1. PyMuPDF4LLM Markdown conversion
2. Section segmentation
3. 4-agent extraction
4. Department classification
5. Directive enrichment (Gemini 2.5 Pro)
6. PyMuPDF source-paragraph annotation

Expected time per PDF: 30–90 seconds depending on length.

### Method 2 — UI upload (single file)

Log in as any HLC, LCO, or Central Law user → click the "New Case Analysis" file picker in the sidebar → select a PDF. The upload runs the full pipeline and lands you on the case detail page when done. SHA-256 dedup returns the existing case if the same file was uploaded before.

### Method 3 — Direct API (for testing)

```bash
# Get a JWT
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"central_law@demo.local","password":"demo123"}' \
  | python -c "import json,sys; print(json.load(sys.stdin)['access'])")

# Upload one PDF
curl -X POST http://127.0.0.1:8000/api/cases/extract/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "pdf_file=@testcases/service_law.pdf"
```

### Demo-day preparation

Right before demo, run these three commands in order:

```bash
# 1. Re-seed 48 departments + 13 demo users (idempotent — safe to re-run)
python manage.py seed_demo_data

# 2. Ingest the demo PDFs (skips any already in DB by hash)
python manage.py bulk_ingest --dir testcases/

# 3. Re-set all approved Action Plans' deadlines to "today + N" so
#    nothing shows as overdue on stage. Also auto-approves any plans
#    not yet flagged approved.
python manage.py refresh_demo_deadlines
```



### What runs automatically on every upload

Every PDF you upload through the UI (or `bulk_ingest` CLI) now triggers the
full demo-ready pipeline — no follow-up commands needed:

```
1. SHA-256 hash dedup
2. PyMuPDF4LLM → Markdown + bi-directional section segmentation
3. 4-agent extraction
4. Department classification + auto-routing
5. PyMuPDF source-paragraph annotation
6. Directive enrichment (Gemini 2.5 Pro)            ← auto
7. ActionPlan get_or_create + demo deadlines        ← auto (today + N)
   (verification_status stays PENDING — HLC still verifies on stage)
```

Each step logs its outcome to the server console (`[Enrichment] case=… method=llm_gemini`,
`[DemoDeadlines] case=… compliance=2026-06-12 …`) so silent failures are visible.

### Resetting between rehearsals

If a rehearsal leaves the DB messy:

```bash
# Refresh deadlines on ALL existing plans + auto-approve them
# (use this when you want the LCO/Nodal tabs immediately populated)
python manage.py refresh_demo_deadlines

# Same as above but keep verification_status untouched
python manage.py refresh_demo_deadlines --no-approve

# Re-enrich existing directives (only needed if you've tweaked the enricher prompt)
python manage.py enrich_directives --force

# Nuke everything and start fresh (drops DB)
python manage.py flush --no-input
python manage.py seed_demo_data
python manage.py bulk_ingest --dir testcases/
```

---

## Project Structure

```
Nyaya-Drishti/
├── backend/
│   ├── apps/
│   │   ├── accounts/                         # Custom User + 6 statutory roles
│   │   │   ├── models.py                       Department, User
│   │   │   ├── permissions.py                  DepartmentScopedQuerysetMixin,
│   │   │   │                                   GLOBAL_ACCESS_ROLES, VERIFIER_ROLES
│   │   │   ├── serializers.py                  UserSerializer, EmailTokenObtainPair
│   │   │   └── management/commands/
│   │   │       └── seed_demo_data.py           48 depts + 13 demo users
│   │   │
│   │   ├── cases/                            # Case, Judgment, Citation
│   │   │   ├── models.py                       (UUID PKs, primary_department FK,
│   │   │   │                                   secondary_departments M2M,
│   │   │   │                                   pdf_hash for dedup)
│   │   │   ├── views.py                        CaseExtractView, ReAnnotateSourceView,
│   │   │   │                                   CaseDepartmentOverrideView,
│   │   │   │                                   ActionPlanReviewView,
│   │   │   │                                   _annotate_source_locations()
│   │   │   ├── services/
│   │   │   │   ├── pdf_processor.py            PyMuPDF4LLM → Markdown
│   │   │   │   ├── section_segmenter.py        Bi-directional regex segmenter
│   │   │   │   ├── extractor.py                4-agent extraction pipeline +
│   │   │   │   │                               _call_agent_8b (OpenRouter),
│   │   │   │   │                               _call_agent_70b (NVIDIA NIM),
│   │   │   │   │                               _call_openrouter_llama
│   │   │   │   ├── dept_classifier.py          48-dept LLM classifier
│   │   │   │   └── directive_enricher.py       Gemini 2.5 Pro govt-perspective
│   │   │   └── management/commands/
│   │   │       ├── bulk_ingest.py              Sequential PDF ingestion
│   │   │       ├── backfill_departments.py     Re-classify existing cases
│   │   │       └── enrich_directives.py        Backfill enrichment
│   │   │
│   │   ├── action_plans/                     # ActionPlan, DirectiveExecution
│   │   │   ├── models.py                       LimitationRule, CourtCalendar
│   │   │   ├── views.py                        LCOExecutionListView,
│   │   │   │                                   LCOExecutionDetailView,
│   │   │   │                                   GenerateRecommendationView
│   │   │   ├── services/
│   │   │   │   ├── rag_engine.py               Hybrid RAG (BM25+dense+RRF+rerank)
│   │   │   │   ├── recommendation_pipeline.py  Single-agent / 4-agent RAG
│   │   │   │   ├── rules_engine.py             Limitation Act §4/§12
│   │   │   │   ├── risk_classifier.py          Contempt risk (keyword)
│   │   │   │   └── appeal_strategist.py        Appeal strategy generator
│   │   │   └── management/commands/
│   │   │       └── refresh_demo_deadlines.py   Demo-day deadline reset
│   │   │
│   │   ├── rag/                              # Shared embedding/retrieval infra
│   │   │   ├── embedder.py                     InLegalBERT ChromaDB EF
│   │   │   ├── parquet_store.py                DuckDB analytics over parquet
│   │   │   └── classifier.py                   Zero-shot legal domain
│   │   │
│   │   ├── reviews/                          # ReviewLog audit chain
│   │   ├── dashboard/                        # Aggregation endpoints
│   │   │   ├── views.py                        DashboardStatsView,
│   │   │   │                                   NodalDeadlinesMonitorView,
│   │   │   │                                   DashboardByDepartmentView
│   │   │   └── urls.py
│   │   ├── notifications/
│   │   └── translation/
│   │
│   ├── config/                               # Django settings, root URLs
│   ├── data/                                 # Downloaded from HuggingFace
│   │   ├── chroma_db/                          ChromaDB persistent store
│   │   └── parquet/sc_embeddings.parquet       431K SC judgment chunks
│   ├── media/judgments/                      # Uploaded PDFs (gitignored)
│   ├── testcases/                            # 6 demo HC judgment PDFs
│   ├── requirements.txt
│   ├── requirements-ml.txt
│   └── manage.py
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.tsx                   Live stats + dept badge
│   │   │   ├── CaseList.tsx                    With dept filter chip
│   │   │   ├── CaseOverview.tsx                Case detail central view:
│   │   │   │                                   dept assignment card, case meta grid,
│   │   │   │                                   executive brief, AI Recommendation
│   │   │   │                                   (verdict + contempt risk + deadline
│   │   │   │                                   heatmap + similar cases RAG table),
│   │   │   │                                   Court Directions timeline (urgency-
│   │   │   │                                   coloured deadline pills, glowing
│   │   │   │                                   verification nodes, responsible-party
│   │   │   │                                   footer with initials avatar),
│   │   │   │                                   Verification & Final Decision banner
│   │   │   ├── CaseHeader.tsx                  Case metadata header
│   │   │   ├── VerifyActions.tsx               PDF side-by-side + edit UI
│   │   │   ├── Precedents.tsx                  Citation network + RAG matches
│   │   │   ├── Sidebar.tsx                     Govt-of-Karnataka branded
│   │   │   ├── CentralLawView.tsx              48-tile grid
│   │   │   ├── DepartmentOverrideModal.tsx     Verifier re-routing
│   │   │   ├── LCOExecutionView.tsx            Execution dashboard
│   │   │   └── NodalDeadlineView.tsx           Deadline monitor
│   │   ├── api/client.ts                       JWT-injected fetch wrapper
│   │   ├── context/AuthContext.tsx             User + role helpers
│   │   ├── App.tsx                             Routing + role-based default view
│   │   ├── LoginPage.tsx
│   │   ├── RegisterPage.tsx                    Responsive, 48-dept dropdown
│   │   ├── karnataka_govt_logo.png
│   │   └── images.d.ts
│   ├── vite.config.ts
│   └── package.json
│
├── CLAUDE.md                                 # AI agent guide (architecture notes)
├── .claude/settings.json                     # Project-wide permission allowlist
└── README.md                                 # ← you are here
```

---

## API Endpoints

| Method | Endpoint | Purpose | Auth |
|---|---|---|---|
| `POST` | `/api/auth/register/` | User signup with role + dept | None |
| `POST` | `/api/auth/login/` | JWT login (role + dept claims) | None |
| `GET` | `/api/auth/departments/` | List 48 departments | None |
| `GET` | `/api/cases/` | List cases (dept-scoped) | JWT |
| `POST` | `/api/cases/extract/` | Upload PDF → full pipeline (with dedup) | JWT |
| `GET` | `/api/cases/<uuid>/` | Case detail (dept-scoped) | JWT |
| `GET` | `/api/cases/<uuid>/status/` | Processing status | JWT |
| `PATCH` | `/api/cases/<uuid>/department/` | Verifier dept override | JWT (HLC/CL) |
| `POST` | `/api/cases/<uuid>/re-annotate/` | Re-run PDF source highlighting | JWT |
| `GET` | `/api/cases/judgments/<uuid>/pdf/` | Serve judgment PDF | JWT |
| `PATCH` | `/api/cases/judgments/<uuid>/` | HLC edits to extraction | JWT (HLC/CL) |
| `POST` | `/api/cases/action-plans/<id>/review/` | HLC approve/edit/reject | JWT (HLC/CL) |
| `GET` | `/api/cases/<uuid>/action-plan/` | Get action plan for a case | JWT |
| `POST` | `/api/action-plans/recommend/` | Trigger RAG recommendation | JWT |
| `GET` | `/api/action-plans/execution/` | LCO list (gov + verified only) | JWT |
| `PATCH` | `/api/action-plans/execution/<uuid>/` | LCO status + proof upload | JWT (dept) |
| `GET` | `/api/dashboard/stats/` | Dept-scoped headline stats | JWT |
| `GET` | `/api/dashboard/by-department/` | 48-dept aggregate (Central Law) | JWT (global) |
| `GET` | `/api/dashboard/deadlines-monitor/` | Nodal urgency-sorted list | JWT |
| `GET` | `/api/dashboard/high-risk/` | Contempt-risk-sorted list | JWT |

---

## Management Commands

```bash
# Department + user seeding
python manage.py seed_demo_data                  # 48 depts + 13 demo users (idempotent)

# Data ingestion
python manage.py bulk_ingest --dir testcases/    # Sequential PDF ingest with dedup
python manage.py backfill_departments [--force]  # Re-run dept classifier on existing cases

# AI enrichment
python manage.py enrich_directives [--force]     # Re-run Gemini enricher
                                                  # [--case-number-prefix PREFIX] [--sleep N]

# Demo prep
python manage.py refresh_demo_deadlines          # Future-dates approved ActionPlans

# RAG corpus management
python manage.py import_kaggle_embeddings --path /path/to/parquet/
python manage.py build_vectors
python manage.py rebuild_chromadb
python manage.py download_parquet
python manage.py classify_parquet
python manage.py export_for_merge
python manage.py import_merged_data
python manage.py reconcile_citations
python manage.py seed_court_calendar             # Karnataka court holidays
```

---

## ML Models

| Model | Source | Role | Runs |
|---|---|---|---|
| Llama 3.1 8B Instruct | OpenRouter `meta-llama/llama-3.1-8b-instruct` | Agent 1 (header metadata) | Cloud (cheap) |
| Llama 3.3 70B Instruct | NVIDIA NIM `meta/llama-3.3-70b-instruct` | Agents 2/3/4 + dept classifier | Cloud (free credits) |
| Llama 3.3 70B Instruct | OpenRouter `meta-llama/llama-3.3-70b-instruct` | All agents for ≥25-page PDFs | Cloud (paid, cheap) |
| Gemini 2.5 Pro | OpenRouter `google/gemini-2.5-pro` | Directive enricher | Cloud (paid) |
| Gemini 2.5 Pro | Google AI Studio (direct) | 4-agent recommendation final | Cloud (optional) |
| **InLegalBERT** | HuggingFace `law-ai/InLegalBERT` | 768-d legal embeddings — trained on 5.4M Indian legal docs | **Local CPU/GPU** |
| Cross-Encoder | HuggingFace open-source | RAG reranking | Local CPU |
| BM25Okapi | `rank-bm25` (PyPI) | Sparse retrieval | Local CPU |
| Contempt classifier | Custom keyword rules (22 high + 14 medium) | Deterministic risk scoring | Local — no GPU |

---

## Evaluation Criteria Mapping

### 1. Accuracy of Extraction

| Technique | How NyayaDrishti achieves it |
|---|---|
| **Layout-aware PDF parsing** | `PyMuPDF4LLM` produces clean Markdown preserving structure, tables, and reading order — far superior to raw text extraction |
| **Bi-directional regex segmenter** | 37+ legal trigger patterns specific to Indian HC judgments; bidirectional scan ensures no reasoning is lost at boundaries |
| **4 specialized LLM agents** | Each agent gets only its section + a strict Pydantic schema. Single-responsibility prompts reduce hallucination |
| **Cost-shaped LLM cascade** | Cheap 8B model for simple header parsing; strong 70B for reasoning-heavy facts/issues/operative agents |
| **Source highlighting** | PyMuPDF block-level resolution maps each directive to its **full paragraph** in the PDF for visual verification |
| **Fallback chains** | Every LLM call has retry + provider fallback. NVIDIA NIM → OpenRouter; OpenRouter → NVIDIA NIM as needed |
| **Per-case anti-hallucination enrichment** | Gemini 2.5 Pro with explicit prompt guardrails against fabricating form numbers / codes / deadlines |
| **SHA-256 dedup** | Same PDF uploaded twice short-circuits to the existing case — no spurious re-extraction |

### 2. Quality of Action Plan Generation

| Technique | How NyayaDrishti achieves it |
|---|---|
| **Hybrid RAG retrieval** | BM25 + InLegalBERT + RRF + cross-encoder rerank — 4-stage retrieval for max relevance |
| **431K-chunk corpus** | Pre-embedded SC judgments (20 years) provide statistical grounding |
| **DuckDB analytics** | Real win-rate statistics over parquet (allowed/dismissed/partly allowed rates) |
| **Government-perspective enricher** | Per-directive implementation steps + actor classification — directly answers "what does my dept do?" |
| **Karnataka-specific routing rules** | Dept classifier prompt encodes state-specific knowledge (GST→FINANCE, KPTCL→ENERGY, etc.) |
| **Single- + 4-agent recommendation** | Cheap default mode + adversarial mode for on-premise servers |
| **Deterministic rules engine** | Limitation Act §4/§12 + court holiday calendar → never trust the LLM for date math |
| **Court hierarchy logic** | Automatic appellate forum detection (Single Judge → Division Bench → SC) |
| **Result caching** | `full_rag_recommendation` JSON cache — revisits skip LLM re-run |

### 3. Effectiveness of Human Verification

| Feature | How NyayaDrishti achieves it |
|---|---|
| **Side-by-side PDF viewer** | `react-pdf` renders original judgment alongside extracted data |
| **Full-paragraph source highlighting** | PyMuPDF block resolution — every line of the directive's paragraph is highlighted, not just one phrase |
| **Explicit Show-in-PDF button** | Card click highlights without scrolling; explicit button triggers the jump |
| **Auto-collapse sidebar in Verify tab** | Maximises horizontal space for the PDF viewer |
| **Editable AI action plans** | HLC can rewrite the AI's govt summary + implementation steps inline |
| **Government Perspective Panel** | Green-bordered card per directive shows actor type + steps; muted card for non-gov informational items |
| **Per-directive verified flag** | HLC ticks each directive individually; only ticked items reach LCO Execution |
| **Server-side role enforcement** | Backend 403s non-HLC writes — UI gating is cosmetic, not the security boundary |
| **Multi-level review chain** | `ReviewLog` with L1/L2 review levels, audit trail (reviewer, timestamp, notes, action) |

### 4. Clarity and Usability of Dashboard

| Feature | How NyayaDrishti achieves it |
|---|---|
| **Material 3 glassmorphism** | Dark theme with `glass-card` surfaces, blue accents, smooth Framer Motion transitions |
| **Role-based default landing** | LCO → Execution, Nodal → Deadlines, Central Law → 48-tile grid, HLC → Dashboard |
| **Live database-driven stats** | Real-time totals, pending review, high-risk count, upcoming deadlines |
| **30-day deadline heatmap** | Visual calendar from actual compliance/appeal dates |
| **Risk board** | Priority-sorted by contempt risk + days remaining |
| **Department drill-down** | Click any of the 48 tiles → filtered case list with breadcrumb chip |
| **Government-of-Karnataka branding** | State crest in sidebar, official tagline |
| **Responsive layouts** | Phone / tablet / desktop breakpoints throughout |

#### Case Overview — central detail view

| Feature | Design detail |
|---|---|
| **Department Assignment card** | Square icon tile + monospace `RESPONSIBLE DEPT` / `ALSO AFFECTS` labels + indigo-tinted active pill for primary department + neutral surface pills for secondary departments + ghost Reassign button |
| **Court Directions & Action Plan panel** | Sticky right column with monospace order-date sub-line + verified/pending progress bar; each direction card shows a `DIRECTION · #01` monospace label, urgency-coloured deadline pill, direction body text, and a dashed-border footer with two-letter initials avatar + `RESPONSIBLE` label + `✓ Verified` badge |
| **Urgency-coloured deadline pills** | Dynamically coloured by timeframe: weeks → muted rose-red; 1 month → orange-amber; 2-3 months → soft amber; 4+ months → slate-sky; acknowledged/on-track → muted sage green |
| **Timeline verification nodes** | Circular nodes with double-ring glow shadow — emerald with checkmark for verified, amber with direction number for pending |
| **AI Recommendation card** | Rename from "AI Verdict" to "AI Recommendation"; shows APPEAL/COMPLY decision + confidence %, contempt risk badge, appeal grounds or key reasoning, CCMS perspective note, and a Key Deadlines block with limitation deadline / days remaining / urgency + animated heatmap bar |
| **Verification & Final Decision banner** | Full-width two-column card with green left-accent gradient; left col shows verification status (pending progress bar or verified meta — Verified By / Reviewed / Order Source rows), right col shows final decision locked (comply/appeal badge + Change button) or decision buttons disabled until verification complete |
| **Similar Cases & RAG Evidence table** | Similarity score bar + outcome label + core precedent text; "View All N Precedents" button when corpus returns more than 5 matches |

---

## License & Team

Built for the **Centre for e-Governance Hackathon — Theme 11**: Court Judgments to Verified Action Plans.

License: **MIT**.

External datasets:
- **InLegalBERT**: Apache 2.0 (HuggingFace `law-ai/InLegalBERT`)
- **NyayaDrishti RAG data**: [Harsh2005/nyaya-drishti-data](https://huggingface.co/datasets/Harsh2005/nyaya-drishti-data) — derived from publicly-available Supreme Court judgments

---

<div align="center">

**Built for the Government of Karnataka — Centre for e-Governance**

</div>
