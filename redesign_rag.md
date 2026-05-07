Final Architecture: Court Case AI Decision Support (Hackathon Optimized)
This concise blueprint defines a laptop-optimized, highly parallelized AI pipeline capable of processing millions of historical records without exhausting local storage or hitting API rate limits.

1. Laptop-Optimized Storage Layer
Do not download or OCR raw PDFs for historical data. Rely entirely on the pre-extracted .tar JSON/text archives [1].

Cold Storage (Metadata Analytics): Compress all structured case metadata (Case ID, Court, Date, Outcomes) into Parquet files. Use DuckDB as an in-process engine to query these files directly from disk. DuckDB can execute complex analytical filters over millions of rows in milliseconds using minimal RAM.

Hot Storage (Vector Database): Compute embeddings only for a filtered subset of critical cases (e.g., Supreme Court and the last 10 years of High Court cases). Store these locally using PostgreSQL with the pgvector extension (HNSW indexing) to maintain a tiny storage footprint (under a few GBs).

2. Zero-LLM Semantic Classification & Cluster-Gating
Because the AWS eCourts Parquet dataset natively provides basic structured metadata (such as Court Name, Case Number, and Date) [1], we eliminate the need for Regex extraction for these foundational fields. However, crucial semantic fields like area_of_law and case_type are often missing or inconsistent.

To categorize these millions of documents without hitting LLM API rate limits, we use a two-layer lightweight classification approach operating on the "short descriptions" or headnotes provided in the AWS metadata ``:

Layer 1 (DistilBERT Classifier): A lightweight, 66-million parameter classification model (DistilBERT) fine-tuned on the Indian Legal Documents Corpus (ILDC) ``. It evaluates the short description to accurately categorize the case into one of 47 areas of law and specific case types (e.g., Writ Petition, Special Leave Petition) natively on your laptop's CPU/GPU.

Layer 2 (K-Means Cluster Assignment): If the classifier is uncertain (confidence < 0.7), the system falls back to unsupervised K-Means clustering (k=500). By embedding the AWS short description with InLegalBERT, the case is assigned a cluster_id [2]. This guarantees that cases with similar semantic themes (e.g., property disputes) share a cluster ID, acting as a highly accurate soft-label pre-filter for the RAG pipeline even when explicit metadata is missing.

3. Three-Stage Hybrid Retrieval Pipeline
To prevent semantic contamination (mixing unrelated legal domains), use a strict retrieval funnel:

Stage 1: DuckDB Pre-filter: Query the Parquet files to reduce the candidate pool from millions to ~100k by filtering cluster_id, court jurisdiction, and date.

Stage 2: Hybrid RRF: Run sparse retrieval (BM25 for exact statute keyword matching) and dense vector retrieval in parallel on the pre-filtered set. Merge them using Reciprocal Rank Fusion (RRF) to get the Top 100.

Stage 3: Cross-Encoder Reranking: Pass the Top 100 query-document pairs through a legal cross-encoder. This solves the "semantic illusion" of bi-encoders and outputs a highly precise shortlist of the Top 5 most relevant cases.

4. Rate-Limit Optimized RAG (LangGraph)
To operate safely within the NVIDIA NIM free tier limit of 40 Requests Per Minute (RPM), we abandon massive parallel API calls for a context-stuffing approach.

Agent 1 (Historical Research - Context Stuffing): Instead of processing 20 cases sequentially or in parallel, the cross-encoder restricts the candidates to the Top 5 cases. The key extracted chunks from these 5 cases are concatenated into a single prompt. Llama 3.3 70B processes this combined context in one API call to output a JSON array of 5 research summaries, entirely circumventing the 40 RPM limit.

Rules Engine (Deterministic Analyzer): A pure Python script evaluates the metadata of the Top 5 cases to compute hard statistical win rates. It uses dateparser to calculate exact statutory limitation deadlines (e.g., 30 days for a Division Bench appeal), keeping this math away from the LLM.

Agent 2 (Legal Argument Mapper): Synthesizes the 5 case reports from Agent 1 into a structured landscape of pro-appeal and pro-compliance arguments.

Agent 3 (Adversarial Red-Team): Uses Llama 3.3 70B (with "detailed thinking" enabled via NVIDIA NIM) to actively probe the current case for procedural loopholes and assess contempt risks.

Agent 4 (Recommendation Synthesis): Aggregates insights from all agents and the Rules Engine to finalize the verdict and action plan.

5. Final Output Schema Integration
The final Agent 4 node strictly formats the output into your required JSON schema for the CCMS Dashboard:

JSON
{
  "recommendation_id": "uuid",
  "case_id": "e4f1a2b3-c5d6-4e7f-8a9b-0c1d2e3f4a5b",
  "status": "PENDING_VERIFICATION",
  "verdict": {
    "decision": "APPEAL",
    "appeal_to": "Division Bench",
    "confidence": 0.74,
    "urgency": "HIGH",
    "limitation_deadline": "2024-04-26",
    "days_remaining": 42
  },
  "statistical_basis": {
    "similar_cases_analyzed": 5,
    "government_appeal_win_rate": 0.67,
    "financial_exposure_if_comply": 1620000
  },
  "primary_reasoning": "Based on 5 similar service law cases, the government has a 67% appeal success rate at Division Bench level...",
  "appeal_grounds": [
  ...
  ],
  "alternative_routes": [
  ...
  ],
  "action_plan": {
    "immediate_actions": [
    ...
    ],
    "financial_actions": [
    ...
    ]
  }
}
