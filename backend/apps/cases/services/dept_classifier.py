"""Map judgment text to one of the 48 Karnataka secretariat departments.

LLM-first strategy:
  - Single NVIDIA-NIM 70B call with the full 48-dept catalogue in the prompt.
  - Falls back to a deterministic keyword pass only when the LLM call fails
    (network, rate limit) or returns an invalid code.
  - The Pydantic schema forces JSON output, mirroring the 4 extraction agents.

Returns a dict the extractor and override endpoint can both consume:
  {"primary": "HEALTH",
   "secondary": ["FINANCE", "PWD"],
   "confidence": 0.0..1.0,
   "method": "llm" | "keyword_fallback" | "none"}
"""
import logging
from typing import Optional

from pydantic import BaseModel, Field

from apps.accounts.models import Department

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Schema (Pydantic — same json_object enforcement pattern as the 4 agents)
# ---------------------------------------------------------------------------

class DeptClassification(BaseModel):
    primary_code: str = Field(
        description="EXACT code of the single most responsible Karnataka government "
                    "department (e.g., 'HEALTH', 'COMM_TAX', 'REVENUE'). Must be one "
                    "of the codes from the catalogue."
    )
    secondary_codes: list[str] = Field(
        default_factory=list,
        description="Up to 3 EXACT codes for departments that are also affected "
                    "(financial impact, joint compliance, etc.). Never include the primary.",
    )
    rationale: str = Field(
        description="One sentence justifying the primary assignment based on subject matter."
    )


# ---------------------------------------------------------------------------
# Catalogue builder
# ---------------------------------------------------------------------------

def _build_catalogue() -> tuple[list[dict], set[str]]:
    """Return (catalogue_rows, valid_codes_set) from the DB.

    catalogue_rows = [{"code": "HEALTH", "name": "...", "sector": "...", "keywords": [...]}, ...]
    """
    rows = []
    codes = set()
    for d in Department.objects.filter(is_active=True).order_by("code"):
        rows.append({
            "code": d.code,
            "name": d.name,
            "sector": d.sector or "",
            "keywords": list(d.keywords or [])[:6],  # cap to keep prompt small
        })
        codes.add(d.code)
    return rows, codes


def _catalogue_block(rows: list[dict]) -> str:
    """Format the dept catalogue compactly for inclusion in the prompt."""
    lines = []
    for r in rows:
        kw = ", ".join(r["keywords"]) if r["keywords"] else ""
        kw_part = f" — keywords: {kw}" if kw else ""
        lines.append(f"  {r['code']:<22} {r['name']} [{r['sector']}]{kw_part}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Keyword fallback (used only when LLM is unavailable)
# ---------------------------------------------------------------------------

def _keyword_fallback(case_text: str, parties: tuple, entities: list) -> dict:
    """Deterministic backup — keyword voting, no LLM."""
    haystack = " ".join([
        case_text or "",
        " ".join(str(e) for e in (entities or [])),
        str(parties[0] if parties else ""),
        str(parties[1] if len(parties) > 1 else ""),
    ]).lower()
    scores: dict[str, int] = {}
    for dept in Department.objects.filter(is_active=True).only("code", "keywords"):
        kws = dept.keywords or []
        hits = sum(1 for kw in kws if kw.lower() in haystack)
        if hits:
            scores[dept.code] = hits
    if not scores:
        return {"primary": None, "secondary": [], "confidence": 0.0, "method": "none"}
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    primary = ranked[0][0]
    secondary = [c for c, _ in ranked[1:4]]
    top_sum = sum(s for _, s in ranked[:3])
    conf = round(ranked[0][1] / top_sum, 2) if top_sum else 0.0
    return {
        "primary": primary,
        "secondary": secondary,
        "confidence": conf,
        "method": "keyword_fallback",
    }


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------

def classify(case_text: str, entities: list, parties: tuple) -> dict:
    """Map judgment text to (primary_department, secondary_departments) via LLM.

    Args:
        case_text: Operative order + body text concatenation.
        entities: Named entities extracted by the agents.
        parties: (petitioner_name, respondent_name).

    Returns:
        {"primary": "HEALTH" or None, "secondary": [...up to 3],
         "confidence": 0.0..1.0, "method": "llm" | "keyword_fallback" | "none"}
    """
    rows, valid_codes = _build_catalogue()
    if not rows:
        logger.warning("dept_classifier: no active departments in DB")
        return {"primary": None, "secondary": [], "confidence": 0.0, "method": "none"}

    petitioner = str(parties[0] if parties else "")
    respondent = str(parties[1] if len(parties) > 1 else "")
    entity_str = ", ".join(str(e) for e in (entities or [])[:30])
    excerpt = (case_text or "")[:6000]

    prompt = (
        "You are routing a Karnataka High Court judgment to the responsible "
        "state government department(s). Read the case below and assign:\n"
        "  1) ONE primary_code — the department primarily accountable for compliance.\n"
        "  2) Up to 3 secondary_codes — departments also materially affected (e.g., "
        "Finance when there is a monetary award; PWD when public works are ordered).\n\n"
        "STRICT RULES:\n"
        "  - primary_code and secondary_codes MUST be EXACT codes from the catalogue below.\n"
        "  - For any GST / VAT / commercial-tax / income-tax dispute use FINANCE "
        "(Karnataka's Commercial Taxes Department sits under FINANCE). NEVER invent codes.\n"
        "  - For land acquisition / mutation / khata / revenue records use REVENUE.\n"
        "  - For Karnataka Housing Board / KHB / slum board allotment use HOUSING.\n"
        "  - For KPTCL / BESCOM / HESCOM / MESCOM / electricity board service or tariff "
        "matters use ENERGY.\n"
        "  - For criminal prosecutions (IPC / CrPC / NDPS / POCSO) where State is the "
        "prosecutor use HOME (Police).\n"
        "  - For medical-negligence, drug-control, PCPNDT, hospital licensing use HEALTH "
        "(NOT MED_EDU — MED_EDU is for medical colleges and PG seats).\n"
        "  - For Kannada language, state symbols, statehood-day, regional culture use "
        "KANNADA_CULTURE.\n"
        "  - For motor-accident / Motor Vehicles Act claims the primary is TRANSPORT "
        "(secondary may be FINANCE for compensation).\n"
        "  - Do NOT default to HOME, TECH_EDU, or LAW unless the subject genuinely fits.\n"
        "  - Add FINANCE as a secondary whenever the order has a monetary award, "
        "compensation, refund, or fine.\n\n"
        "DEPARTMENT CATALOGUE (code  name [sector]  keywords):\n"
        f"{_catalogue_block(rows)}\n\n"
        "CASE:\n"
        f"  Petitioner: {petitioner}\n"
        f"  Respondent: {respondent}\n"
        f"  Entities: {entity_str}\n"
        f"  Excerpt:\n{excerpt}\n\n"
        "Return JSON with keys: primary_code, secondary_codes, rationale."
    )

    try:
        from apps.cases.services.extractor import _call_agent_70b
        result = _call_agent_70b(prompt, DeptClassification, temperature=0.0)
        primary = (result.get("primary_code") or "").strip().upper()
        secondary = [str(c).strip().upper() for c in (result.get("secondary_codes") or [])]
        rationale = result.get("rationale", "")

        if primary not in valid_codes:
            logger.warning("dept_classifier: LLM returned invalid primary=%r — falling back", primary)
            return _keyword_fallback(case_text, parties, entities)

        secondary = [c for c in secondary if c in valid_codes and c != primary][:3]
        logger.info("dept_classifier(LLM): primary=%s secondary=%s rationale=%s",
                    primary, secondary, rationale[:120])
        return {
            "primary": primary,
            "secondary": secondary,
            "confidence": 0.9,
            "method": "llm",
        }
    except Exception as e:
        logger.warning("dept_classifier: LLM call failed (%s) — falling back to keywords", e)
        return _keyword_fallback(case_text, parties, entities)


# ---------------------------------------------------------------------------
# Helper used by the extractor + backfill command
# ---------------------------------------------------------------------------

def apply_to_case(case, classification: dict) -> None:
    """Persist a classify() result onto a Case row."""
    if classification.get("primary"):
        case.primary_department = Department.objects.filter(
            code=classification["primary"]
        ).first()
    case.save()
    if classification.get("secondary"):
        case.secondary_departments.set(
            Department.objects.filter(code__in=classification["secondary"])
        )
    else:
        case.secondary_departments.clear()
