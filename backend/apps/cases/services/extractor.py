import json
import logging
import time
import requests
from typing import Optional
from pydantic import BaseModel, Field

from django.conf import settings
from apps.cases.models import Case, Judgment, Citation

logger = logging.getLogger(__name__)

# ==============================================================================
# Pydantic Schemas for Structured Output (4-Agent Pipeline)
# ==============================================================================

# Agent 1: Registry Clerk (8B)
class RegistryExtraction(BaseModel):
    case_number: str = Field(description="e.g., WA 541/2026 or WP No. 98 of 2024")
    court_name: str = Field(description="e.g., High Court of Karnataka")
    bench: str = Field(description="'Single Judge' or 'Division Bench'")
    presiding_judges: list[str] = Field(description="List of judge full names")
    case_type: str = Field(description="Exact case type abbreviation: 'Writ Petition', 'Writ Appeal', etc.")
    document_type: str = Field(description="'Final Judgment', 'Interim Order', 'Notice', 'Stay Order'")
    date_of_order: str = Field(description="Date in ISO format YYYY-MM-DD.")
    petitioner_name: str = Field(description="Full name(s) of petitioner(s)")
    respondent_name: str = Field(description="Full name(s) of respondent(s)")
    appeal_type: str = Field(description="'writ_petition', 'writ_appeal', 'regular_first_appeal', 'criminal_appeal', 'other'. Use 'none' if original.")
    # Appeal lineage
    is_appeal_from_lower_court: bool = Field(description="True if this is an appeal/revision from a lower court.")
    lower_court_name: Optional[str] = Field(description="Name of lower court whose order is challenged.", default=None)
    lower_court_case_number: Optional[str] = Field(description="Case number in the lower court.", default=None)
    lower_court_decision: Optional[str] = Field(description="What the lower court decided.", default=None)

# Agent 2: Legal Analyst (70B)
class AnalystExtraction(BaseModel):
    summary_of_facts: str = Field(description="Display-ready factual summary in 3-5 complete sentences.")
    issues_framed: list[str] = Field(description="List of legal questions the court addresses. Complete sentences.")

# Agent 3: Precedent Scholar (70B)
class CitationExtraction(BaseModel):
    case_name: str = Field(description="Full case name as cited. e.g., 'X vs. Y'")
    citation_ref: str = Field(description="Citation reference if available. e.g., '(2010) 5 SCC 186'")
    context: str = Field(description="How the court used this case: 'relied_upon', 'distinguished', 'overruled', 'referred'.")
    principle_extracted: Optional[str] = Field(description="The legal principle for which this case was cited.", default=None)

class ScholarExtraction(BaseModel):
    ratio_decidendi: str = Field(description="The court's legal reasoning and analysis in 2-4 complete sentences.")
    area_of_law: str = Field(description="Primary legal domain: e.g., 'Service Law', 'Motor Vehicles', 'Criminal'. NEVER empty.")
    primary_statute: str = Field(description="The MAIN Act/statute the case is about. e.g., 'Motor Vehicles Act 1988'. NEVER empty.")
    citations: list[CitationExtraction] = Field(description="ALL case citations mentioned in the body with their context.")
    entities: list[str] = Field(description="All named entities: government departments, officials, Acts mentioned.")

# Agent 4: Compliance Officer (70B — most critical agent)
class DirectiveExtraction(BaseModel):
    text: str = Field(description="The COMPLETE verbatim paragraph(s) of the operative ORDER ITSELF — the court's actual command/direction. Do NOT include legal reasoning or citations that precede the order. Include ALL details: amounts, percentages, calculations, conditions.")
    responsible_entity: str = Field(description="The specific department/party/court who must carry out this directive.")
    action_required: str = Field(description="Clear 1-2 sentence summary of the compliance action for a government officer. Include specific amounts and deadlines.")
    deadline_mentioned: Optional[str] = Field(description="Exact phrase describing deadline, e.g. 'within 8 weeks'", default=None)
    financial_details: Optional[str] = Field(description="Specific monetary amounts, calculations, percentages mentioned in this directive.", default=None)

class ComplianceExtraction(BaseModel):
    disposition: str = Field(description="Outcome word: 'Allowed', 'Dismissed', 'Partly Allowed', 'Disposed of', 'Remanded'.")
    winning_party_type: str = Field(description="Who won: 'Petitioner/Appellant', 'Respondent', 'None'.")
    operative_order_summary: str = Field(description="Complete summary of the operative order in 3-5 sentences, covering ALL directives, amounts, and conditions.")
    court_directions: list[DirectiveExtraction] = Field(description="List of ACTIONABLE compliance directives with FULL paragraph context.")
    financial_implications: list[str] = Field(description="ALL monetary orders: exact amounts, costs, interest, deposits, deductions.")
    contempt_indicators: list[str] = Field(description="Phrases suggesting contempt risk: compliance warnings, personal appearance.")
    contempt_risk: str = Field(description="'High', 'Medium', or 'Low' risk.")
    entities: list[str] = Field(description="Additional named entities in the operative order (departments, officials).")

# ==============================================================================
# LLM Provider Abstraction
# ==============================================================================

def _salvage_json(content: str) -> dict:
    """Try hard to recover a JSON object from a noisy model response.

    Llama 70B occasionally wraps the JSON in markdown fences, adds an
    explanation paragraph before/after, or truncates mid-key on long inputs.
    We pull the first balanced { ... } substring and try to parse it.
    """
    if not content:
        return {}
    s = content.strip()
    if s.startswith("```"):
        s = s.strip("`")
        if s.startswith("json"):
            s = s[4:].strip()
    # Find first balanced brace
    start = s.find("{")
    if start == -1:
        return {}
    depth = 0
    end = -1
    for i, ch in enumerate(s[start:], start=start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end == -1:
        # Truncated — try appending closing braces to balance
        candidate = s[start:] + ("}" * abs(depth) if depth > 0 else "")
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            return {}
    try:
        return json.loads(s[start:end])
    except json.JSONDecodeError:
        return {}


def _call_agent_70b(prompt: str, schema: type[BaseModel], temperature: float) -> dict:
    """Agent 2 & 3: Calls NVIDIA 70B for heavy reasoning."""
    api_key = settings.NVIDIA_API_KEY
    base_url = settings.NVIDIA_BASE_URL.rstrip("/")
    model = "meta/llama-3.3-70b-instruct"

    schema_json = json.dumps(schema.model_json_schema(), indent=2)
    full_prompt = f"{prompt}\n\nRespond ONLY with valid JSON matching this schema:\n{schema_json}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": full_prompt}],
        "temperature": temperature,
        "max_tokens": 8192,
        "response_format": {"type": "json_object"},
    }

    last_error = None
    for attempt in range(5):
        try:
            print(f"  [NVIDIA 70B] Calling {model} (attempt {attempt+1}/5)...")
            resp = requests.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=180,
            )
            if resp.status_code in (429, 503):
                wait = 30 * (attempt + 1)
                print(f"  [NVIDIA 70B] Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            if resp.status_code == 413 or resp.status_code == 400:
                # Payload too large or bad request — likely context overflow.
                # Truncate the prompt aggressively and retry once.
                if attempt == 0 and len(full_prompt) > 30000:
                    truncated = full_prompt[:30000] + "\n\n[...truncated due to context limit...]\n\nRespond ONLY with valid JSON matching the schema above."
                    payload["messages"][0]["content"] = truncated
                    print(f"  [NVIDIA 70B] {resp.status_code} on {len(full_prompt)}-char prompt; retrying with 30k-char truncation")
                    continue
                # Give up gracefully — return empty dict so caller can use defaults
                print(f"  [NVIDIA 70B] {resp.status_code} on retry; returning empty extraction (downstream fields will use defaults)")
                return {}
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Salvage the JSON if the model added preamble or truncated mid-stream.
                recovered = _salvage_json(content)
                if recovered:
                    print(f"  [NVIDIA 70B] Salvaged JSON from noisy response ({len(content)} chars)")
                    return recovered
                print(f"  [NVIDIA 70B] Could not parse JSON; first 200 chars: {content[:200]!r}")
                last_error = ValueError("Malformed JSON from 70B")
                time.sleep(10)
                continue
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response else 0
            last_error = e
            if status in (429, 503):
                wait = 30 * (attempt + 1)
                time.sleep(wait)
            else:
                raise
        except Exception as e:
            last_error = e
            print(f"  [NVIDIA 70B] Unexpected error: {e}")
            time.sleep(10)
    # All retries exhausted — don't blow up the whole pipeline.
    # Returning {} lets downstream fill with defaults so the user still gets a Case.
    print(f"  [NVIDIA 70B] All 5 attempts failed (last: {last_error}); returning empty extraction")
    return {}


def _call_agent_8b(prompt: str, schema: type[BaseModel], temperature: float) -> dict:
    """Agent 1 & 4: Calls OpenRouter Llama 3.1 8B for fast extraction, falls back to NVIDIA 70B.

    Replaces the older Groq-hosted 8B path — OpenRouter has been more reliable
    (no aggressive per-minute rate limits, larger context, same generation
    model) and is cheap enough for routine extraction.
    """
    import os as _os
    api_key = getattr(settings, "OPENROUTER_API_KEY", "") or _os.environ.get("OPENROUTER_API_KEY", "")
    base_url = getattr(settings, "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
    model = "meta-llama/llama-3.1-8b-instruct"

    schema_json = json.dumps(schema.model_json_schema(), indent=2)
    full_prompt = f"{prompt}\n\nRespond ONLY with valid JSON matching this schema:\n{schema_json}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://nyaya-drishti.onrender.com/",
        "X-Title": "NyayaDrishti CCMS",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": full_prompt}],
        "temperature": temperature,
        "max_tokens": 2048,
        "response_format": {"type": "json_object"},
    }

    if not api_key:
        print(f"  [OR-8B] OPENROUTER_API_KEY not set; falling straight through to NVIDIA 70B")
        last_error = RuntimeError("OPENROUTER_API_KEY missing")
    else:
        last_error = None
        for attempt in range(3):
            try:
                print(f"  [OR-8B] Calling {model} (attempt {attempt+1}/3)...")
                resp = requests.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=90,
                )
                if resp.status_code in (429, 503):
                    wait = 15 * (attempt + 1)
                    print(f"  [OR-8B] Rate limited (HTTP {resp.status_code}), waiting {wait}s...")
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"]
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    recovered = _salvage_json(content)
                    if recovered:
                        return recovered
                    last_error = ValueError(f"Malformed JSON; first 200 chars: {content[:200]!r}")
                    continue
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response else 0
                print(f"  [OR-8B] HTTP error {status_code}: {e}")
                last_error = e
                if status_code in (429, 503):
                    time.sleep(15 * (attempt + 1))
                else:
                    break
            except Exception as e:
                print(f"  [OR-8B] Error: {e}")
                last_error = e
                time.sleep(5)

    # Fallback: use NVIDIA 70B instead of failing completely
    print(f"  [OR-8B] Falling back to NVIDIA 70B ({last_error})...")
    nvidia_key = settings.NVIDIA_API_KEY
    nvidia_url = settings.NVIDIA_BASE_URL.rstrip("/")
    nvidia_payload = {
        "model": "meta/llama-3.3-70b-instruct",
        "messages": [{"role": "user", "content": full_prompt}],
        "temperature": temperature,
        "max_tokens": 2048,
        "response_format": {"type": "json_object"},
    }
    nvidia_headers = {
        "Authorization": f"Bearer {nvidia_key}",
        "Content-Type": "application/json",
    }
    # Big PDFs blow past 8B context — retry the NVIDIA fallback with a truncated prompt
    # if the original was too large.
    for attempt in range(2):
        try:
            if attempt == 1 and len(full_prompt) > 30000:
                truncated = full_prompt[:30000] + "\n\n[...truncated...]\n\nRespond ONLY with valid JSON matching the schema."
                nvidia_payload["messages"][0]["content"] = truncated
                print(f"  [NVIDIA 70B Fallback] Retry with 30k-char truncation")
            print(f"  [NVIDIA 70B Fallback] Calling meta/llama-3.3-70b-instruct (attempt {attempt+1}/2)...")
            resp = requests.post(
                f"{nvidia_url}/chat/completions",
                headers=nvidia_headers,
                json=nvidia_payload,
                timeout=180,
            )
            if resp.status_code in (400, 413):
                # context overflow — fall through to truncation retry
                if attempt == 0:
                    continue
                print(f"  [NVIDIA 70B Fallback] {resp.status_code} on retry; returning empty extraction")
                return {}
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                recovered = _salvage_json(content)
                if recovered:
                    return recovered
                print(f"  [NVIDIA 70B Fallback] Could not parse JSON; returning empty")
                return {}
        except Exception as e:
            last_error = e
            if attempt == 1:
                # Final attempt — return empty rather than crashing the whole pipeline.
                print(f"  [NVIDIA 70B Fallback] Both Groq and NVIDIA failed: {e}; returning empty extraction")
                return {}
            time.sleep(5)
    return {}


def _sanitize_disposition(val: str) -> str:
    if not val or val.strip().lower() in ("none", "null", "n/a", ""):
        return ""
    return val.strip()

def _sanitize_party_type(val) -> str:
    if isinstance(val, list):
        val = ", ".join(str(v) for v in val)
    if not val or str(val).strip().lower() in ("none", "null", "n/a", ""):
        return ""
    return str(val).strip()

def _safe_str(val, max_len: int | None = None) -> str:
    """Coerce an LLM-returned value to a string and (optionally) truncate.

    The LLM occasionally returns a list, dict, or a verbose schema-fragment in
    a field we expect to be a short string (e.g. case_type). When written to a
    Postgres CharField with a max_length, that overflow raises
    DataError: value too long for type character varying(N). Pass max_len to
    clip safely before save.
    """
    if isinstance(val, list):
        out = ", ".join(str(v) for v in val if v)
    elif isinstance(val, dict):
        # LLM sometimes nests a dict where a string was expected — flatten to
        # a comma-joined "k=v" so we keep readable signal without crashing.
        out = ", ".join(f"{k}={v}" for k, v in val.items() if v) or ""
    elif val is None:
        out = ""
    else:
        out = str(val).strip()
    if max_len and len(out) > max_len:
        out = out[: max_len - 1].rstrip()
    return out

# ==============================================================================
# Extraction Service (4 Agents)
# ==============================================================================

def _call_openrouter_llama(prompt: str, schema: type[BaseModel], temperature: float) -> dict:
    """Route large-PDF agent calls to OpenRouter's Llama 3.3 70B Instruct.

    Groq 8B 413s on long inputs and NVIDIA NIM read-times-out at 180s on the
    same prompts. OpenRouter serves the same `meta-llama/llama-3.3-70b-instruct`
    model on a more reliable infrastructure and accepts much larger payloads.
    """
    api_key = getattr(settings, "OPENROUTER_API_KEY", "") or os.environ.get("OPENROUTER_API_KEY", "")
    base_url = getattr(settings, "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    if not api_key:
        print(f"  [OpenRouter] OPENROUTER_API_KEY not set — cannot route large PDF; falling back to NVIDIA 70B")
        return _call_agent_70b(prompt, schema, temperature)

    model = "meta-llama/llama-3.3-70b-instruct"
    schema_json = json.dumps(schema.model_json_schema(), indent=2)
    full_prompt = f"{prompt}\n\nRespond ONLY with valid JSON matching this schema:\n{schema_json}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        # OpenRouter recommends these for ranking / quota attribution.
        "HTTP-Referer": "https://nyaya-drishti.onrender.com/",
        "X-Title": "NyayaDrishti CCMS",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": full_prompt}],
        "temperature": temperature,
        "max_tokens": 4096,
        "response_format": {"type": "json_object"},
    }

    last_error = None
    for attempt in range(3):
        try:
            print(f"  [OpenRouter Llama-70B] Calling {model} (attempt {attempt+1}/3, prompt {len(full_prompt)} chars)...")
            resp = requests.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload,
                timeout=300,
            )
            if resp.status_code in (429, 503):
                wait = 20 * (attempt + 1)
                print(f"  [OpenRouter] Rate limited ({resp.status_code}); waiting {wait}s...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                recovered = _salvage_json(content)
                if recovered:
                    print(f"  [OpenRouter] Salvaged JSON from noisy response")
                    return recovered
                last_error = ValueError(f"Malformed JSON; first 200 chars: {content[:200]!r}")
                continue
        except Exception as e:
            last_error = e
            print(f"  [OpenRouter] Attempt {attempt+1} failed: {e}")
            time.sleep(10)

    print(f"  [OpenRouter] All retries failed ({last_error}); falling back to NVIDIA 70B")
    return _call_agent_70b(prompt, schema, temperature)


def extract_structured_data(
    judgment_id: str,
    header_text: str,
    middle_text: str,
    operative_text: str,
    page_count: int = 0,
) -> dict:
    judgment = Judgment.objects.get(id=judgment_id)
    case = judgment.case
    extracted_data = {}

    # Large-PDF routing: anything >= OPENROUTER_LARGE_PDF_THRESHOLD pages
    # (default 25) goes through OpenRouter Llama 70B for ALL 4 agents. Small
    # PDFs use OpenRouter Llama 8B for Agents 1 & 4 and NVIDIA NIM 70B for
    # Agents 2 & 3.
    large_threshold = getattr(settings, "OPENROUTER_LARGE_PDF_THRESHOLD", 25)
    use_openrouter = page_count >= large_threshold
    if use_openrouter:
        print(f"  [Extractor] PDF has {page_count} pages (>= {large_threshold}); routing all agents via OpenRouter Llama 3.3 70B")
        agent_8b_call = _call_openrouter_llama
        agent_70b_call = _call_openrouter_llama
    else:
        if page_count:
            print(f"  [Extractor] PDF has {page_count} pages (< {large_threshold}); using OpenRouter Llama 8B + NVIDIA 70B path")
        agent_8b_call = _call_agent_8b
        agent_70b_call = _call_agent_70b

    # --- AGENT 1: Registry Clerk ---
    if header_text:
        print(f"  [Agent 1] Registry Clerk (Header)...")
        header_prompt = (
            "Extract metadata from the header of an Indian High Court judgment PDF.\n"
            "Extract every field exactly as it appears. Pay attention to case number, date, judges, and parties.\n"
            f"Document:\n{header_text}"
        )
        extracted_data["registry"] = agent_8b_call(header_prompt, RegistryExtraction, temperature=0.0)

    # --- AGENT 4: Compliance Officer (70B — most critical for Theme 11) ---
    if operative_text:
        print(f"  [Agent 4] Compliance Officer (70B — Operative Order)...")
        operative_prompt = (
            "You are a senior compliance officer for a government department. "
            "Extract the COMPLETE operative order from this Indian court judgment.\n\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. Extract ALL OPERATIVE ORDERS — not just enforcement/compliance actions. This includes EVERY category:\n"
            "   a) Sentencing / conviction orders (life imprisonment, rigorous imprisonment, fines, default sentences)\n"
            "   b) Acquittal orders (e.g., 'appeal against acquittal dismissed', acquittal upheld)\n"
            "   c) Orders for absconding accused (e.g., 'to be heard separately when produced')\n"
            "   d) Set-off / remission rights (e.g., 'entitled to set-off for period already spent in jail')\n"
            "   e) Conviction warrant directions (e.g., 'Registrar to issue conviction warrants forthwith')\n"
            "   f) Compensation orders — including WHO receives the money (e.g., 'widow of deceased')\n"
            "   g) Procedural orders (supply of copies, printing of judgment, free copies to accused)\n"
            "   h) Welfare / medical care orders (e.g., 'Jail Superintendent to monitor health of accused')\n"
            "   i) Costs / interest / penalty orders\n"
            "   j) Any other direction by the court\n"
            "2. For each court direction, the 'text' field must contain ONLY the verbatim text of the OPERATIVE ORDER ITSELF.\n"
            "   Do NOT include legal reasoning, citations, or analysis paragraphs that precede the order.\n"
            "   The text should start with the actual direction/command of the court.\n"
            "3. Capture the FULL PARAGRAPH for each direction — do NOT extract isolated sentences.\n"
            "   A government officer reading your extraction must understand the COMPLETE order without referring back to the judgment.\n"
            "4. Include ALL financial details: exact rupee amounts, percentages, base values, calculation methods, deductions.\n"
            "5. The 'action_required' field should read like a clear compliance instruction, e.g.:\n"
            "   BAD: 'Pay market value to appellants'\n"
            "   GOOD: 'Pay enhanced compensation of ₹3,38,400/- per acre to appellants (base value ₹7,20,000 per acre minus 53% developmental charges under HUDCO scheme), plus statutory benefits and interest under Sections 23(1A), 23(2), and 28 of the Land Acquisition Act.'\n"
            "6. For 'operative_order_summary': Write a complete 3-5 sentence summary that a government secretary can read to understand the ENTIRE order — including procedural directions, not just the headline sentence/fine.\n"
            "7. You MUST extract at least one directive for each distinct court order. If there are 8 separate orders, there must be 8 directives.\n\n"
            "RESPONSIBLE ENTITY RULES:\n"
            "- If the court itself must act (e.g. 'conviction warrants to be issued', 'copies to be supplied'), responsible_entity = 'Reference Court' or 'Registrar (Judicial)' or the specific court/tribunal.\n"
            "- If a jail authority must act (e.g. 'monitor health'), responsible_entity = 'Jail Superintendent' or the specific authority.\n"
            "- If a government department/officer must pay or act, identify the SPECIFIC entity.\n"
            "- If the order is about an accused's rights (e.g. set-off), responsible_entity = the specific accused.\n"
            "- Different directives may have DIFFERENT responsible entities.\n\n"
            f"Case Type: {case.case_type or 'Unknown'}\n"
            f"Petitioner/Appellant: {case.petitioner_name or 'Unknown'}\n"
            f"Respondent: {case.respondent_name or 'Unknown'}\n\n"
            f"OPERATIVE ORDER TEXT:\n{operative_text}"
        )
        # OpenRouter has no NIM rate-limit issues — skip the 15s sleep for the large-PDF path.
        if not use_openrouter:
            print(f"  [Sleep] Waiting 15s before 70B call for compliance...")
            time.sleep(15)
        extracted_data["compliance"] = agent_70b_call(operative_prompt, ComplianceExtraction, temperature=0.1)

    # --- AGENT 2: Legal Analyst ---
    if middle_text:
        print(f"  [Agent 2] Legal Analyst (Facts/Issues)...")
        analyst_prompt = (
            "Extract the factual summary and legal issues framed from the body of this judgment.\n"
            "Write in clear, professional prose.\n"
            f"Document:\n{middle_text}"
        )
        extracted_data["analyst"] = agent_70b_call(analyst_prompt, AnalystExtraction, temperature=0.2)

        if not use_openrouter:
            # NVIDIA's free tier rate-limits; OpenRouter doesn't.
            print(f"  [Sleep] Waiting 15s before next 70B call...")
            time.sleep(15)

    # --- AGENT 3: Precedent Scholar (70B) ---
    if middle_text:
        print(f"  [Agent 3] Precedent Scholar (Ratio/Citations)...")
        scholar_prompt = (
            "Extract the legal reasoning (ratio decidendi), area of law, primary statute, and ALL case citations.\n"
            "For citations, identify how the court used them (relied_upon, distinguished, overruled, referred).\n"
            f"Document:\n{middle_text}"
        )
        extracted_data["scholar"] = agent_70b_call(scholar_prompt, ScholarExtraction, temperature=0.1)

    # Save raw JSON backup
    judgment.raw_extracted_json = extracted_data

    # -----------------------------------------------------------------------
    # Populate DB Models
    # -----------------------------------------------------------------------

    # Registry (Agent 1)
    if "registry" in extracted_data:
        h = extracted_data["registry"]
        # Fix: LLM sometimes returns Pydantic schema wrapper
        if "$defs" in h or ("properties" in h and "type" in h):
            print("  [Extractor] Detected schema-wrapped registry response, unwrapping...")
            h = h.get("properties", h)
        judgment.presiding_judges = h.get("presiding_judges", [])
        
        raw_date = _safe_str(h.get("date_of_order", ""))
        if raw_date and raw_date not in ("", "YYYY-MM-DD", "Unknown"):
            from datetime import datetime as _dt
            parsed_date = None
            for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%B %d, %Y", "%d %B %Y"):
                try:
                    parsed_date = _dt.strptime(raw_date.strip(), fmt).date()
                    break
                except (ValueError, TypeError):
                    continue
            if parsed_date:
                judgment.date_of_order = parsed_date
            else:
                # Try to extract year at least
                import re
                year_match = re.search(r'(19|20)\d{2}', raw_date)
                if year_match:
                    judgment.date_of_order = f"{year_match.group()}-01-01"

        # Judgment.document_type is CharField(max_length=50); appeal_type is 30.
        doc_type = _safe_str(h.get("document_type", ""), max_len=50)
        if doc_type: judgment.document_type = doc_type

        appeal_type = _safe_str(h.get("appeal_type", "none"), max_len=30).lower()
        if appeal_type: judgment.appeal_type = appeal_type

        extracted_case_number = _safe_str(h.get("case_number", ""))
        # Dedup: only if case_number is non-trivial (>5 chars, not "Pending" placeholder).
        # We skip dedup entirely if the number is too short or matches the temp pattern,
        # to prevent unrelated PDFs from being merged into the same Case row.
        is_dedup_safe = (
            len(extracted_case_number) > 5
            and not extracted_case_number.lower().startswith("pending")
        )
        if is_dedup_safe:
            existing = Case.objects.filter(
                court_name=_safe_str(h.get("court_name", case.court_name)),
                case_number=extracted_case_number,
            ).exclude(id=case.id).first()

            if existing:
                old_case = case
                judgment.case = existing
                judgment.save()  # MUST save before deleting old_case to avoid cascade-delete
                case = existing
                old_case.delete()

        if extracted_case_number:
            # Case.case_number is CharField(max_length=255)
            case.case_number = _safe_str(extracted_case_number, max_len=255)

        # CharField max_length values mirror Case model field definitions —
        # any LLM-supplied string is clipped to fit Postgres column bounds.
        case.court_name = _safe_str(h.get("court_name", case.court_name), max_len=200)
        case.case_type = _safe_str(h.get("case_type", case.case_type), max_len=100)
        case.petitioner_name = _safe_str(h.get("petitioner_name", ""))  # TextField, no clip needed
        case.respondent_name = _safe_str(h.get("respondent_name", ""))  # TextField
        case.save()

    # Analyst (Agent 2)
    if "analyst" in extracted_data:
        a = extracted_data["analyst"]
        judgment.summary_of_facts = a.get("summary_of_facts", "")
        judgment.issues_framed = a.get("issues_framed", [])

    # Scholar (Agent 3)
    if "scholar" in extracted_data:
        s = extracted_data["scholar"]
        judgment.ratio_decidendi = s.get("ratio_decidendi", "")
        
        # Area of law & Statute are extracted by the Scholar (Agent 3)
        # Case.area_of_law is CharField(max_length=100); primary_statute is 300.
        case.area_of_law = _safe_str(s.get("area_of_law", ""), max_len=100)
        case.primary_statute = _safe_str(s.get("primary_statute", ""), max_len=300)
        case.save()

    # Compliance (Agent 4)
    if "compliance" in extracted_data:
        c = extracted_data["compliance"]
        # Fix: LLM sometimes returns Pydantic schema wrapper instead of raw data
        if "$defs" in c or ("properties" in c and "type" in c):
            print("  [Extractor] Detected schema-wrapped compliance response, unwrapping from 'properties'...")
            c = c.get("properties", c)
        judgment.court_directions = c.get("court_directions", [])
        # Judgment CharField clip lengths from models.py: disposition=30,
        # winning_party_type=30, contempt_risk=20. operative_order_text is
        # TextField so no clip needed.
        judgment.disposition = _safe_str(
            _sanitize_disposition(c.get("disposition", "")), max_len=30
        )
        judgment.winning_party_type = _safe_str(
            _sanitize_party_type(c.get("winning_party_type", "")), max_len=30
        )
        judgment.contempt_indicators = c.get("contempt_indicators", [])
        judgment.contempt_risk = _safe_str(c.get("contempt_risk", "Low"), max_len=20)
        judgment.financial_implications = c.get("financial_implications", [])
        judgment.operative_order_text = c.get("operative_order_summary", "")

    # Entities Merging
    entities = set()
    if "scholar" in extracted_data:
        entities.update(extracted_data["scholar"].get("entities", []))
    if "compliance" in extracted_data:
        entities.update(extracted_data["compliance"].get("entities", []))
    judgment.entities = list(entities)

    # Citations Save
    all_citations = []
    if "scholar" in extracted_data:
        all_citations = extracted_data["scholar"].get("citations", [])
    
    if all_citations:
        Citation.objects.filter(citing_judgment=judgment).delete()
        citation_objs = []
        for cit in all_citations:
            if isinstance(cit, dict):
                case_name = _safe_str(cit.get("case_name", ""))
                citation_ref = _safe_str(cit.get("citation_ref", ""))
                context = _safe_str(cit.get("context", "referred")).lower()
                principle = _safe_str(cit.get("principle_extracted", ""))
                valid_contexts = {"relied_upon": "Relied upon", "distinguished": "Distinguished",
                                  "overruled": "Overruled", "referred": "Referred"}
                context_display = valid_contexts.get(context, "Referred")

                if case_name:
                    citation_objs.append(Citation(
                        citing_judgment=judgment,
                        cited_case=None,
                        cited_case_name_raw=case_name,
                        citation_id_raw=citation_ref,
                        citation_context=context_display,
                        principle_extracted=principle,
                    ))
        Citation.objects.bulk_create(citation_objs)
        print(f"  [Extractor] Saved {len(citation_objs)} citation records.")

    # ─── Department classification ──────────────────────────────────────────
    # Maps the judgment to one of the 48 Karnataka secretariat departments
    # so dept-scoped users see this case in their queue. Verifier can override
    # later via PATCH /api/cases/<uuid>/department/.
    try:
        from apps.cases.services.dept_classifier import classify as classify_dept
        dept_haystack = (operative_text or "")[:6000] + "\n" + (middle_text or "")[:4000]
        dept_result = classify_dept(
            case_text=dept_haystack,
            entities=list(judgment.entities or []),
            parties=(case.petitioner_name or "", case.respondent_name or ""),
        )
        if dept_result.get("primary"):
            from apps.accounts.models import Department
            case.primary_department = Department.objects.filter(code=dept_result["primary"]).first()
            case.save()
            case.secondary_departments.set(
                Department.objects.filter(code__in=dept_result.get("secondary", []))
            )
            print(
                f"  [Extractor] Dept classification: primary={dept_result['primary']} "
                f"secondary={dept_result.get('secondary')} confidence={dept_result.get('confidence')} "
                f"method={dept_result.get('method')}"
            )
        else:
            print("  [Extractor] Dept classification: no match — case will be visible only to central law role")
    except Exception as e:
        # Never let dept classification fail extraction itself.
        print(f"  [Extractor] Dept classification skipped due to error: {e}")

    judgment.extraction_confidence = 0.95
    judgment.processing_status = "completed"
    judgment.save()

    return extracted_data