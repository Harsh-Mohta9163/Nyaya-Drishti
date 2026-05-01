# NyayaDrishti
## Court Judgment Intelligence System for CCMS

**AI for Bharat Hackathon 2 | Theme 11: From Court Judgments to Verified Action Plans | Centre for e-Governance, Karnataka**

---

> **Core Idea**
>
> A judgment that goes untracked after disposal is justice delivered but not executed. **NyayaDrishti** reads the PDF, extracts what the court ordered, generates a verified action plan mapped to real CCMS workflow stages, and ensures no compliance deadline or appeal window is ever missed --- with a fully on-premise AI stack so sensitive state legal data never leaves government infrastructure.

---

## 1. Problem Framing

**What CCMS already does well:** fetches judgment PDFs automatically from the HC CIS the moment a case is disposed.

**The gap:** In the next 24 hours an officer must:

- Read a 40–80 page judgment manually
- Find the court's actual directions (buried in legal reasoning)
- Decide: comply or appeal?
- Calculate the limitation period
- Update the correct CCMS workflow stage

> **! Real Risks**
>
> - Missing compliance → **Contempt of Court**
> - Missing appeal window → **Permanent loss of legal recourse**
> - Both managed today by human memory alone

> **★ What We Observed in the Live CCMS Interface**
>
> CCMS already tracks a precise workflow: *LCO Proposal Stage* → *GA/LCO Authorization* → *Draft PWR* → *Approved PWR* → *Draft SO from Advocate* → *Affidavit Filing* → *Order Compliance Stage* → {*Proposed for Appeal* / *Closed with Appeal Number* / *Not to Appeal*}.
> **Every post-judgment action already has a named stage. NyayaDrishti is the intelligence layer that fills those stages automatically.**

---

## 2. System Flow Overview

```
[INGEST]  →  [PARSE]  →  [EXTRACT]  →  [VERIFY]  →  [DASHBOARD]
PDF via       Structure    Hybrid AI    Human-in-    Verified
CCMS API      Detection    Engine       Loop         Only
```

- **01 Ingest:** OCR if scanned; logged with metadata
- **02 Parse:** Section-aware splitting; operative order isolated
- **03 Extract:** LLM + Rules Engine + RAG
- **04 Verify:** 3-level human review; confidence scoring
- **05 Dashboard:** CCMS-mapped, role-based, verified records only

---

## 3. Extraction Strategy — Handling Unstructured PDFs

### The Core Challenge

Judgments arrive as scanned images, digital-born PDFs, or hybrid documents. They are 10–80 pages of dense legal prose. Generic OCR + LLM pipelines fail because they treat the entire document as equal --- the reasoning section looks textually similar to the operative order but is not actionable.

### Structure-Aware Parsing Pipeline

```
PDF Input                 Layout-Preserving OCR        Section Segmenter
(Digital / Scanned)  →   PyMuPDF + LayoutLMv3      →  Pattern + ML classifier
                          Tesseract fallback
                                                              ↓
                                              ┌───────────────────────────────┐
                                              │  OPERATIVE ORDER              │
                                              │  Full extraction              │
                                              │  95% of directives live here  │
                                              ├───────────────────────────────┤
                                              │  Header                       │
                                              │  Case No., Bench, Parties,    │
                                              │  Date                         │
                                              ├───────────────────────────────┤
                                              │  Brief Facts                  │
                                              │  Context only                 │
                                              ├───────────────────────────────┤
                                              │  Legal Analysis               │
                                              │  Reasoning                    │
                                              └───────────────────────────────┘
```

### Why Section Targeting Matters

- **Operative order section:** Full LLM extraction — every direction parsed verbatim
- **Header section:** Rule-based extraction for case no., bench, dates, parties
- **Facts / Analysis sections:** Context only; never confused with actionable orders
- Every extracted field is anchored to `(page, paragraph, char_offset)` for PDF highlighting during review

### Handling Scanned & Inconsistent PDFs

| **PDF Type** | **Detection Method** | **Processing Strategy** |
|---|---|---|
| Digital-born | PyMuPDF text layer present | Direct text extraction; paragraph boundaries preserved |
| Scanned (image) | No text layer; rasterized pages | Tesseract + LayoutLMv3 for layout-aware OCR |
| Hybrid | Partial text + image blocks | Block-level detection; per-block routing |
| Damaged / low-res | Confidence score < 0.6 | Flagged for manual review before extraction |

### 3-Dimensional Confidence Score

Each extracted field carries: **OCR Confidence** × **Extraction Model Confidence** × **Rules Engine Agreement**

Low OCR + High LLM ≠ reliable. All three dimensions must align for a high confidence tag.

---

## 4. Action Plan Generation — Hybrid Legal Intelligence Engine

> **★ Design Principle**
>
> **AI for Language. Rules for Law.** The LLM identifies *what* the court said. A deterministic rules engine computes *when* the deadline is. Never trust a language model with a limitation period.

### Three Sub-Components in Parallel

```
                    Parsed Judgment Sections
                   /           |            \
                  ↓            ↓             ↓
      ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────────┐
      │ LLM Extraction  │  │ Statutory Rules  │  │ RAG Appeal           │
      │ Agent           │  │ Engine           │  │ Intelligence         │
      │                 │  │                  │  │                      │
      │ On-premise      │  │ Limitation Act,  │  │ FAISS over           │
      │ Mistral / Sarvam│  │ 1963             │  │ Karnataka HC corpus  │
      │ via Ollama      │  │ (Deterministic)  │  │ (AWS court=27_1)     │
      │                 │  │                  │  │                      │
      │ Extracts:       │  │ Computes:        │  │ Provides:            │
      │ -- Court dirs   │  │ -- SLP → 90 days │  │ -- Similar past      │
      │    (verbatim)   │  │    (Art. 116)    │  │    judgments         │
      │ -- Responsible  │  │ -- Review → 30d  │  │ -- Known appeal      │
      │    entities     │  │    (O.47 CPC)    │  │    outcomes          │
      │ -- Nature of    │  │ -- LPA → 30 days │  │ -- Issue-type match  │
      │    order        │  │ -- Writ compliance│  │ -- Evidence-grounded │
      │ -- Financial    │  │    windows       │  │    comply vs. appeal  │
      │    penalties    │  │ -- Internal govt.│  │    signal            │
      │ -- Case type    │  │    deadlines     │  │                      │
      └────────┬────────┘  └───────┬──────────┘  └──────────┬───────────┘
               └────────────────────┼──────────────────────────┘
                                    ↓
                         Merged Action Plan Output
```

### What the Action Plan Contains

| **Action Field** | **Description** |
|---|---|
| Comply / Appeal Flag | AI recommendation with confidence score; RAG evidence from past similar cases |
| Compliance Actions | Step-by-step actions the department must take to satisfy the order |
| Legal Deadline | Rules engine output: exact date, statutory basis cited |
| Internal Deadline | Earlier government policy deadline for deciding on appeal |
| Responsible Department | Primary dept. + secondary depts. if interdependence detected |
| CCMS Stage Mapping | Explicit instruction: which CCMS stage to move this case to |
| Contempt Risk Level | **High** / **Medium** / **Low** from classifier |
| Case Type | Civil Contempt Petition / Writ Appeal / Writ Petition / S-KSAT |

### Contempt Risk Classifier

- Fine-tuned **InLegalBERT** on Karnataka HC judgment corpus
- Detects high-risk directive language patterns:
  - *"shall comply without fail"*  *"failing which coercive action"*  *"personal appearance of the Secretary"*
  - *"is hereby directed under threat of contempt"*  *"immediate compliance required"*
- Output: 3-level risk tag **(High / Medium / Low)** attached to each directive
- **High-risk cases bypass the standard queue** --- surfaced immediately to the Department Head's dashboard regardless of deadline proximity

### RAG Appeal Intelligence Strategy

- **Corpus:** Karnataka HC judgments (2018–2024) from AWS Open Data Registry (`court=27_1`) with known appeal outcomes
- **Retrieval:** Given the extracted issue type + court finding, retrieve the 3–5 most similar past cases using FAISS vector search
- **Output surface:** *"In 4 of 5 similar cases involving [issue type], appeals were unsuccessful. Grounds: [X]. Recommend compliance."*
- Officers get **evidence-grounded reasoning**, not a language model's guess

---

## 5. Department Interdependence Handling

Many Karnataka HC judgments name multiple secretariat departments or imply cross-departmental action. No other solution in this space addresses this.

### Detection

- LLM extracts all named government entities from the operative order
- Entity resolution maps names to CCMS department codes
- If > 1 department detected → interdependence flag raised

### Dependency Graph

```
Revenue Dept                           Finance Dept
(Primary Respondent)  ── funds needed ──→  (Fund Release Required)
        |                                        ↑
        | legal advice                    appeal rec. (dashed)
        ↓                                        |
    Law Dept  ────────────────────────────────────
 (Appeal Decision)
        |
        ↓
  CCMS: Order Compliance Stage
  Primary dept. must act before Finance release
```

### Sequenced Action Plan

- Actions are ordered: **Action A must complete before Action B can begin**
- The dashboard shows each department its specific slice of the action plan only
- Shared deadline is visible to all; per-department sub-deadlines are computed
- If Department A has not marked their action complete, Department B receives an automated escalation alert
- Audit trail captures which department completed what and when

---

## 6. Human Verification — 3-Level Review

| **Level** | **What the Reviewer Sees** | **Actions Available** |
|---|---|---|
| Field-Level | Each extracted field + highlighted PDF source span + confidence score | Approve / Edit / Reject per field; conflict detection if edits create logical inconsistency |
| Directive-Level | Each court direction + generated action plan side-by-side | Approve / Edit / Reject per directive; attach dept. routing and deadline |
| Case-Level | Full case summary with all verified fields and action plans | Final sign-off; only after this does the record reach the Dashboard |

### Conflict Detection

If a reviewer edit creates a logical inconsistency --- e.g., changing the order date to after the compliance deadline --- the system **flags the conflict** before allowing approval.

### Continuous Learning from Feedback

- Edit → correction stored as labelled training pair
- Reject + rewrite → (AI plan, human plan) stored
- **LoRA adapters** retrain the on-premise model periodically on accumulated corrections
- Model improves on Karnataka-specific legal language **over time with real use**

---

## 7. Dashboard — Trusted View Only

### Role-Based Views

| **Role** | **What They See** |
|---|---|
| Reviewer | Verification queue; PDF side-panel; confidence scores; edit interface |
| Dept. Officer | Their department's verified action plans; deadline countdown; CCMS stage mapping |
| Dept. Head | Aggregate summary; contempt risk board; cases pending action; interdependence alerts |
| Legal Advisor | Appeal-recommended cases; RAG evidence panel; limitation period tracker |

### Key Dashboard Features

- **Deadline Heatmap** --- visual calendar; 7 / 30 / 90 day views; colour-coded urgency
- **Contempt Risk Board** --- High-risk cases pinned at top regardless of deadline distance
- **Appeal Window Countdown** --- live timer on limitation period for each case
- **Case Type Filter** --- Writ Petition / Civil Contempt Petition / Writ Appeal / S-KSAT (matching CCMS exactly)
- **Department Dependency View** --- sequenced action map for multi-dept. cases
- **Full Audit Trail** --- every AI output, reviewer edit, approval logged with user identity and timestamp
- **Kannada Interface** --- IndicTrans2 (IIT Madras) translation, runs fully on-premise

### CCMS Stage Mapping

| **Judgment Outcome** | **NyayaDrishti Action** | **CCMS Stage** |
|---|---|---|
| Compliance direction issued | Compliance plan + dept. + deadline | Order Compliance Stage |
| Appeal grounds identified | Limitation period + escalation path | Proposed for Appeal |
| Appeal filed and closed | Archive with appeal number | Closed with Appeal Number |
| No appeal warranted | Archive with compliance confirmation | Not to Appeal |
| Draft Standing Order needed | GA/LCO authorization workflow | Draft SO from Advocate |
| High contempt risk detected | Immediate senior officer alert | Civil Contempt track |

---

## 8. Evaluation Criteria Alignment

| **Criterion** | **How NyayaDrishti Addresses It** |
|---|---|
| Accuracy of Extraction | • Structure-aware parsing targets *operative order* specifically, not the entire document  <br>• 3-dimensional confidence score: OCR × extraction × rules-engine agreement  <br>• Layout-preserving OCR retains paragraph boundaries crucial for directive isolation  <br>• Every field anchored to PDF source location for full verifiability |
| Quality of Action Plan | • Statutory rules engine: deadlines from actual Limitation Act provisions, not LLM inference  <br>• RAG: evidence from past Karnataka HC cases with known outcomes  <br>• Contempt risk classifier flags high-risk directives explicitly  <br>• Action plans map directly to named CCMS stages departments already use |
| Effectiveness of Human Verification | • 3-level review (field / directive / case) with PDF inline highlighting  <br>• Conflict detection prevents logical errors introduced during review  <br>• LoRA fine-tuning pipeline: system improves from every correction reviewers make  <br>• Full before/after edit log for accountability |
| Clarity & Usability of Dashboard | • Case type filter matches CCMS exactly; no new concepts for officers to learn  <br>• Contempt risk board, appeal countdown, deadline heatmap  <br>• Role-based views: each user sees only what is relevant to their decisions  <br>• Kannada interface for Kannada-medium officials |

---

## 9. Technical Stack

| **Component** | **Technology** | **Reason** |
|---|---|---|
| PDF Parsing | PyMuPDF + LayoutLMv3 | Layout-preserving; retains paragraph metadata |
| OCR | Tesseract + preprocessing | Open-source; fully on-premise |
| LLM | Mistral 7B / LLaMA 3 / Sarvam via Ollama | **No data leaves govt. network** |
| Rules Engine | Python — Limitation Act 1963 | Deterministic; legally reliable deadlines |
| Contempt Classifier | Fine-tuned InLegalBERT | Trained on Karnataka HC corpus |
| RAG / Vector Store | FAISS + Karnataka HC dataset | Evidence-grounded appeal recommendations |
| Fine-tuning | LoRA adapters on reviewer edits | Continuous improvement from human corrections |
| Backend | FastAPI, PostgreSQL, Redis | Reliable; widely used in govt. deployments |
| Frontend | React + Tailwind CSS + PDF.js | Inline PDF highlighting during verification |
| Translation | IndicTrans2 (IIT Madras) | Kannada support; runs locally |
| Deployment | Docker on NIC Cloud / Govt. private infra | Data sovereignty guaranteed |

---

## 10. Privacy, Constraints & Deployment

### Privacy-First Architecture

- **Fully on-premise LLM** (Ollama): no judgment text ever sent to external APIs
- All ML models (classifier, RAG, fine-tuning) run within government infrastructure
- Kannada translation via IndicTrans2: local inference only

### Deployment Phases

1. Karnataka HC judgments, all benches and secretariat depts.
2. District courts and tribunals across Karnataka
3. Statewide multi-dept. deployment; model fine-tuned per dept.
4. eCourts API integration for all-India scalability

---

> **★ Five Differentiators**
>
> 1. **Structure-aware operative order parsing** --- not generic full-document summarisation
> 2. **Statutory rules engine** --- Limitation Act provisions hard-coded, not inferred by AI
> 3. **RAG-based appeal intelligence** --- evidence from past Karnataka HC cases, not LLM opinion
> 4. **Continuous learning from reviewer corrections** --- LoRA fine-tuning; improves with real use
> 5. **CCMS-native output** --- action plans map to stages departments already know and use