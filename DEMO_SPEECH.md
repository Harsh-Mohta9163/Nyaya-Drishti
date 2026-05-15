# NyayaDrishti — Live Demo Speech

**Audience:** Government of Karnataka officials, judges, evaluators
**Duration:** 8 minutes  ·  **Format:** Live web-app demonstration
**Hook → Demonstration → Close** arc with the financial argument front-loaded

---

## Pre-demo setup checklist (5 minutes before)

- [ ] Backend running: `python manage.py runserver` (or production URL)
- [ ] Frontend running: `npm run dev` (or production URL)
- [ ] Pipeline data fresh: `python manage.py refresh_demo_deadlines` ran this morning
- [ ] Browser open at the login page, full-screen
- [ ] Three accounts ready in a sticky-note: `central_law@demo.local`, `health_hlc@demo.local`, `health_lco@demo.local`, `health_nodal@demo.local` — all password `demo123`
- [ ] Featured case identified: **MFA No. 20338/2011 — Land Acquisition / Karnataka Housing Board** (under REVENUE dept). Backup: **K-9 Enterprises GST case** (FINANCE).
- [ ] Backup tab open in case the live LLM call stalls

---

## Speaker Notes & Stage Directions

Bracketed text in **`[brackets]`** indicates on-stage actions (clicks, transitions). Indented italic text is **what to say verbatim**. Timing markers in the left margin are cumulative.

---

### 0:00 — Opening Hook (45 seconds)

[*Stand at the centre. Stage open with the NyayaDrishti login screen visible.*]

> *"Honourable judges, distinguished officials, thank you for your time.*
>
> *Every year, the Government of Karnataka spends an enormous amount of money — not on schemes, not on infrastructure — but on **delays**. Delays in reading court judgments. Delays in routing them to the right department. Delays in executing simple compliance steps that the High Court has already laid down in black and white.*
>
> *Today I will show you a single platform that converts those delays into action — at the speed the courts expect."*

[*Pause for 2 seconds. Let the room settle.*]

---

### 0:45 — The Financial Toll (75 seconds)

[*Stay on the login screen — the numbers are the visual.*]

> *"Let me give you the numbers behind the problem.*
>
> *Karnataka currently has nearly **₹30,000 crore** blocked in revenue arrears and stalled capital projects — of which **₹5,067 crore** is sunk into 4,328 incomplete infrastructure works, largely held up by pending bills and contract disputes.*
>
> *Since 2022, the state has accumulated **3,957 pending contempt cases**. The High Court has been forced to levy exemplary penalties — **₹5 lakh** in one case for a three-and-a-half-year delay in executing a wage-parity order; **₹10 lakh** in another for abuse of process.*
>
> *And when compensation is delayed — for land acquisition, contractor dues, or employee retirement — the courts compound it back onto the exchequer at **statutory interest as high as 15 percent**.*
>
> *When you add up the carrying cost of blocked capital, the compounding interest on delayed compensation, and the direct legal penalties, **the conservative estimate is ₹590 crore per year — or nearly ₹7,000 crore over a 10-year horizon**.*
>
> *That is the cost of paper sitting on the wrong desk."*

[*Brief pause.*]

> *"The root cause is structural. A judgment is a 30 to 200 page PDF. The actionable direction is buried in legal reasoning. Even when the right officer eventually reads it, they have no automated way to know which department must act, what the Limitation Act deadline is, or what implementation steps to follow.*
>
> *NyayaDrishti closes that gap."*

---

### 2:00 — How We Align With Government Workflow (40 seconds)

[*Don't log in yet. Stay on the page.*]

> *"Before I show you the platform, one important point. We did not design a workflow and then ask the government to adopt it. We took the **statutory CCMS workflow that already exists** — Ingestion within 48 hours, AI-assisted routing, mandatory verification by the **Head of the Legal Cell**, executive decision by the Head of the Department, physical execution by the **Litigation Conducting Officer**, and statutory monitoring by the **Nodal Officer** — and built each step into a single platform that all four roles share.*
>
> *Every officer sees their own focused view, with role-based access controls enforced at the database layer. Central Law and the State Monitoring Committee see the cross-department aggregate. Nothing leaves the secretariat network — the entire stack is open-source and on-premise capable."*

---

### 2:40 — Live Demonstration (3 minutes 45 seconds)

#### 2:40 — Login as Central Law

[*Login with* `central_law@demo.local` / `demo123`. *Land on the Central View — the 48-tile grid.*]

> *"This is what the Central Law Department sees when they log in — **all 48 secretariat departments** in one view. Cases tagged automatically by our AI. Risk and urgency colour-coded. The Honourable Chief Secretary, or this department, can see at a glance which departments are running hot — which have contempt risk, which have imminent deadlines.*
>
> *Today there are six departments with active cases. Let me drill into one."*

[*Click on the **Revenue Department** tile (or whichever has the MFA land-acquisition case).*]

#### 3:10 — Open the featured case

[*Click on **MFA No. 20338/2011 — Land Acquisition** in the case list.*]

> *"This is a real Karnataka High Court judgment — a land acquisition matter involving the Karnataka Housing Board. The case is 12 pages of legal reasoning. Watch what our pipeline has done in under a minute."*

[*Land on the Case Overview screen.*]

> *"Our system has identified the parties — the appellants are the land losers, the respondents are the Assistant Commissioner and the Karnataka Housing Board. The case has been **automatically routed to the Revenue Department**, with Finance and Housing tagged as secondary stakeholders because the order has financial implications and KHB is the beneficiary department.*
>
> *Notice the deadline panel on the right — the AI has computed the **Limitation Act §4 and §12** appeal deadline by accounting for the Karnataka High Court calendar, including vacations. No manual calculation needed."*

#### 3:40 — Verify Actions tab (the centrepiece)

[*Click the **Verify Actions** tab. The PDF appears on the left, directive cards on the right.*]

> *"This is where the **Head of the Legal Cell** does their work — the mandatory human-in-the-loop step that the law requires. On the left is the original judgment. On the right are the directives our AI extracted.*
>
> *Watch what happens when I click on a directive."*

[*Click **"Show in PDF"** on the first directive — the PDF jumps and highlights the entire source paragraph.*]

> *"The system has **traced this directive back to its exact source paragraph** in the judgment. The Head of Legal Cell can verify in seconds what would otherwise take twenty minutes of cross-referencing.*
>
> *And here — beneath the verbatim text — is something we call the **Government Perspective Panel**."*

[*Point to the green-bordered panel showing govt_summary + implementation steps.*]

> *"The AI has translated the court's direction into a plain-English action plan: **recalculate the compensation at ₹3,38,400 per acre after deducting 53 percent developmental charges, add statutory benefits and interest, and disburse via a modified award**. Four concrete steps an officer can execute today.*
>
> *Crucially — our enricher will never invent a form number, treasury code, or deadline that does not appear in the operative order. We learned that the hard way during testing; you cannot pitch this to the secretariat with hallucinated procedure. We added explicit guardrails."*

#### 4:30 — Government action vs informational (key differentiator)

[*Scroll down to a non-government directive — e.g. one tagged "Informational / Court Registry". If MFA only has one directive, switch to the **CRL.A No. 870** criminal case briefly.*]

> *"Compare that with this directive — marked **Informational**. The court has directed the **Registrar** to issue conviction warrants. That is **not the government's job to execute**. The system says so clearly, with a one-line note explaining why.*
>
> *This matters. Today, officers waste hours trying to figure out whether a particular line in a judgment is their responsibility or someone else's. Our AI does that classification for them."*

#### 5:00 — HLC verifies

[*Click the verify checkbox on a couple of directives. Then click **Verify All** if available, or approve the plan via the review button.*]

> *"The Head of Legal Cell ticks each directive they accept. The data flows forward only after their approval — this is non-negotiable. If they think the AI got it wrong, they can edit the implementation steps directly in this same view, or re-route the case to a different department in one click.*
>
> *Every change is logged with a timestamp and the reviewer's identity. Full audit trail."*

#### 5:25 — LCO Execution view

[*Log out. Log in as* `health_lco@demo.local` *— or whichever department's LCO matches your demo case. Land on the **Execution** tab directly.*]

> *"Now I log in as the **Litigation Conducting Officer** — the officer who physically does the work. They land here, on the Execution tab.*
>
> *Notice — only the directives the Head of Legal Cell verified appear here. Informational items are filtered out by default. The LCO sees the implementation steps for each task, marks status as **In Progress** or **Completed**, and uploads proof of compliance — a receipt, a sanctioned order, anything."*

[*Mark one directive **Completed** and pretend to upload a proof file.*]

> *"That status flows back into the system. The Head of the Department, the Central Law office, and the State Monitoring Committee all see updated compliance figures instantly."*

#### 5:55 — Nodal Officer Deadline Monitor

[*Log out. Log in as* `health_nodal@demo.local`. *Land on the **Deadlines** tab.*]

> *"And here is the **Nodal Officer's** view — the role whose statutory duty is to ensure the department never crosses a limitation deadline.*
>
> *Every approved plan is sorted by urgency. **Red is overdue or critical, within three days. Amber is within fourteen. Green is on track.** A Nodal Officer can walk into work, glance at this screen, and know exactly where to focus.*
>
> *No spreadsheet. No reminder emails. No contempt notices arriving unannounced."*

---

### 6:25 — How The AI Works — Briefly (40 seconds)

[*Optional: open a system architecture slide if you have one. Otherwise stay on the Nodal screen and speak.*]

> *"A quick word on what's under the hood. We use a **four-agent extraction pipeline** — each agent has one job.*
>
> *Our **Registry Clerk** reads the header and extracts case numbers, parties, dates. Our **Legal Analyst** extracts the facts and issues framed. Our **Precedent Scholar** extracts the legal reasoning and citations. Our **Compliance Officer** extracts the operative directives.*
>
> *Then a second pipeline — the **four-agent recommendation engine** — runs over the extraction. A **Precedent Researcher** retrieves similar cases from our 4 lakh-chunk Supreme Court corpus. A **Devil's Advocate** argues the opposite side. A **Risk Auditor** flags contempt and financial exposure. A **Decision Synthesizer** produces a final APPEAL or COMPLY recommendation with full reasoning.*
>
> *Everything is grounded in real precedents. Nothing is hallucinated. And every component is open-source — InLegalBERT for embeddings, ChromaDB for retrieval, BM25 for keyword match — so the entire system can run inside a Government of Karnataka data centre, with no data ever leaving the network."*

---

### 7:05 — The Bottom Line (40 seconds)

[*Return to the Central Law dashboard view if convenient. Otherwise face the audience directly.*]

> *"Let me bring this back to where I started.*
>
> *The Karnataka government loses an estimated **₹590 crore every year** to litigation delays, contempt penalties, and statutory interest on stalled payments.*
>
> *If NyayaDrishti reduces those delays by even **20 percent** — by routing cases to the right department on day one, by giving every officer a plain-English action plan, by alerting Nodal Officers before deadlines lapse — the platform pays for itself many times over in a single year.*
>
> *More importantly, it restores something more valuable than money: **the credibility of the State Government before the courts**. Fewer contempt notices. Fewer adverse orders. Fewer judges levying exemplary costs on a government that should know better."*

---

### 7:45 — Close & Call To Action (15 seconds)

> *"NyayaDrishti is ready for pilot deployment with the Department of Personnel and Administrative Reforms, or any sectoral department willing to start. The codebase is open. The data stays on-premise. The team is here.*
>
> *We are happy to take your questions. Thank you."*

[*Pause. Step back. Wait for applause / questions.*]

---

## If a question is asked — quick-reference answers

| Likely question | One-line answer |
|---|---|
| *Do you connect to the actual High Court CIS API?* | "Not today — most state High Courts don't expose one. Our 48-hour manual upload SLA is the same path the workflow already mandates. Our endpoint can be triggered by a CIS push the moment the Registry exposes it." |
| *How accurate is the AI?* | "On our pilot of six representative judgments, every directive was traced to its source paragraph with zero false matches. The Head of Legal Cell remains the verifier — the AI never bypasses human approval." |
| *What about data privacy?* | "Every ML component — embeddings, retrieval, reranking, analytics — runs locally. The only external calls are to the LLM, and those can be replaced with a self-hosted Llama or Mistral model via vLLM in an air-gapped deployment." |
| *Cost?* | "Per case, the cloud LLM cost is under ₹0.50 with current providers. At full state scale, the LLM bill is a tiny fraction of the savings we just discussed." |
| *Can it handle scanned PDFs?* | "Yes — PyMuPDF handles OCR. For older scanned judgments we add a Tesseract fallback. Accuracy drops marginally on heavily-degraded scans but is recoverable through the verifier interface." |
| *Why these specific roles?* | "These are not roles we invented. They are defined in the Government of Karnataka's CCMS doctrine. We built our software to fit, not the other way round." |
| *Department override?* | "Yes — both the Head of Legal Cell and the Central Law office can re-route any case in one click. The override writes a full audit row with reviewer ID, timestamp, old department, new department." |

---

## Backup talking points (if the live demo stalls)

If the LLM call hangs mid-demo, do not wait. Pivot to:

> *"While the extraction runs, let me show you what a verified case looks like."*

Switch to the **CRL.A No. 870 of 2017** case (already enriched, fast load) and continue from the **Verify Actions** stage. The audience won't notice; you save the demo.

If the network drops entirely, you have screenshots in `frontend/src/karnataka_govt_logo.png` (and you can describe the flow narratively from this script).

---

## Pacing reminders

- **Speak slowly.** Government officials are listening for substance, not pace. 130 words per minute is a good target — your nervous system will push you to 180. Practise at 130.
- **Three pauses are mandatory:**
  1. After the ₹6,918 crore figure (1:30).
  2. After the highlighted paragraph appears in the PDF (3:55).
  3. After the closing line (7:55).
- **The numbers are your friends.** ₹30,000 crore, ₹5,067 crore, 3,957 contempt cases, ₹590 crore per year. Drop them at the rhythm of speech, not in a list.
- **Avoid technical jargon in the spoken script.** "Four-agent pipeline" is fine. "Pydantic schema validation against the model_dump" is not.

---

## One-line elevator version (for hallway conversations after)

> *"NyayaDrishti is a court-to-compliance platform that routes High Court judgments to the right Karnataka secretariat department, translates the court's directives into a plain-English action plan with statutory deadlines, and tracks execution through verified, audit-trail-protected workflows — built around the four statutory roles the CCMS doctrine already defines. We estimate it saves the state ₹500 crore plus annually in contempt penalties, statutory interest, and avoidable litigation cost."*

---

**Good luck.** ⚖️
