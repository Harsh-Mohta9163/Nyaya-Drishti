# NyayaDrishti — Demo Video Script (5 Minutes)
### Revised: Demo-as-you-go format

> **Target:** AI for Bharat Hackathon — Theme 11: Court Judgments to Verified Action Plans  
> **Duration:** ~5 minutes  
> **Format:** Narration + live screen recording running end-to-end, section by section  
> **Tone:** Confident, concise, human

---

## SECTION 1 — THE PROBLEM (0:00 – 0:40)

**[SCREEN: Title card → cut to a plain PDF of a real Karnataka High Court judgment — dense legalese, 30 pages]**

**PRESENTER:**

> Every day, the Karnataka High Court disposes of cases involving government departments. The judgment — a 30-page PDF — lands in the Court Case Monitoring System. And then, a government officer has to read the entire thing to figure out: *What do we do now? Do we comply? Do we appeal? What's the deadline? Who's responsible?*
>
> Miss a deadline — contempt proceedings. Misread a directive — crores go unaccounted for.
>
> This is the problem NyayaDrishti solves. Let me show you exactly how.

---

## SECTION 2 — STEP 1: UPLOAD & AI EXTRACTION (0:40 – 1:45)

**[SCREEN: NyayaDrishti login → Case list dashboard → Click "New Case Analysis"]**

**PRESENTER:**

> We start by uploading the judgment PDF. The officer selects the file — and from here, everything is automated.

**[SCREEN: Upload dialog → progress indicator showing extraction running]**

> Behind the scenes, our **4-agent extraction pipeline** kicks in immediately.
>
> First, **PyMuPDF4LLM** converts the PDF into clean, structured text — handling both digital and scanned documents.
>
> Then four specialized AI agents take over — each with a distinct job:
>
> - **Agent 1** pulls the registry details: case number, court, bench composition, parties, and the date of the order.
> - **Agent 2** reads the full judgment and writes a concise summary of facts and the legal issues framed by the court.
> - **Agent 3** identifies every case citation in the judgment — whether each precedent was relied upon, distinguished, or overruled — and extracts the ratio decidendi.
> - **Agent 4**, the most critical one, goes through the operative order and extracts every single actionable directive — with the full verbatim text, the responsible entity, deadlines, and any financial implications. It also flags the contempt risk.

**[SCREEN: Case opens → Case Overview tab → Case Details card populated — jurisdiction, bench, filing date, case type, statute]**

> Here's the result. The case details are already filled in. Jurisdiction, bench, date of order, area of law, primary statute.

**[SCREEN: Scroll down → Executive Case Brief card — Summary of Facts + Issues Framed visible]**

> Below that — the Executive Case Brief. A clean, readable summary of what this case is actually about, and the legal questions the court addressed. Every officer can read this in under a minute and understand the case.
>
> No more reading 30 pages of legalese.

---

## SECTION 3 — STEP 2: HUMAN VERIFICATION (1:45 – 2:45)

**[SCREEN: Click "Verify Actions" tab → side-by-side view — PDF on the left, extracted directives on the right]**

**PRESENTER:**

> Now, before any of this data moves forward, a human has to verify it. This is mandatory — and it's the core of our design.
>
> On the left, the original PDF. On the right, the extracted court directives.

**[SCREEN: Click on a court direction in the right panel → PDF auto-scrolls and highlights the exact paragraph in yellow]**

> Watch what happens when I click on a directive. The PDF **instantly scrolls to the exact paragraph** where that direction was found — and highlights it. This is powered by PyMuPDF bounding boxes. The officer is not trusting the AI blindly — they can read the original text, word for word, right next to the extraction.
>
> They can approve it, edit it if something is off, or reject it entirely.

**[SCREEN: Check the checkbox → direction turns green with "✓ Verified" badge]**

> Once they're satisfied, they verify. Each directive gets a clear status — verified or pending. Only verified directives move forward to the dashboard.

**[SCREEN: Show the 0/1 → 1/1 counter update, "Verify All" button]**

> There's also a "Verify All" option for straightforward cases — and an "Add Action" button if the officer needs to add a directive the AI may have missed.
>
> This is what explainability looks like in practice. Not a confidence score in a corner — the actual source, highlighted, right there.

---

## SECTION 4 — STEP 3: SIMILAR CASES FROM 20 YEARS OF SUPREME COURT JUDGMENTS (2:45 – 3:30)

**[SCREEN: Back on Case Overview → scroll to Similar Cases & RAG Evidence card at the bottom]**

**PRESENTER:**

> Here's something no manual process can do.
>
> We built a **Retrieval-Augmented Generation pipeline** over a **20-year corpus of Supreme Court judgments**. The case text is embedded using **InLegalBERT** — a transformer model pre-trained on 5.4 million Indian legal documents — and stored in a vector database.
>
> When a new case is analyzed, we search the entire corpus for the most legally similar cases.

**[SCREEN: Similar Cases table visible — Case IDs, similarity scores, outcome (Allowed/Dismissed), core precedent text]**

> Right here — the top similar cases, with similarity scores and outcomes. An officer can see: *"In comparable cases, the court consistently ruled this way. Here's the key legal principle."*
>
> This gives the government real context — grounded in two decades of actual Supreme Court jurisprudence — not just the AI's opinion.

---

## SECTION 5 — STEP 4: AI RECOMMENDATION (3:30 – 4:15)

**[SCREEN: Scroll up to the AI Verdict card — "COMPLY" or "APPEAL" badge, confidence bar, contempt urgency indicator]**

**PRESENTER:**

> With all of this context in hand, NyayaDrishti generates an **AI recommendation** — should the government appeal this order, or comply with it?
>
> This is powered by **DeepSeek V4 Pro** — a reasoning-optimized model. We feed it the operative order, the ratio decidendi, the court directions, and the Indian court hierarchy — so it understands, for instance, that a Division Bench order goes to the Supreme Court via Special Leave Petition.

**[SCREEN: Expand the AI Verdict → show Primary Reasoning text, Appeal Grounds list, Risk Summary]**

> The verdict comes with a confidence score, a contempt urgency level, and — critically — **the reasoning**. 
>
> Let's look at this specific test case, a land acquisition dispute. The AI recommends to **Comply**. And its reasoning is brilliant. It points out that an appeal to the Supreme Court is unlikely to succeed because the Division Bench applied well-settled law regarding consent awards under Section 11. 
>
> But it goes further and does a financial cost-of-delay analysis. It calculates that while the principal amount of ₹3.3 Lakhs per acre is modest, a 3-5 year appeal process would accrue statutory interest under the Land Acquisition Act at 9-15%, potentially doubling the government's liability. The AI concludes that the guaranteed interest cost of a failed appeal far outweighs any potential savings.
>
> This is deep, contextual, legally and financially sound reasoning — not just a random guess.
>
> And if the officer still disagrees with the AI's call, they can override it — right from this screen.

**[SCREEN: Show Appeal / Comply buttons — officer clicks one → status updates]**

> The final decision is the officer's. The AI is a powerful second opinion, not the final word.

---

## SECTION 6 — THE RESULT: TRUSTED DASHBOARD (4:15 – 4:50)

**[SCREEN: Back to the Case List / Dashboard — cases showing "Verified" badges, risk levels, compliance status]**

**PRESENTER:**

> Once verified and decided, the case is visible on the dashboard — and only then.
>
> Decision-makers see exactly what they need: which cases require compliance action, which are being appealed, what the deadlines are, and which are high contempt risk. Clean, reliable, verified.
>
> Nothing on this dashboard is unreviewed AI output. Every record passed through a human.

---

## SECTION 7 — CLOSE (4:50 – 5:00)

**[SCREEN: Summary slide — NyayaDrishti logo + key differentiators in 5 bullets]**

**PRESENTER:**

> NyayaDrishti is built for Indian courts, Indian law, and Indian government workflows. A 4-agent extraction pipeline. Source-level verification with PDF tracing. 20 years of Supreme Court precedents at your fingertips. An AI recommendation you can actually read and challenge. And a dashboard that only shows what's been verified.
>
> This is what trustworthy legal AI looks like. Thank you.

**[SCREEN: End card — Team name / Contact]**

---

## SECTION 8 — ON-PREMISE / OFFLINE DEPLOYMENT FOR GOVERNMENT (5:00 – 5:30)

**[SCREEN: Slide showing architecture diagram with "On-Premise" box]**

**PRESENTER:**

> For government deployments where data privacy is critical, NyayaDrishti can run entirely offline — no internet required.

**[SCREEN: Terminal showing Ollama running locally]**

> Here's how it works.
>
> **Local LLM Inference with Ollama:**
> - We use **Ollama** to run open-source models like Llama 3, Mistral, or Phi-3 directly on the government server
> - All LLM inference happens on-premise — no data leaves the network
> - Configure `LLM_PROVIDER=ollama` in settings, and point to your local model endpoint

**[SCREEN: Code snippet showing settings]**

```python
# settings.py - Government Server Configuration
LLM_PROVIDER = "ollama"
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3:70b"  # or "mistral", "phi-3"
```

> **Local Embeddings with sentence-transformers:**
> - Instead of calling OpenAI or NVIDIA APIs for embeddings, we use **sentence-transformers** running locally
> - Models like `sentence-transformers/all-MiniLM-L6-v2` or `law-ai/InLegalBERT` are downloaded once and used offline
> - The vector database (ChromaDB) stays on your server — your case data never leaves

**[SCREEN: Docker Compose showing all services]**

> **Complete Offline Stack:**
> - **Backend:** Django API + PostgreSQL + Redis (all on-premise)
> - **LLM:** Ollama serving Llama 3 / Mistral (GPU required, or CPU for smaller models)
> - **Embeddings:** Local sentence-transformers
> - **Vector Store:** ChromaDB (local filesystem)
> - **Frontend:** Static React build served via Nginx

> This is a complete Docker Compose deployment — one command brings up the entire system, with zero external API calls.

**[SCREEN: Quick command]**

```bash
# Government server deployment
docker-compose up -d  # Starts Django, PostgreSQL, Redis, Ollama, ChromaDB
```

> NyayaDrishti gives you the power of AI-assisted legal analysis — while keeping all sensitive case data within your secure network. That's trustworthy AI for the government.

---

## PRODUCTION NOTES

| Section | Time | Screen |
|---|---|---|
| Problem | 0:00–0:40 | Title card → raw judgment PDF close-up |
| Upload & Extraction | 0:40–1:45 | Upload → Case Overview: Case Details + Executive Brief |
| Human Verification | 1:45–2:45 | Verify Actions: PDF + directive side-by-side, highlight in action |
| RAG Precedents | 2:45–3:30 | Similar Cases table on Case Overview |
| AI Recommendation | 3:30–4:15 | AI Verdict card with reasoning expanded |
| Dashboard | 4:15–4:50 | Case list with verified statuses + risk indicators |
| Close | 4:50–5:00 | Summary slide |

> [!TIP]
> **The "source highlight" moment (Section 3)** — clicking a directive and watching the PDF scroll and highlight — is your strongest visual. Slow down here. Let the viewer absorb what just happened. Consider a 2-second pause after the highlight appears before continuing narration.
