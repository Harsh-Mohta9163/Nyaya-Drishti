"""
LLM-based structured extraction using NVIDIA NIM (Llama 3.3 70B).

Extracts court directions, order type, entities, contempt indicators,
and financial implications from the operative order section.
"""
import json
import logging
from datetime import date

logger = logging.getLogger(__name__)

LEGAL_SYSTEM_PROMPT = """You are a specialist in analyzing Indian High Court judgments, particularly from the Karnataka High Court.

Your task is to extract structured information from the OPERATIVE ORDER section of a judgment.

Return a JSON object with EXACTLY these fields:

{
  "court_directions": [
    {
      "text": "Verbatim directive text from the order",
      "responsible_entity": "Department/official who must act",
      "deadline_mentioned": "Any deadline mentioned in the directive, or null",
      "action_required": "Brief summary of what must be done"
    }
  ],
  "order_type": "One of: Allowed | Dismissed | Disposed | Partial | Modified | Remanded",
  "entities": [
    {
      "name": "Name of government department/official",
      "role": "respondent | petitioner | interested_party"
    }
  ],
  "contempt_indicators": ["List of exact phrases indicating coercive/contempt language"],
  "financial_implications": {
    "amount": null,
    "type": "compensation | penalty | cost | refund | none",
    "details": ""
  },
  "appeal_type": "SLP | LPA | Review | Writ_Appeal | none",
  "case_metadata": {
    "case_number": "Extract from header if visible",
    "bench": "Single/Division bench",
    "judgment_date": "Date if found"
  }
}

RULES:
1. Extract directives VERBATIM - do not paraphrase
2. Only extract from the OPERATIVE ORDER section, not from facts or analysis
3. Look for contempt-related phrases like: "shall comply without fail", "failing which", "coercive action", "personal appearance"
4. If information is not found, use null or empty values - never guess
5. Respond with ONLY valid JSON, no markdown formatting"""


def _build_client():
    """Build OpenAI-compatible client for NVIDIA NIM or Groq."""
    try:
        from openai import OpenAI
        from django.conf import settings

        provider = getattr(settings, "LLM_PROVIDER", "nvidia").lower()
        if provider == "nvidia":
            base_url = settings.NVIDIA_BASE_URL
            api_key = settings.NVIDIA_API_KEY
            model = "meta/llama-3.3-70b-instruct"
        else:
            base_url = settings.GROQ_BASE_URL
            api_key = settings.GROQ_API_KEY
            model = "llama-3.1-8b-instant"

        if not api_key:
            logger.warning("No API key configured for %s", provider)
            return None, None
        return OpenAI(base_url=base_url, api_key=api_key), model
    except Exception as e:
        logger.error("Failed to build LLM client: %s", e)
        return None, None


def _fallback_extract(case, sections):
    """Rule-based fallback when LLM is unavailable."""
    operative_order = sections.get("operative_order", "")
    lines = [line.strip() for line in operative_order.splitlines() if line.strip()]
    directions = []
    for line in lines[:10]:
        if len(line) > 20:
            directions.append({
                "text": line,
                "responsible_entity": "",
                "deadline_mentioned": None,
                "action_required": line[:100],
            })

    lowered = operative_order.lower()
    if "allowed" in lowered:
        order_type = "Allowed"
    elif "dismissed" in lowered:
        order_type = "Dismissed"
    elif "disposed" in lowered:
        order_type = "Disposed"
    else:
        order_type = "unknown"

    return {
        "header_data": {
            "case_number": case.case_number,
            "court": case.court,
            "judgment_date": (
                case.judgment_date.isoformat()
                if hasattr(case.judgment_date, "isoformat")
                else str(case.judgment_date)
            ),
        },
        "operative_order": operative_order,
        "court_directions": directions,
        "order_type": order_type,
        "entities": [{"name": case.respondent, "role": "respondent"}] if case.respondent else [],
        "extraction_confidence": 0.45,
        "ocr_confidence": 0.5,
        "source_references": [{"section": "operative_order", "page": 1, "paragraph": 1}],
    }


def extract_structured_data(case, sections):
    """
    Extract structured data from judgment sections using LLM.

    Falls back to rule-based extraction if LLM is unavailable.
    """
    client, model = _build_client()
    if client is None:
        logger.info("Using fallback extraction for case %s", case.case_number)
        return _fallback_extract(case, sections)

    header = sections.get("header", "")[:2000]
    operative = sections.get("operative_order", "")[:6000]

    if not operative.strip():
        logger.warning("Empty operative order for case %s", case.case_number)
        return _fallback_extract(case, sections)

    user_message = (
        f"CASE NUMBER: {case.case_number}\n"
        f"COURT: {case.court}\n"
        f"CASE TYPE: {case.case_type}\n"
        f"JUDGMENT DATE: {case.judgment_date}\n\n"
        f"--- HEADER ---\n{header}\n\n"
        f"--- OPERATIVE ORDER ---\n{operative}"
    )

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0.1,
            max_tokens=2000,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": LEGAL_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
        )

        content = response.choices[0].message.content
        if not content:
            return _fallback_extract(case, sections)

        parsed = json.loads(content)
        logger.info("LLM extraction successful for case %s", case.case_number)

        # Normalize into the format expected by the Case/ExtractedData models
        return {
            "header_data": parsed.get("case_metadata", {
                "case_number": case.case_number,
                "court": case.court,
                "judgment_date": str(case.judgment_date),
            }),
            "operative_order": operative,
            "court_directions": parsed.get("court_directions", []),
            "order_type": parsed.get("order_type", "unknown"),
            "entities": parsed.get("entities", []),
            "extraction_confidence": 0.85,
            "ocr_confidence": 0.85,
            "source_references": [{"section": "operative_order"}],
            # Extra fields for action plan generation
            "contempt_indicators": parsed.get("contempt_indicators", []),
            "financial_implications": parsed.get("financial_implications", {}),
            "appeal_type": parsed.get("appeal_type", "none"),
        }

    except json.JSONDecodeError as e:
        logger.error("LLM returned invalid JSON for case %s: %s", case.case_number, e)
        return _fallback_extract(case, sections)
    except Exception as e:
        logger.error("LLM extraction failed for case %s: %s", case.case_number, e)
        return _fallback_extract(case, sections)