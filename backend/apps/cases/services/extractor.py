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
    text: str = Field(description="The COMPLETE verbatim paragraph(s) from the operative order. Include ALL details: amounts, percentages, calculations, conditions, and reasoning. Do NOT shorten or summarize.")
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
        "max_tokens": 4096,
        "response_format": {"type": "json_object"},
    }

    for attempt in range(5):
        try:
            print(f"  [NVIDIA 70B] Calling {model} (attempt {attempt+1}/5)...")
            resp = requests.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=120,
            )
            if resp.status_code in (429, 503):
                wait = 30 * (attempt + 1)
                print(f"  [NVIDIA 70B] Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            return json.loads(content)
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response else 0
            if status in (429, 503):
                wait = 30 * (attempt + 1)
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("NVIDIA Llama 70B failed after 5 retries")


def _call_agent_8b(prompt: str, schema: type[BaseModel], temperature: float) -> dict:
    """Agent 1 & 4: Calls Groq 8B for fast extraction, falls back to NVIDIA 70B."""
    api_key = settings.GROQ_API_KEY
    base_url = getattr(settings, "GROQ_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
    model = "llama-3.1-8b-instant"

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
        "max_tokens": 2048,
        "response_format": {"type": "json_object"},
    }

    last_error = None
    for attempt in range(3):
        try:
            print(f"  [Groq 8B] Calling {model} (attempt {attempt+1})...")
            resp = requests.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )
            if resp.status_code in (429, 503):
                wait = 20 * (attempt + 1)
                print(f"  [Groq 8B] Rate limited (HTTP {resp.status_code}), waiting {wait}s...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            return json.loads(content)
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else 0
            print(f"  [Groq 8B] HTTP error {status_code}: {e}")
            last_error = e
            if status_code in (429, 503):
                wait = 20 * (attempt + 1)
                print(f"  [Groq 8B] Waiting {wait}s before retry...")
                time.sleep(wait)
            else:
                break
        except Exception as e:
            print(f"  [Groq 8B] Error: {e}")
            last_error = e
            time.sleep(5)

    # Fallback: use NVIDIA 70B instead of failing completely
    print(f"  [Groq 8B] All attempts failed ({last_error}). Falling back to NVIDIA 70B...")
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
    try:
        print(f"  [NVIDIA 70B Fallback] Calling meta/llama-3.3-70b-instruct...")
        resp = requests.post(
            f"{nvidia_url}/chat/completions",
            headers=nvidia_headers,
            json=nvidia_payload,
            timeout=120,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception as e:
        raise RuntimeError(f"Both Groq 8B and NVIDIA 70B failed. Last error: {e}")


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

def _safe_str(val) -> str:
    """Helper to handle if LLM returns a list for a string field."""
    if isinstance(val, list):
        return ", ".join(str(v) for v in val)
    if val is None:
        return ""
    return str(val).strip()

# ==============================================================================
# Extraction Service (4 Agents)
# ==============================================================================

def extract_structured_data(
    judgment_id: str,
    header_text: str,
    middle_text: str,
    operative_text: str
) -> dict:
    judgment = Judgment.objects.get(id=judgment_id)
    case = judgment.case
    extracted_data = {}

    # --- AGENT 1: Registry Clerk (8B) ---
    if header_text:
        print(f"  [Agent 1] Registry Clerk (Header)...")
        header_prompt = (
            "Extract metadata from the header of an Indian High Court judgment PDF.\n"
            "Extract every field exactly as it appears. Pay attention to case number, date, judges, and parties.\n"
            f"Document:\n{header_text}"
        )
        extracted_data["registry"] = _call_agent_8b(header_prompt, RegistryExtraction, temperature=0.0)

    # --- AGENT 4: Compliance Officer (70B — most critical for Theme 11) ---
    if operative_text:
        print(f"  [Agent 4] Compliance Officer (70B — Operative Order)...")
        operative_prompt = (
            "You are a senior compliance officer for a government department. "
            "Extract the COMPLETE operative order from this Indian court judgment.\n\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. IGNORE any case law citations or legal reasoning. Focus ONLY on what the department MUST DO.\n"
            "2. For each court direction, capture the FULL PARAGRAPH — do NOT extract isolated sentences.\n"
            "   A government officer reading your extraction must understand the COMPLETE order without referring back to the judgment.\n"
            "3. Include ALL financial details: exact rupee amounts, percentages, base values, calculation methods, deductions.\n"
            "4. The 'action_required' field should read like a clear compliance instruction, e.g.:\n"
            "   BAD: 'Pay market value to appellants'\n"
            "   GOOD: 'Pay enhanced compensation of ₹3,38,400/- per acre to appellants (base value ₹7,20,000 per acre minus 53% developmental charges under HUDCO scheme), plus statutory benefits and interest under Sections 23(1A), 23(2), and 28 of the Land Acquisition Act.'\n"
            "5. For 'operative_order_summary': Write a complete 3-5 sentence summary that a government secretary can read to understand the entire order.\n\n"
            "RESPONSIBLE ENTITY RULES:\n"
            "- If the court itself must act (e.g. 'modified award shall be drawn'), responsible_entity = 'Reference Court' or the specific court/tribunal.\n"
            "- If a government department/officer must pay or act, identify the SPECIFIC entity.\n"
            "- Different directives may have DIFFERENT responsible entities.\n\n"
            f"Case Type: {case.case_type or 'Unknown'}\n"
            f"Petitioner/Appellant: {case.petitioner_name or 'Unknown'}\n"
            f"Respondent: {case.respondent_name or 'Unknown'}\n\n"
            f"OPERATIVE ORDER TEXT:\n{operative_text}"
        )
        # Use 70B for the most critical extraction — court orders must be complete and accurate
        print(f"  [Sleep] Waiting 15s before 70B call for compliance...")
        time.sleep(15)
        extracted_data["compliance"] = _call_agent_70b(operative_prompt, ComplianceExtraction, temperature=0.1)

    # --- AGENT 2: Legal Analyst (70B) ---
    if middle_text:
        print(f"  [Agent 2] Legal Analyst (Facts/Issues)...")
        analyst_prompt = (
            "Extract the factual summary and legal issues framed from the body of this judgment.\n"
            "Write in clear, professional prose.\n"
            f"Document:\n{middle_text}"
        )
        extracted_data["analyst"] = _call_agent_70b(analyst_prompt, AnalystExtraction, temperature=0.2)
        
        # Prevent 429 rate limits on NVIDIA's free tier for the second 70B call
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
        extracted_data["scholar"] = _call_agent_70b(scholar_prompt, ScholarExtraction, temperature=0.1)

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

        doc_type = _safe_str(h.get("document_type", ""))
        if doc_type: judgment.document_type = doc_type

        appeal_type = _safe_str(h.get("appeal_type", "none")).lower()
        if appeal_type: judgment.appeal_type = appeal_type

        extracted_case_number = _safe_str(h.get("case_number", ""))
        if extracted_case_number:
            existing = Case.objects.filter(
                court_name=_safe_str(h.get("court_name", case.court_name)),
                case_number=extracted_case_number,
                case_year=case.case_year,
            ).exclude(id=case.id).first()

            if existing:
                old_case = case
                judgment.case = existing
                judgment.save()  # MUST save before deleting old_case to avoid cascade-delete
                case = existing
                old_case.delete()

            case.case_number = extracted_case_number

        case.court_name = _safe_str(h.get("court_name", case.court_name))
        case.case_type = _safe_str(h.get("case_type", case.case_type))
        case.petitioner_name = _safe_str(h.get("petitioner_name", ""))
        case.respondent_name = _safe_str(h.get("respondent_name", ""))
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
        
        # Area of law & Statute are now extracted by the Scholar (Agent 3)
        case.area_of_law = _safe_str(s.get("area_of_law", ""))
        case.primary_statute = _safe_str(s.get("primary_statute", ""))
        case.save()

    # Compliance (Agent 4)
    if "compliance" in extracted_data:
        c = extracted_data["compliance"]
        # Fix: LLM sometimes returns Pydantic schema wrapper instead of raw data
        if "$defs" in c or ("properties" in c and "type" in c):
            print("  [Extractor] Detected schema-wrapped compliance response, unwrapping from 'properties'...")
            c = c.get("properties", c)
        judgment.court_directions = c.get("court_directions", [])
        judgment.disposition = _sanitize_disposition(c.get("disposition", ""))
        judgment.winning_party_type = _sanitize_party_type(c.get("winning_party_type", ""))
        judgment.contempt_indicators = c.get("contempt_indicators", [])
        judgment.contempt_risk = c.get("contempt_risk", "Low")
        judgment.financial_implications = c.get("financial_implications", [])
        # Save full operative order summary
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

    judgment.extraction_confidence = 0.95
    judgment.processing_status = "completed"
    judgment.save()

    return extracted_data