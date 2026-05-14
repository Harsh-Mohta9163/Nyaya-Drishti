"""Re-frame court_directions from the GOVERNMENT'S perspective.

Agent 4 extracts directives verbatim — that's correct for the source-of-truth
record. But a dept officer reading the verified list needs to know two things
Agent 4 doesn't answer well:

  1. "Is this directive something MY DEPARTMENT must execute, or is it for the
     court / the accused / another party?"
  2. If it is mine: "What are the concrete implementation steps?"
     If it isn't: "Is there anything I need to track at all?"

This enricher takes the already-extracted directives plus case context and
classifies each one (actor_type, gov_action_required) and writes either
`implementation_steps` (for govt actions) or `display_note` (for others).

Provider: OpenRouter `google/gemini-2.5-pro` (best instruction-following for
the anti-hallucination guardrails we need here). Falls back to NVIDIA-NIM
70B if the OpenRouter call fails. Output keys are merged INTO each directive
dict so the frontend can pick them up with no schema migration.
"""
from __future__ import annotations

import json
import logging
import os
import time

import requests
from django.conf import settings
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

ACTOR_TYPES = (
    "government_department",  # MY dept (or another dept) must execute
    "court_or_registry",      # Court itself / Registrar / Reference Court will act
    "accused_or_petitioner",  # The litigating private party
    "third_party",            # Bank, employer, jail, KHB, etc. — not the dept
    "informational",          # Dismissal / acquittal / no-op
)


class DirectiveEnrichment(BaseModel):
    actor_type: str = Field(
        description=(
            "Who must execute this directive. Must be exactly one of: "
            "government_department, court_or_registry, accused_or_petitioner, "
            "third_party, informational."
        )
    )
    gov_action_required: bool = Field(
        description=(
            "True iff a Karnataka state government department must take "
            "compliance action. Sentencing, acquittals, court-internal admin "
            "(supply copies, issue warrants), and accused-side directives are "
            "all FALSE."
        )
    )
    implementation_steps: list[str] = Field(
        default_factory=list,
        description=(
            "Concrete, sequenced steps the department's LCO must take to "
            "execute this directive. 3-5 imperative bullets, each ~1 sentence, "
            "with specific procedural references (Treasury Code / Receipt / "
            "form number) wherever applicable. EMPTY LIST if gov_action_required "
            "is false."
        ),
    )
    display_note: str = Field(
        default="",
        description=(
            "One-sentence note shown to the HLC / LCO when this directive is "
            "NOT a department action — e.g. 'Court will execute via Registrar — "
            "no action required from your department.' EMPTY STRING if "
            "gov_action_required is true."
        ),
    )
    govt_summary: str = Field(
        default="",
        description=(
            "Short one-line restatement of this directive in plain language "
            "from the government's perspective — what a Secretary would say in "
            "a half-hour briefing. Always populated."
        ),
    )


class CaseEnrichment(BaseModel):
    enrichments: list[DirectiveEnrichment] = Field(
        description=(
            "One enrichment per input directive, in the same order. The list "
            "length MUST equal the number of input directives."
        )
    )


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------

def _build_prompt(case_meta: dict, directives: list[dict]) -> str:
    lines = [
        "You are a Karnataka State Secretariat compliance officer reading a "
        "judgment that has just been routed to a specific department. Your job "
        "is to translate the court's directives into actionable guidance for "
        "the Head of Legal Cell (verifier), the Litigation Conducting Officer "
        "(executor), and the Nodal Officer (deadline watcher).",
        "",
        f"Case: {case_meta.get('case_number', '?')}  ({case_meta.get('case_type', '?')})",
        f"Court: {case_meta.get('court_name', '?')}",
        f"Petitioner: {case_meta.get('petitioner_name', '?')}",
        f"Respondent: {case_meta.get('respondent_name', '?')}",
        f"Area of law: {case_meta.get('area_of_law', '?')}",
        f"Primary statute: {case_meta.get('primary_statute', '?')}",
        f"Responsible department: {case_meta.get('primary_department', '?')}",
        f"Disposition: {case_meta.get('disposition', '?')}",
        "",
        "═══ ANTI-HALLUCINATION RULES (CRITICAL — read these first) ═══",
        "  1. NEVER invent procedural specifics not explicitly named in the "
        "operative order. Forbidden inventions include:",
        "       • Form numbers (e.g. 'Form TCR-3', 'GST RFD-01')",
        "       • Treasury Code section numbers (e.g. 'Treasury Code 431', 'Rule 5')",
        "       • Internal file reference numbers (e.g. 'FD/CGST/2023', 'KPTCL/B16/...')",
        "       • Specific deadlines in days (e.g. 'within 30 days') unless "
        "the operative order names that exact period.",
        "     If the operative order does not name a form / code / rule / deadline, "
        "do NOT make one up. Use plain English: 'process the refund through the "
        "department's standard treasury workflow' — not 'using Form TCR-3'.",
        "",
        "  2. DISTINGUISH WHAT THE COURT ACTUALLY ORDERED. Read the operative "
        "order carefully and match the action to one of these patterns:",
        "       (a) QUASHED / SET ASIDE an administrative order → the action is "
        "to REVERSE that administrative state. Example: 'quashed the Rule 86A "
        "blocking order' → 'Unblock the Electronic Credit Ledger on the GST "
        "portal'. NOT a refund.",
        "       (b) DECLARED a legal status (exempt, eligible, entitled) → the "
        "action is to UPDATE the department's assessment / classification "
        "records to reflect that status going forward. NOT a refund unless the "
        "court also explicitly directs payment.",
        "       (c) DIRECTED PAYMENT / REFUND / COMPENSATION → only THEN is the "
        "action to process a payment. The court must explicitly say 'pay', "
        "'refund', 'release', 'disburse' for this category.",
        "       (d) REMANDED for reconsideration → the action is to RECONSIDER "
        "afresh in light of the court's observations. NOT to grant the relief "
        "automatically.",
        "       (e) MODIFIED an award with specific math → the action is to "
        "RECALCULATE per the court's formula AND disburse.",
        "",
        "  3. WHEN IN DOUBT, STAY GENERAL. It is better to say 'update the "
        "department's assessment records to reflect the petitioner's exempt "
        "status' than to fabricate 'Update field FD-XYZ in the Commercial Taxes "
        "module of e-Office'. The HLC and LCO know their own internal procedures.",
        "",
        "═══ CLASSIFICATION RULES ═══",
        "  • actor_type MUST be exactly one of: "
        "government_department, court_or_registry, accused_or_petitioner, "
        "third_party, informational.",
        "  • gov_action_required is TRUE ONLY when a state secretariat "
        "department must take a compliance step.",
        "  • Sentencing, acquittals, set-off, set-aside of trial-court orders, "
        "directing the Registrar to issue warrants, ordering supply of copies, "
        "asking the accused to pay personal compensation under §357(3) CrPC, "
        "directing jail authorities — all of these are NOT gov_action_required.",
        "  • If the writ petition / appeal is DISMISSED → no government action "
        "needed; actor_type='informational', gov_action_required=false.",
        "",
        "═══ OUTPUT FORMAT ═══",
        "  • For gov_action_required=True items: write 2-4 imperative steps "
        "describing what the LCO must physically do. Each step is ONE sentence. "
        "Reference specific numbers, percentages, parties only if they appear "
        "in the operative order. Otherwise stay general.",
        "  • For gov_action_required=False items: leave implementation_steps "
        "EMPTY and write a one-sentence display_note explaining why no action "
        "is needed (e.g. 'No action — court will execute via Registrar' or "
        "'No action — petition dismissed').",
        "  • ALWAYS fill govt_summary in plain English (~15 words) from the "
        "government's perspective.",
        "",
        f"DIRECTIVES TO ENRICH ({len(directives)} total — preserve order):",
    ]

    for i, d in enumerate(directives):
        text = (
            d.get("description")
            or d.get("text")
            or d.get("sourceText")
            or d.get("title")
            or ""
        )
        action = d.get("action_required", "")
        entity = d.get("responsible_entity") or d.get("source") or ""
        deadline = d.get("deadline_mentioned") or d.get("dueDate") or ""
        money = d.get("financial_details") or d.get("financialDetails") or ""

        lines.append(f"\n[{i}]")
        if entity:
            lines.append(f"  Responsible entity (as written): {entity}")
        if text:
            lines.append(f"  Verbatim text: {text[:1200]}")
        if action and action != text:
            lines.append(f"  Action note: {action[:400]}")
        if deadline:
            lines.append(f"  Deadline mentioned: {deadline}")
        if money:
            lines.append(f"  Financial detail: {money}")

    lines.append("")
    lines.append(
        "Respond with JSON of shape "
        "{\"enrichments\": [{actor_type, gov_action_required, "
        "implementation_steps, display_note, govt_summary}, ...]}. "
        f"List MUST contain exactly {len(directives)} items in the same order."
    )
    return "\n".join(lines)


def _call_openrouter_gemini_pro(prompt: str, schema_cls, temperature: float = 0.1) -> dict:
    """Send the enrichment prompt to google/gemini-2.5-pro via OpenRouter.

    Returns an empty dict if the key is missing or all retries fail — the
    caller should handle the empty case and fall back to the NVIDIA NIM 70B
    path via apps.cases.services.extractor._call_agent_70b.
    """
    api_key = getattr(settings, "OPENROUTER_API_KEY", "") or os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        logger.warning("directive_enricher: OPENROUTER_API_KEY not set; cannot call Gemini Pro")
        return {}

    base_url = getattr(settings, "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
    model = "google/gemini-2.5-pro"

    schema_json = json.dumps(schema_cls.model_json_schema(), indent=2)
    full_prompt = (
        f"{prompt}\n\nRespond ONLY with valid JSON matching this schema:\n{schema_json}"
    )

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
        # Gemini 2.5 Pro uses internal reasoning tokens that count against
        # max_tokens — keep this generous so we don't truncate before the
        # actual JSON payload appears.
        "max_tokens": 16384,
        "response_format": {"type": "json_object"},
        # Cap reasoning effort so we don't burn the whole budget on internal
        # chain-of-thought before producing JSON. "low" is plenty for this
        # classify-and-summarize task.
        "reasoning": {"effort": "low"},
    }

    last_error = None
    for attempt in range(3):
        try:
            print(f"  [OR-Gemini-2.5-Pro] Calling {model} (attempt {attempt+1}/3, "
                  f"prompt {len(full_prompt)} chars)...")
            resp = requests.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=300,
            )
            if resp.status_code in (429, 503):
                wait = 20 * (attempt + 1)
                print(f"  [OR-Gemini-2.5-Pro] Rate limited ({resp.status_code}); waiting {wait}s")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Try to salvage — Gemini occasionally wraps in markdown fences
                from apps.cases.services.extractor import _salvage_json
                recovered = _salvage_json(content)
                if recovered:
                    return recovered
                last_error = ValueError(f"Malformed JSON; first 200 chars: {content[:200]!r}")
                continue
        except Exception as e:
            last_error = e
            print(f"  [OR-Gemini-2.5-Pro] Attempt {attempt+1} failed: {e}")
            time.sleep(10)

    logger.warning("directive_enricher: all OpenRouter Gemini retries failed (%s)", last_error)
    return {}


def enrich_case_directives(case, *, force: bool = False) -> dict:
    """Enrich every directive in `case.judgments.first().court_directions`.

    Args:
        case: apps.cases.models.Case
        force: re-enrich even if directives already have actor_type set.

    Returns:
        {"updated": N, "skipped": M, "errors": K, "method": "llm" | "skipped"}
    """
    judgment = case.judgments.first()
    if not judgment:
        return {"updated": 0, "skipped": 0, "errors": 0, "method": "skipped"}

    directives = list(judgment.court_directions or [])
    if not directives:
        return {"updated": 0, "skipped": 0, "errors": 0, "method": "skipped"}

    # Skip cases that look already enriched unless forced
    if not force and all(isinstance(d, dict) and "actor_type" in d for d in directives):
        return {"updated": 0, "skipped": len(directives), "errors": 0, "method": "skipped"}

    case_meta = {
        "case_number": case.case_number,
        "case_type": case.case_type,
        "court_name": case.court_name,
        "petitioner_name": case.petitioner_name,
        "respondent_name": case.respondent_name,
        "area_of_law": case.area_of_law,
        "primary_statute": case.primary_statute,
        "primary_department": case.primary_department.name if case.primary_department else None,
        "disposition": judgment.disposition,
    }

    prompt = _build_prompt(case_meta, directives)
    method = "llm"

    # Primary: OpenRouter Gemini 2.5 Pro (best instruction-following for the
    # anti-hallucination guardrails). Fallback: NVIDIA NIM Llama 70B if Gemini
    # is unavailable or returns nothing usable.
    try:
        result = _call_openrouter_gemini_pro(prompt, CaseEnrichment, temperature=0.1)
        enrichments = (result or {}).get("enrichments") or []
        if not enrichments:
            raise RuntimeError("Gemini Pro returned no enrichments — falling back to NVIDIA 70B")
        method = "llm_gemini"
    except Exception as gem_err:
        logger.warning(
            "directive_enricher: Gemini Pro path failed (%s); trying NVIDIA 70B", gem_err
        )
        try:
            from apps.cases.services.extractor import _call_agent_70b
            result = _call_agent_70b(prompt, CaseEnrichment, temperature=0.1)
            enrichments = (result or {}).get("enrichments") or []
            method = "llm_nvidia_fallback"
        except Exception as e:
            logger.warning("directive_enricher: NVIDIA 70B fallback also failed (%s)", e)
            return {"updated": 0, "skipped": len(directives), "errors": 1, "method": "skipped"}

    if len(enrichments) != len(directives):
        logger.warning(
            "directive_enricher: LLM returned %d enrichments for %d directives; padding/truncating",
            len(enrichments), len(directives),
        )

    updated = 0
    for i, d in enumerate(directives):
        if not isinstance(d, dict):
            continue
        if i < len(enrichments):
            enr = enrichments[i] or {}
            actor = str(enr.get("actor_type", "informational")).strip().lower()
            if actor not in ACTOR_TYPES:
                actor = "informational"
            d["actor_type"] = actor
            d["gov_action_required"] = bool(enr.get("gov_action_required", False))
            d["implementation_steps"] = [s for s in (enr.get("implementation_steps") or []) if isinstance(s, str)]
            d["display_note"] = str(enr.get("display_note") or "")
            d["govt_summary"] = str(enr.get("govt_summary") or "")
        else:
            d["actor_type"] = "informational"
            d["gov_action_required"] = False
            d["implementation_steps"] = []
            d["display_note"] = "Enrichment unavailable — manual review recommended."
            d["govt_summary"] = ""
        updated += 1

    judgment.court_directions = directives
    judgment.save(update_fields=["court_directions", "updated_at"])
    return {"updated": updated, "skipped": 0, "errors": 0, "method": method}
