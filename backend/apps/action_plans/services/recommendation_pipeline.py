"""
NyayaDrishti — 4-Agent Recommendation Pipeline V2
Complete rewrite with:
  - Detailed inter-agent prompts with full case context
  - Gemini 2.5 Pro for final agent with Llama fallbacks
  - Court hierarchy logic
  - Fixed DuckDB parquet path
  - Disposition/outcome passed to all agents
"""
import logging
import json
import uuid
import time
import re
import os
from typing import List, Dict, Any
from datetime import date, timedelta, datetime

from pydantic import BaseModel, Field
from django.conf import settings
from openai import OpenAI

from apps.action_plans.services.rag_engine import HybridRAGEngine
from apps.rag.parquet_store import DuckDBStore
from apps.action_plans.services.domain_prompts import get_domain_key, build_agent_prompt

logger = logging.getLogger(__name__)

def validate_financial_math(financial_implications: list[str], domain: str) -> dict:
    """
    Pure deterministic validation using regex.
    Returns: { "flags": list[str], "summary": str }
    """
    flags = []
    text = " ".join(financial_implications)

    if domain == "LAND_ACQUISITION":
        # Check deduction percentage
        deductions = re.findall(r'(\d+(?:\.\d+)?)\s*%\s*(?:developmental|deduction|discount)', text, re.IGNORECASE)
        for d in deductions:
            pct = float(d)
            if pct > 53:
                flags.append(f"WARNING: Deduction {pct}% exceeds SC-approved ceiling of 53% (Lal Chand v. Union)")
            elif pct < 20:
                flags.append(f"NOTE: Deduction {pct}% is very low — government may have grounds to challenge")

        # Check interest rate
        interest = re.findall(r'(\d+)\s*%\s*(?:per annum|p\.a\.|interest)', text, re.IGNORECASE)
        for i in interest:
            if int(i) > 9:
                flags.append(f"WARNING: Interest rate {i}% exceeds Section 28/34 LAA statutory rate of 9% p.a.")

    elif domain == "MOTOR_VEHICLES":
        # Check multiplier
        multipliers = re.findall(r'multiplier[:\s]+(\d+)', text, re.IGNORECASE)
        for m in multipliers:
            if not (8 <= int(m) <= 18):
                flags.append(f"WARNING: Multiplier {m} is outside Sarla Verma/Pranay Sethi table range [8-18]")
            if int(m) > 15:
                flags.append(f"NOTE: High multiplier {m} — verify victim's age matches this bracket")

    elif domain == "SERVICE_LAW":
        # Check if back wages are for very long period
        years = re.findall(r'(\d+)\s*years?\s*(?:back wages|arrears)', text, re.IGNORECASE)
        for y in years:
            if int(y) > 10:
                flags.append(f"NOTE: Back wages for {y} years is substantial — quantify total liability")

    summary = "\n".join(flags) if flags else "No mathematical anomalies detected."
    return {"flags": flags, "summary": summary}


# ==============================================================================
# Pydantic Schemas (Enhanced)
# ==============================================================================

class ResearchSummary(BaseModel):
    case_id: str
    case_title: str = Field(description="Title of the precedent case")
    relevance: str = Field(description="2-3 sentence explanation of why this case is similar")
    key_holding: str = Field(description="The court's core finding/ratio in this precedent")
    outcome: str = Field(description="APPEAL_ALLOWED, APPEAL_DISMISSED, DISPOSED_OFF, or UNKNOWN")
    applicability: str = Field(description="How this precedent supports or undermines the current case")

class Agent1Output(BaseModel):
    precedents: List[ResearchSummary]
    overall_trend: str = Field(description="Summary of what the precedents collectively suggest")
    precedent_strength: str = Field(description="STRONG, MODERATE, or WEAK - how strongly precedents support appeal")

class Agent2Output(BaseModel):
    pro_appeal_arguments: List[str] = Field(description="Specific legal arguments supporting an appeal")
    pro_compliance_arguments: List[str] = Field(description="Specific legal arguments supporting compliance")
    strongest_appeal_ground: str = Field(description="The single strongest ground for appeal, if any")
    strongest_compliance_reason: str = Field(description="The single strongest reason to comply")
    balance_assessment: str = Field(description="APPEAL_FAVORED, COMPLIANCE_FAVORED, or BALANCED")

class Agent3Output(BaseModel):
    procedural_loopholes: List[str]
    contempt_risk_assessment: str = Field(description="Detailed assessment of contempt risk if non-compliant")
    contempt_urgency: str = Field(description="HIGH, MEDIUM, or LOW")
    limitation_analysis: str = Field(description="Analysis of limitation period and deadlines")
    financial_risk: str = Field(description="Assessment of financial exposure")

class FinalVerdict(BaseModel):
    decision: str = Field(description="APPEAL or COMPLY")
    appeal_to: str = Field(description="The correct next appellate forum")
    confidence: float = Field(description="0.0 to 1.0")
    urgency: str = Field(description="HIGH, MEDIUM, or LOW")

class ActionPlanDetail(BaseModel):
    immediate_actions: List[str]
    financial_actions: List[str]

class Agent4Output(BaseModel):
    verdict: FinalVerdict
    primary_reasoning: str = Field(description="3-5 sentence detailed reasoning for the decision")
    appeal_grounds: List[str] = Field(description="Specific legal grounds for appeal")
    alternative_routes: List[str] = Field(description="Alternative legal remedies")
    action_plan: ActionPlanDetail
    risk_summary: str = Field(description="Key risks of the recommended action")

# ==============================================================================
# Court Hierarchy Logic
# ==============================================================================

COURT_HIERARCHY = {
    "subordinate": {"next": "High Court", "appeal_type": "Regular First Appeal / Writ Petition"},
    "district": {"next": "High Court", "appeal_type": "Regular First Appeal"},
    "tribunal": {"next": "High Court", "appeal_type": "Writ Petition under Art. 226"},
    "single_judge": {"next": "Division Bench of the same High Court", "appeal_type": "Intra-Court Appeal / Letters Patent Appeal"},
    "division_bench": {"next": "Supreme Court of India", "appeal_type": "Special Leave Petition under Art. 136"},
    "supreme_court": {"next": "Supreme Court (Review/Curative)", "appeal_type": "Review Petition under Art. 137"},
}

# Keywords used to detect whether a party in petitioner_name / respondent_name is the State.
# Match aggressively — government parties are referenced under many names in Indian judgments.
_GOVT_PARTY_TOKENS = [
    "state of", "state government", "government of", "union of india", "uoi",
    "republic of india", "uoi & ors", "secretary", "commissioner",
    "collector", "deputy commissioner", "asst commissioner", "assistant commissioner",
    "tahsildar", "tehsildar", "lokayukta", "central bureau", "cbi",
    "directorate", "department of", "department,", "municipal corporation",
    "panchayat", "municipality", "ministry of", "the state", "karnataka state",
    "bbmp", "bda", "kiadb", "kptcl", "kseb", "kpcl", "bescom",
    "principal secretary", "additional chief secretary", "chief secretary",
    "income tax officer", "ito ", "assessing officer", "ao ",
    "labour enforcement officer", "labour commissioner", "factories inspector",
    "public works", "pwd", "national highway", "nhai",
    "election commission", "ec ", "kerc",
    "registrar of", "sub-registrar", "land acquisition officer", "lao ",
    "deputy director", "joint director", "additional director",
    "commercial tax", "central excise", "central tax", "gst commissioner",
    "the commissioner", "the deputy commissioner", "the director",
    "the principal commissioner", "principal commissioner",
    "respondent state", "appellant state", "petitioner state",
]


def _party_is_government(name: str) -> bool:
    if not name:
        return False
    n = name.lower()
    return any(tok in n for tok in _GOVT_PARTY_TOKENS)


def _determine_government_role(petitioner: str, respondent: str,
                                winning_party: str, disposition: str,
                                case_type: str = "") -> dict:
    """Detect whether the government won or lost, regardless of disposition wording.

    The CCMS pipeline serves the government. When the government is the APPELLANT
    (criminal appeals, revenue appeals, writ appeals filed by the State),
    a "Dismissed" disposition means the government LOST — the opposite of the
    intuition for original writ petitions where dismissed=government won.

    Returns a dict with:
      side: "PETITIONER" | "RESPONDENT" | "BOTH" | "UNCLEAR"
      outcome: "GOVT_WON" | "GOVT_LOST" | "UNCLEAR"
      explanation: human-readable one-line summary
    """
    pet_is_govt = _party_is_government(petitioner)
    resp_is_govt = _party_is_government(respondent)

    if pet_is_govt and resp_is_govt:
        side = "BOTH"
    elif pet_is_govt:
        side = "PETITIONER"
    elif resp_is_govt:
        side = "RESPONDENT"
    else:
        side = "UNCLEAR"

    disp = (disposition or "").lower()
    win = (winning_party or "").lower()

    # Map disposition + side -> outcome
    # "Allowed" / "Partly Allowed" means the petitioner/appellant's prayer succeeded.
    # "Dismissed" / "Rejected" means the petitioner/appellant failed.
    pet_won = (
        "allowed" in disp or "granted" in disp
        or "petitioner" in win or "appellant" in win
    )
    resp_won = (
        "dismissed" in disp or "rejected" in disp or "quashed" not in disp and "respondent" in win
    )

    if side == "PETITIONER":
        outcome = "GOVT_WON" if pet_won else ("GOVT_LOST" if "dismissed" in disp or "rejected" in disp else "UNCLEAR")
    elif side == "RESPONDENT":
        outcome = "GOVT_WON" if ("dismissed" in disp or "rejected" in disp) else ("GOVT_LOST" if pet_won else "UNCLEAR")
    elif side == "BOTH":
        outcome = "UNCLEAR"
    else:
        # Fall back to winning_party_type only
        if "respondent" in win:
            outcome = "GOVT_WON_LIKELY"  # most cases have govt as respondent
        elif "petitioner" in win or "appellant" in win:
            outcome = "GOVT_LOST_LIKELY"
        else:
            outcome = "UNCLEAR"

    explanations = {
        ("PETITIONER", "GOVT_WON"): "Government was the petitioner/appellant and its prayer was granted.",
        ("PETITIONER", "GOVT_LOST"): "Government was the petitioner/appellant and its prayer was dismissed — the State LOST this case.",
        ("RESPONDENT", "GOVT_WON"): "Government was the respondent and the petition was dismissed — the State WON.",
        ("RESPONDENT", "GOVT_LOST"): "Government was the respondent and the petition was allowed — the State LOST.",
        ("BOTH", "UNCLEAR"): "Both sides include government entities (inter-departmental dispute).",
        ("UNCLEAR", "GOVT_WON_LIKELY"): "Could not identify government party from names; based on winning_party=Respondent the State likely won.",
        ("UNCLEAR", "GOVT_LOST_LIKELY"): "Could not identify government party from names; based on winning_party=Petitioner/Appellant the State likely lost.",
    }
    explanation = explanations.get(
        (side, outcome),
        f"Insufficient signal (side={side}, disposition={disposition!r}, winning_party={winning_party!r})."
    )

    return {"side": side, "outcome": outcome, "explanation": explanation}


def _determine_appeal_forum(court: str, bench: str = "", case_type: str = "") -> dict:
    """Determine the correct next appellate forum based on Indian court hierarchy."""
    court_lower = court.lower()
    bench_lower = bench.lower()
    case_type_lower = case_type.lower()

    if "supreme court" in court_lower:
        return COURT_HIERARCHY["supreme_court"]
    if "high court" in court_lower:
        # Division Bench indicators:
        # 1. Explicit "division" or "DB" in bench
        # 2. Case types that are always heard by Division Bench:
        #    MFA = Miscellaneous First Appeal, RSA = Regular Second Appeal,
        #    WA = Writ Appeal, ICA = Intra-Court Appeal, RFA = Regular First Appeal
        # 3. Multiple judges (2+ comma-separated names in bench)
        is_division_bench = (
            "division" in bench_lower or "db" in bench_lower
            or "writ appeal" in case_type_lower
            or any(ct in case_type_lower for ct in ["mfa", "rfa", "rsa", "wa ", "ica", "appeal", "mfa no"])
            or (bench and len([j for j in bench.split(",") if j.strip()]) >= 2)
        )
        if is_division_bench:
            return COURT_HIERARCHY["division_bench"]
        return COURT_HIERARCHY["single_judge"]
    if "tribunal" in court_lower:
        return COURT_HIERARCHY["tribunal"]
    if "district" in court_lower or "sessions" in court_lower:
        return COURT_HIERARCHY["district"]
    return COURT_HIERARCHY["subordinate"]


# ==============================================================================
# LLM Providers
# ==============================================================================

def _build_example_json(response_model) -> str:
    examples = {
        "Agent1Output": json.dumps({
            "precedents": [{"case_id": "X", "case_title": "A v. B", "relevance": "...", "key_holding": "...", "outcome": "APPEAL_DISMISSED", "applicability": "..."}],
            "overall_trend": "Precedents suggest courts generally dismiss such appeals...",
            "precedent_strength": "WEAK"
        }, indent=2),
        "Agent2Output": json.dumps({
            "pro_appeal_arguments": ["The court erred in..."], "pro_compliance_arguments": ["The order is well-reasoned..."],
            "strongest_appeal_ground": "...", "strongest_compliance_reason": "...", "balance_assessment": "COMPLIANCE_FAVORED"
        }, indent=2),
        "Agent3Output": json.dumps({
            "procedural_loopholes": ["..."], "contempt_risk_assessment": "...", "contempt_urgency": "MEDIUM",
            "limitation_analysis": "...", "financial_risk": "..."
        }, indent=2),
        "Agent4Output": json.dumps({
            "verdict": {"decision": "COMPLY", "appeal_to": "Supreme Court of India", "confidence": 0.75, "urgency": "HIGH"},
            "primary_reasoning": "...", "appeal_grounds": ["..."], "alternative_routes": ["..."],
            "action_plan": {"immediate_actions": ["..."], "financial_actions": ["..."]}, "risk_summary": "..."
        }, indent=2),
    }
    return examples.get(response_model.__name__, "{}")


def _call_llm_provider(prompt: str, response_model, system_prompt: str, is_agent4: bool = False) -> BaseModel:
    """Call NVIDIA NIM or OpenRouter API based on environment toggle."""
    use_openrouter = os.environ.get("USE_OPENROUTER", "False").lower() == "true"
    
    if use_openrouter:
        base_url = "https://openrouter.ai/api/v1"
        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        # Use the explicit V3 snapshot — the generic "deepseek-chat" slug points
        # to an older model that produces noticeably thinner reasoning.
        model = "deepseek/deepseek-r1" if is_agent4 else "deepseek/deepseek-chat-v3-0324"
        provider_name = "OpenRouter"
    else:
        base_url = getattr(settings, "NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
        api_key = getattr(settings, "NVIDIA_API_KEY", "")
        model = "qwen/qwen3-next-80b-a3b-thinking" if is_agent4 else "meta/llama-3.3-70b-instruct"
        provider_name = "NVIDIA"

    client = OpenAI(base_url=base_url, api_key=api_key)
    example_json = _build_example_json(response_model)
    messages = [
        {"role": "system", "content": f"{system_prompt}\n\nIMPORTANT: Respond ONLY with valid JSON. No explanation or markdown.\nFollow this structure:\n{example_json}"},
        {"role": "user", "content": prompt}
    ]
    for attempt in range(3):
        try:
            logger.info(f"[{provider_name}] Calling {model} for {response_model.__name__} (attempt {attempt+1}/3)")
            
            # Use extra body params for openrouter json mode support depending on model
            extra_params = {}
            if use_openrouter:
                # OpenRouter deepseek json support
                extra_params["response_format"] = {"type": "json_object"}
            else:
                extra_params["response_format"] = {"type": "json_object"}
                
            response = client.chat.completions.create(
                model=model, messages=messages, temperature=0.15,
                **extra_params
            )
            content = response.choices[0].message.content
            
            # Clean up thinking tokens if deepseek-r1 was used and returned them inside content
            if use_openrouter and is_agent4 and "</think>" in content:
                content = content.split("</think>")[-1].strip()
                
            # If the model surrounds JSON with ```json ... ```, strip it
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "").strip()
                
            logger.info(f"[{provider_name}] Response ({len(content)} chars): {content[:150]}...")
            return response_model.model_validate_json(content)
        except Exception as e:
            logger.warning(f"[{provider_name}] Attempt {attempt+1} failed: {e}")
            if attempt == 2: raise
            time.sleep(8 * (attempt + 1))


def _call_nvidia(prompt: str, response_model, system_prompt: str, model: str = "meta/llama-3.3-70b-instruct") -> BaseModel:
    """Legacy call function for single-agent pipeline."""
    return _call_llm_provider(prompt, response_model, system_prompt, is_agent4=(model == "qwen/qwen3-next-80b-a3b-thinking"))


def _call_synthesis(prompt: str, response_model, system_prompt: str) -> BaseModel:
    """Call synthesis agent."""
    return _call_llm_provider(prompt, response_model, system_prompt, is_agent4=True)


# ==============================================================================
# Build Case Context (shared across all agents)
# ==============================================================================

def _build_case_context(case_text: str, area_of_law: str, court: str,
                        disposition: str = "", winning_party: str = "",
                        case_type: str = "", bench: str = "",
                        petitioner: str = "", respondent: str = "",
                        issues: List[str] = None,
                        financial_implications: list = None,
                        operative_order_text: str = "") -> str:
    """Build a structured case summary that all agents receive."""
    appeal_info = _determine_appeal_forum(court, bench, case_type)
    govt_role = _determine_government_role(petitioner, respondent, winning_party, disposition, case_type)
    issues_text = "\n".join(f"  {i+1}. {iss}" for i, iss in enumerate(issues or []))

    # Surface explicit rupee/percentage figures as their own block so the agents
    # cannot claim "no financial exposure" when the operative order has numbers.
    fin_block = ""
    if financial_implications:
        if isinstance(financial_implications, dict):
            fin_lines = [f"  - {k}: {v}" for k, v in financial_implications.items() if v]
        else:
            fin_lines = [f"  - {str(f)}" for f in financial_implications if f]
        if fin_lines:
            fin_block = "\n=== EXTRACTED FINANCIAL FIGURES (verbatim from operative order) ===\n" + "\n".join(fin_lines) + "\n=== END FINANCIAL FIGURES ==="

    # Pull rupee amounts and percentages out of the operative order even if the
    # structured field is empty. Defends against the Math Trap.
    operative_numbers = []
    if operative_order_text:
        operative_numbers += re.findall(r'(?:₹|Rs\.?|INR)\s*[\d,]+(?:\.\d+)?(?:\s*(?:lakh|crore|lakhs|crores))?', operative_order_text)
        operative_numbers += re.findall(r'\d+(?:\.\d+)?\s*%\s*(?:deduction|developmental|interest|p\.?a\.?|per annum)?', operative_order_text)
    if operative_numbers:
        fin_block += "\n=== NUMBERS DETECTED IN OPERATIVE ORDER (do NOT claim 'no financial data') ===\n"
        fin_block += "\n".join(f"  - {n}" for n in operative_numbers[:30])
        fin_block += "\n=== END NUMBERS ==="

    return f"""=== CURRENT CASE DETAILS ===
Court: {court}
Bench: {bench or 'Not specified'}
Case Type: {case_type or 'Not specified'}
Area of Law: {area_of_law}
Petitioner: {petitioner or 'Not specified'}
Respondent: {respondent or 'Not specified'}

CURRENT DISPOSITION: {disposition or 'Unknown'}
WINNING PARTY: {winning_party or 'Unknown'}

═══ GOVERNMENT ROLE (AUTHORITATIVE — do NOT contradict) ═══
Government Side: {govt_role['side']}  (PETITIONER means State was the appellant/petitioner; RESPONDENT means State was the respondent)
Outcome for Government: {govt_role['outcome']}
Interpretation: {govt_role['explanation']}

CRITICAL: When Outcome = GOVT_LOST or GOVT_LOST_LIKELY:
  • The State LOST this case. Do NOT say "the government prevailed".
  • Apply COST-OF-FURTHER-LITIGATION calculus before recommending APPEAL.
When Outcome = GOVT_WON or GOVT_WON_LIKELY:
  • The State WON. Recommend COMPLY with high confidence. appeal_grounds MUST be [].
  • If the petition was simply dismissed, primary_reasoning should note that no
    affirmative directions exist against the State — there is nothing to "comply" with;
    the file may simply be closed.

CORRECT NEXT APPELLATE FORUM: {appeal_info['next']}
APPEAL TYPE: {appeal_info['appeal_type']}

LEGAL ISSUES:
{issues_text or '  Not specified'}
{fin_block}
CASE SUMMARY:
{case_text[:3000]}
=== END CASE DETAILS ==="""


# ==============================================================================
# The Single-Agent Deep Reasoning Pipeline
# ==============================================================================

def _run_single_agent_pipeline(
    case_id: str, case_context: str, appeal_info: dict, date_of_order: str,
    court_directions: list = None, operative_order_text: str = "", ratio_decidendi: str = "",
    precedents: list = None
) -> Dict[str, Any]:
    logger.info("Running Single Agent Recommendation Pipeline (DeepSeek V4 Pro)...")
    
    agent_sys = """You are the Chief Legal Advisor to the State Government Litigation Department (NyayaDrishti CCMS). 
You analyze court judgments where the State/Government is a party and recommend whether the State should APPEAL or COMPLY.

═══ PERSPECTIVE LOCK ═══
- You ALWAYS represent the GOVERNMENT DEPARTMENT (typically the respondent).
- Your goal: protect the public exchequer, minimize state liability, defend government policies.
- NEVER generate arguments that favor the private petitioner/appellant.
- Every argument you draft must pass this test: "Would a government lawyer actually say this in court to REDUCE the State's liability?"

═══ COURT HIERARCHY — READ THIS CAREFULLY ═══
Every case involves AT LEAST two courts:
1. THE LOWER COURT (Reference Court / Trial Court / Single Judge):
   - This court heard the case first
   - Its order was challenged by one of the parties

2. THIS COURT (the court whose judgment you are reading):
   - This court heard the appeal/challenge against the Lower Court
   - THIS is the order the government must now decide to APPEAL or COMPLY with

CRITICAL RULE: When you recommend APPEAL, your "appeal_grounds" must argue why THIS COURT's order was wrong. Do NOT attack the Lower Court using THIS Court's own logic — that is the PETITIONER's argument, not the government's.

═══ MATHEMATICAL REASONING GUARDRAILS ═══
When analyzing compensation/monetary cases, apply these rules EXACTLY:

DEDUCTIONS (e.g., developmental charges in land acquisition):
- A HIGHER deduction % = LOWER net payout by government = GOOD for government
- A LOWER deduction % = HIGHER net payout by government = BAD for government
- Therefore: The government should NEVER argue that a deduction is "excessive" or "too high"
- Government's position: deductions should be HIGHER (e.g., "The court erred in applying only 30% deduction; 50-60% is warranted given the infrastructure costs")

ENHANCEMENT OF COMPENSATION:
- Higher market value = MORE money government pays = BAD for government
- Lower market value = LESS money government pays = GOOD for government
- Government's position: market value should be LOWER

INTEREST RATES:
- Higher interest rate on compensation = MORE government liability = BAD for government
- Lower interest rate = LESS government liability = GOOD for government

Before writing any argument about money, ask yourself: "Does this argument, if accepted by the court, result in the government paying MORE or LESS?" If MORE, do NOT make that argument.

═══ ANTI-PARROT RULE (CRITICAL — most common failure mode) ═══
When the government LOST, the court's "Ratio Decidendi" contains the legal reasoning the court ACCEPTED FROM THE WINNING PRIVATE PARTY. These are exactly the arguments the government must DISPROVE — not repeat.

Before adding any appeal_ground, run this check:
  "Did THIS court rely on this reasoning to rule against the government?"
  - If YES → this argument helped the OTHER side win. FLIP it. Your ground must explain why this reasoning is wrong, why the court should not have accepted it.
  - If NO → it may be a fresh ground.

Concrete examples of PARROTING (DO NOT do this):
  ❌ "The court erred in relying on consent award without consent" — this is what the WINNING party argued; the court ACCEPTED it. The government's ground would be the OPPOSITE: "The consent award was valid comparable evidence and the HC wrongly disregarded it."
  ❌ "Failure to consider appellants' evidence" — this is the winners' argument; flip to: "HC over-weighted a single exemplar sale deed when consent-award and LAO valuation provided more reliable contemporaneous benchmarks."

Format for a proper government appeal ground:
  "The court erred in [accepting argument X / applying principle Y / ignoring fact Z] because [counter-reason grounded in statute or prior SC ruling]."

═══ HALLUCINATION GUARDRAILS ═══
- Do NOT cite any constitutional article (Article 14, 19, 21, 25, 26, 300A, etc.) UNLESS the verbatim judgment text in front of you cites that article. If unsure, leave it out.
- Do NOT cite case names or citations not present in the extracted ratio decidendi.
- If you don't know a specific statutory section number, omit it rather than guessing.
- "contempt_risk" / "contempt_urgency" must be derived from explicit compliance directives with deadlines or "failing which" language in the court_directions. If no such language exists, contempt risk = LOW. Do not assign MEDIUM/HIGH on vibes.

═══ APPEAL_GROUNDS FIELD RULES ═══
- If your verdict is APPEAL: populate "appeal_grounds" with 2-4 specific legal grounds arguing why THIS COURT's order was wrong. Each ground must pass the government-perspective test AND the anti-parrot check above.
- If your verdict is COMPLY: set "appeal_grounds" to an EMPTY LIST []. Do NOT generate appeal arguments when recommending compliance. Instead, explain your reasoning in "primary_reasoning".

═══ FINANCIAL COST-OF-DELAY ANALYSIS ═══
For ANY monetary judgment against the government:
1. Estimate the statutory or commercial interest accumulating during a 3-5 year appeal process.
2. Compare: the potential savings if the government wins the appeal vs. the guaranteed accumulated interest cost if it loses.
3. If the interest cost significantly exceeds potential savings, or the principal amount is small (e.g., under ₹50 lakh), or appellate success probability is low, recommend COMPLY. Appeal is not the default — it must be JUSTIFIED by both legal merit and financial calculus.

═══ DECISION FRAMEWORK ═══
1. If THIS Court ruled AGAINST the government (petitioner's appeal allowed):
   → Government LOST. Weigh appeal vs compliance carefully.
   → Consider: Are there genuine legal errors by THIS Court?
   → Consider: Financial exposure vs cost of further litigation.

2. If THIS Court ruled FOR the government (petition dismissed):
   → Government WON. Recommend COMPLY with HIGH confidence.
   → Set appeal_grounds to empty list [].

3. APPEAL FORUM — Use the correct next court:
   - Single Judge HC → Division Bench of same HC
   - Division Bench HC → Supreme Court (SLP under Art. 136)
   - Supreme Court → Review/Curative Petition"""

    directions_text = json.dumps(court_directions, indent=2) if court_directions else "None specified"
    
    agent_prompt = f"""{case_context}

=== EXTRACTED JUDGMENT DETAILS ===
Operative Order:
{operative_order_text or 'Not available'}

Court Directions (Compliance Directives):
{directions_text}

⚠️ COURT'S REASONING (READ AS HOSTILE WITNESS) ⚠️
The text below is the legal reasoning THIS COURT used. If the government LOST this case,
every line below is something the government must DISPROVE on appeal — not parrot.
Treat each sentence as: "the OTHER side persuaded the court of this; my job is to argue against it".

{ratio_decidendi or 'Not available'}
=== END EXTRACTED DETAILS ===

Make your final recommendation. Two reminders:
  1. Apply the ANTI-PARROT RULE — do not list the court's accepted reasoning as your appeal grounds.
  2. APPEAL is not automatic. Run the cost-of-delay math: if the principal at stake is small,
     or interest over a 3-5 year appeal would exceed potential savings, recommend COMPLY honestly.
     Use the CORRECT NEXT APPELLATE FORUM from the case details if you do recommend appeal."""

    try:
        agent_out = _call_nvidia(agent_prompt, Agent4Output, agent_sys, model="qwen/qwen3-next-80b-a3b-thinking")
    except Exception as e:
        logger.warning(f"Qwen 80B Thinking failed, falling back to Mixtral 8x22B: {e}")
        agent_out = _call_nvidia(agent_prompt, Agent4Output, agent_sys, model="mistralai/mixtral-8x22b-instruct-v0.1")

    appeal_days = 90 if "supreme" in appeal_info["next"].lower() else 30
    
    from datetime import date, datetime, timedelta
    import uuid
    
    base_date = date.today()
    if date_of_order:
        if isinstance(date_of_order, (date, datetime)):
            base_date = date_of_order.date() if isinstance(date_of_order, datetime) else date_of_order
        else:
            try:
                if "T" in str(date_of_order):
                    base_date = date.fromisoformat(str(date_of_order).split("T")[0])
                else:
                    base_date = date.fromisoformat(str(date_of_order))
            except ValueError:
                pass
            
    deadline_date = base_date + timedelta(days=appeal_days)
    deadline = deadline_date.isoformat()
    days_remaining = (deadline_date - date.today()).days

    # Deterministic contempt override — single-agent path also benefits from
    # ignoring the LLM's tendency to hallucinate contempt risk.
    from apps.action_plans.services.risk_classifier import classify_contempt_risk
    contempt_input = (operative_order_text or "") + " " + json.dumps(court_directions or [])
    deterministic_contempt = classify_contempt_risk(contempt_input).upper()

    return {
        "recommendation_id": str(uuid.uuid4()),
        "case_id": case_id,
        "status": "COMPLETED",
        "verdict": {
            "decision": agent_out.verdict.decision,
            # Override LLM's appeal_to with deterministic court-hierarchy result.
            "appeal_to": appeal_info["next"],
            "appeal_type": appeal_info["appeal_type"],
            "confidence": agent_out.verdict.confidence,
            "urgency": "HIGH" if deterministic_contempt == "HIGH" else agent_out.verdict.urgency,
            "limitation_deadline": deadline,
            "days_remaining": days_remaining,
        },
        "statistical_basis": {
            "similar_cases_analyzed": len(precedents) if precedents else 0,
            "government_appeal_win_rate": 0,
            "dismissed_rate": 0,
            "total_cases_in_corpus": 0,
            "financial_exposure_if_comply": 0,
        },
        "primary_reasoning": agent_out.primary_reasoning,
        "appeal_grounds": agent_out.appeal_grounds,
        "alternative_routes": agent_out.alternative_routes,
        "action_plan": agent_out.action_plan.model_dump(),
        "risk_summary": agent_out.risk_summary,
        "agent_outputs": {
            "precedent_strength": "MODERATE" if precedents else "WEAK",
            "overall_trend": "Precedents extracted for reference via semantic search." if precedents else "Precedent analysis currently disabled for focused reasoning.",
            "precedents": precedents if precedents else [],
            "rag_precedents": precedents if precedents else [],
            "balance_assessment": "BALANCED",
            "strongest_appeal_ground": "",
            "strongest_compliance_reason": "",
            "pro_appeal_count": 0,
            "pro_compliance_count": 0,
            # Deterministic contempt — overrides any LLM hallucination
            "contempt_urgency": deterministic_contempt,
            "contempt_risk_assessment": f"Deterministic classifier output: {deterministic_contempt}",
            "limitation_analysis": "",
            "financial_risk": "",
            "procedural_loopholes": [],
        },
    }

# ==============================================================================
# The 4-Agent Pipeline
# ==============================================================================

def generate_recommendation(
    case_id: str, case_text: str, area_of_law: str, court: str,
    disposition: str = "", winning_party: str = "",
    case_type: str = "", bench: str = "",
    petitioner: str = "", respondent: str = "",
    issues: List[str] = None,
    date_of_order: str = "",
    court_directions: List[dict] = None,
    operative_order_text: str = "",
    ratio_decidendi: str = "",
    financial_implications=None,
    use_rag: bool = True
) -> Dict[str, Any]:
    """Main entry point for the 4-agent recommendation pipeline."""
    logger.info(f"Starting recommendation pipeline V2 for case {case_id}")

    # Build shared case context
    case_context = _build_case_context(
        case_text, area_of_law, court, disposition, winning_party,
        case_type, bench, petitioner, respondent, issues,
        financial_implications=financial_implications,
        operative_order_text=operative_order_text,
    )
    appeal_info = _determine_appeal_forum(court, bench, case_type)
    govt_role = _determine_government_role(petitioner, respondent, winning_party, disposition, case_type)

    # ---------------------------------------------------------
    # Stage 1: RAG Retrieval (with dedup + score threshold)
    # Always run this to fetch precedents, even for single-agent pipeline
    # ---------------------------------------------------------
    rag = HybridRAGEngine()
    
    domain_key = get_domain_key(area_of_law)
    
    case_context_dict = {
        "ratio_decidendi": ratio_decidendi,
        "operative_order_text": operative_order_text,
        "case_text": case_text,
        "issues": issues,
        "area_of_law": area_of_law,
        "disposition": disposition
    }
    raw_chunks = rag.retrieve_for_case(case_context_dict, domain_key=domain_key, top_k=10, filters=None)

    # Group by case_id. We rely entirely on cosine ranking + top-K cap.
    # InLegalBERT cross-court cosine scores are tight (typically 0.55-0.75),
    # so any absolute or relative floor risks dropping everything. The trade-off:
    # for cases with no good matches in the SC corpus we show mediocre matches
    # rather than nothing, but the user can see scores and judge for themselves.
    grouped_cases = {}
    score_sample = [round(c.get('score', 0), 3) for c in (raw_chunks or [])[:10]]
    logger.warning(f"RAG raw_chunks: {len(raw_chunks or [])} | top-10 scores: {score_sample} | domain: {domain_key}")

    for c in (raw_chunks or []):
        meta = c.get('metadata', {}) or {}
        cid = meta.get('case_id') or meta.get('title') or ''
        score = c.get('score', 0)
        try:
            chunk_idx = int(meta.get('chunk_index', 0))
        except (TypeError, ValueError):
            chunk_idx = 0

        if cid not in grouped_cases:
            grouped_cases[cid] = {
                "metadata": meta,
                "score": score,
                "texts": [],
                "best_chunk_index": chunk_idx,
            }
        else:
            # If we found a better-scoring chunk for this case, anchor on that index
            if score > grouped_cases[cid]["score"]:
                grouped_cases[cid]["score"] = score
                grouped_cases[cid]["best_chunk_index"] = chunk_idx

        if len(grouped_cases[cid]["texts"]) < 3:
            grouped_cases[cid]["texts"].append(c.get('text', ''))

    # Flatten and sort by highest score
    retrieved_chunks = list(grouped_cases.values())
    retrieved_chunks.sort(key=lambda x: x["score"], reverse=True)
    retrieved_chunks = retrieved_chunks[:8]  # Cap at 8 unique cases
    logger.info(f"RAG: {len(raw_chunks or [])} raw → {len(retrieved_chunks)} unique grouped precedents")

    # Stitch neighbor chunks around the best-scoring chunk for each case so the
    # LLM and the frontend see a paragraph-level view, not a half-cut sentence.
    for entry in retrieved_chunks:
        cid = entry["metadata"].get("case_id")
        idx = entry.get("best_chunk_index", 0)
        stitched = rag.stitch_precedent_text(cid, idx, max_chars=1800) if cid else ""
        entry["stitched_text"] = stitched or " ".join(entry["texts"])[:1800]

    extracted_precedents = []
    for c in retrieved_chunks:
        sim_score = c.get('score', 0)
        # Bucket relevance for frontend display
        if sim_score >= 0.85:
            relevance_label = "High"
        elif sim_score >= 0.78:
            relevance_label = "Moderate"
        else:
            relevance_label = "Low"
        
        decision_date = str(c['metadata'].get('decision_date', ''))
        raw_year = decision_date[:4] if decision_date else ''
        valid_year = raw_year if (raw_year.isdigit() and 1900 <= int(raw_year) <= 2100) else ''
        stitched = c.get("stitched_text") or " ".join(c.get("texts", []))
        extracted_precedents.append({
            "case_id": str(c['metadata'].get('case_id', '')),
            "case_title": str(c['metadata'].get('title', 'Unknown')),
            "relevance": relevance_label,
            "similarity_score": round(sim_score, 4),
            # Longer paragraph window from neighbor chunks rather than 500-char half-cut.
            "key_holding": stitched[:1500] + ("..." if len(stitched) > 1500 else ""),
            "outcome": str(c['metadata'].get('disposal_nature', 'UNKNOWN')),
            "applicability": f"Cosine similarity: {sim_score:.2%} via InLegalBERT semantic search",
            "court": str(c['metadata'].get('court', 'Unknown')),
            "year": valid_year,
            "petitioner": str(c['metadata'].get('petitioner', '')),
            "respondent": str(c['metadata'].get('respondent', '')),
        })

    if not use_rag:
        return _run_single_agent_pipeline(
            case_id=case_id, case_context=case_context, appeal_info=appeal_info,
            date_of_order=date_of_order, court_directions=court_directions,
            operative_order_text=operative_order_text, ratio_decidendi=ratio_decidendi,
            precedents=extracted_precedents
        )

    if not retrieved_chunks:
        logger.warning("No strong precedents found.")
        stuffed_context = "No direct precedents found in the database."
    else:
        stuffed_context = "\n\n".join([
            f"PRECEDENT {i+1}: {c['metadata'].get('title', 'Unknown')}\n"
            f"Outcome: {c['metadata'].get('disposal_nature', 'Unknown')} | "
            f"Court: {c['metadata'].get('court', 'Unknown')} | "
            f"Domain: {c['metadata'].get('area_of_law', 'Unknown')}\n"
            # Paragraph-level window from neighbor chunks.
            f"Key Text: {(c.get('stitched_text') or ' '.join(c.get('texts', [])))[:1800]}"
            for i, c in enumerate(retrieved_chunks)
        ])

    # ---------------------------------------------------------
    # Stage 2: DuckDB Win Rate Stats (fixed path)
    # ---------------------------------------------------------
    parquet_dir = None
    import os
    for candidate in [
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "parquet"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "apps", "data", "parquet"),
    ]:
        if os.path.isdir(candidate):
            parquet_dir = candidate
            break

    store = DuckDBStore(data_dir=parquet_dir) if parquet_dir else DuckDBStore()
    # Try with area_of_law filter first, then without
    stats = store.compute_win_rates(area_of_law=area_of_law, court="")
    if stats.get("error") or stats.get("total_cases_analyzed", 0) == 0:
        # Retry without area_of_law filter to get overall corpus stats
        stats = store.compute_win_rates(area_of_law="", court="")
    logger.info(f"DuckDB stats: {stats}")
    stats_text = json.dumps(stats, indent=2) if not stats.get("error") else "No statistical data available."

    # ---------------------------------------------------------
    # AGENT 1: Precedent Researcher
    # ---------------------------------------------------------
    logger.info("Running Agent 1 (Precedent Researcher)...")
    agent1_sys_base = """You are a Senior Legal Researcher at the Supreme Court of India with 20+ years of experience analyzing case precedents.

YOUR TASK: Analyze the retrieved precedent cases and determine how they relate to the current case.

INSTRUCTIONS:
1. For each precedent, assess its RELEVANCE to the current case (consider: same area of law, similar facts, similar legal issues, same court hierarchy level).
2. Identify the KEY HOLDING — what did the court decide and why?
3. Determine the OUTCOME — was the appeal allowed or dismissed?
4. Assess APPLICABILITY — does this precedent SUPPORT or UNDERMINE the current case's position?
5. Provide an OVERALL TREND — what do the precedents collectively suggest about the likely outcome?
6. Rate PRECEDENT STRENGTH as STRONG (>70% precedents support one side), MODERATE (50-70%), or WEAK (<50% or insufficient data).

IMPORTANT: If the current case was DISMISSED by the court, precedents showing other DISMISSED cases WEAKEN the appeal case. Precedents showing ALLOWED appeals STRENGTHEN it."""
    
    agent1_sys = build_agent_prompt(1, domain_key, agent1_sys_base)

    agent1_prompt = f"""{case_context}

=== RETRIEVED PRECEDENT CASES FROM DATABASE ===
{stuffed_context}
=== END PRECEDENTS ===

Analyze each precedent's relevance and provide your overall assessment."""

    agent1_out = _call_nvidia(agent1_prompt, Agent1Output, agent1_sys)

    # ---------------------------------------------------------
    # AGENT 2: Argument Mapper
    # ---------------------------------------------------------
    logger.info("Running Agent 2 (Argument Mapper)...")
    agent2_sys_base = """You are a Senior Government Advocate advising the Karnataka State Government on whether to appeal or comply with a court order.

YOUR TASK: Generate balanced pro-appeal and pro-compliance arguments — ALWAYS from the GOVERNMENT'S perspective.

INSTRUCTIONS:
1. Generate 3-5 SPECIFIC pro-appeal arguments (only those a government lawyer would make to REDUCE state liability or DEFEND state policy).
2. Generate 3-5 SPECIFIC pro-compliance arguments.
3. Arguments must be GROUNDED in the case facts — no generic statements.
4. Consider the DISPOSITION — if the case was DISMISSED (government won), compliance is the answer; appeal grounds should be empty or minimal.
5. Consider the PRECEDENT ANALYSIS from Agent 1.
6. Identify the SINGLE STRONGEST ground for each side.
7. Give a BALANCE ASSESSMENT: APPEAL_FAVORED, COMPLIANCE_FAVORED, or BALANCED.

ANTI-PARROT RULE (most common failure):
- When the government LOST, the court's ratio_decidendi IS the winning party's argument. NEVER echo it as a pro-appeal ground.
- Bad pro-appeal: "court erred in applying the consent award without consent" (this is the WINNER's argument)
- Good pro-appeal: "the consent award was reliable comparable evidence and the HC wrongly disregarded it in favor of a single small-plot exemplar"

HALLUCINATION RULE:
- Do NOT cite constitutional articles (14, 19, 21, 25, 26, 300A) unless the verbatim judgment text cites them.
- Do NOT invent case citations.

BALANCE RULE:
- Appeal is NOT the default. If the financial exposure is modest (under ₹50 lakh principal) or the legal error is debatable, COMPLIANCE_FAVORED is the honest call.
- Don't add weight to appeal just because constitutional words appear — only weight constitutional grounds the JUDGMENT itself raises."""

    agent2_sys = build_agent_prompt(2, domain_key, agent2_sys_base)
    
    financial_implications = [str(d) for d in (court_directions or [])]
    math_validation = validate_financial_math(financial_implications, domain_key)
    math_validation_text = f"\n=== MATH VALIDATION REPORT ===\n{math_validation['summary']}\n=== END MATH VALIDATION ===\n"

    agent2_prompt = f"""{case_context}
{math_validation_text}
=== PRECEDENT ANALYSIS FROM AGENT 1 ===
{agent1_out.model_dump_json(indent=2)}
=== END PRECEDENT ANALYSIS ===

=== HISTORICAL WIN RATE STATISTICS ===
{stats_text}
=== END STATISTICS ===

Generate balanced arguments for both sides."""

    agent2_out = _call_nvidia(agent2_prompt, Agent2Output, agent2_sys)

    # ---------------------------------------------------------
    # AGENT 3: Risk Auditor
    # ---------------------------------------------------------
    logger.info("Running Agent 3 (Risk Auditor)...")
    agent3_sys_base = """You are a Legal Risk Auditor specializing in Indian government litigation and contempt proceedings.

YOUR TASK: Identify procedural risks, contempt exposure, and limitation issues.

INSTRUCTIONS:
1. PROCEDURAL LOOPHOLES: Identify any procedural defects that could affect the case (limitation, jurisdiction, locus standi, maintainability, non-joinder).
2. CONTEMPT RISK — HARD RULES (do not hallucinate):
   - HIGH only if the order has an explicit deadline AND "failing which" / "coercive steps" / "personal appearance" / "punishable as contempt" language.
   - MEDIUM only if there is an explicit deadline for a compliance action but no warning language.
   - LOW in ALL other cases — including pure compensation/declaratory judgments where no act-by-X-date is ordered.
   - If court_directions is empty or contains only administrative phrases like "modified award shall be drawn", contempt_urgency = LOW.
3. LIMITATION ANALYSIS: Compute appeal limitation per Indian law:
   - High Court to Supreme Court (SLP): 90 days from the date of the order
   - Single Judge to Division Bench: 30 days
   - District Court to High Court: 90 days
4. FINANCIAL RISK: Assess costs, penalties, and financial exposure based on the actual figures in court_directions / operative_order. Do not invent numbers.

CRITICAL: Base contempt_urgency strictly on the keywords above. Do NOT assign MEDIUM/HIGH on intuition — only when the specified language is present in the directives."""

    agent3_sys = build_agent_prompt(3, domain_key, agent3_sys_base)

    agent3_prompt = f"""{case_context}
{math_validation_text}
=== ARGUMENT ANALYSIS FROM AGENT 2 ===
Balance Assessment: {agent2_out.balance_assessment}
Strongest Appeal Ground: {agent2_out.strongest_appeal_ground}
Strongest Compliance Reason: {agent2_out.strongest_compliance_reason}
=== END ARGUMENT ANALYSIS ===

Assess all risks and limitations."""

    agent3_out = _call_nvidia(agent3_prompt, Agent3Output, agent3_sys)

    # ---------------------------------------------------------
    # AGENT 4: Chief Legal Advisor (NVIDIA Llama 3.3 70B)
    # ---------------------------------------------------------
    logger.info("Running Agent 4 (Chief Legal Advisor — NVIDIA Llama 3.3 70B)...")
    agent4_sys_base = """You are the Chief Legal Advisor to the Karnataka State Government, responsible for the FINAL decision on whether to APPEAL or COMPLY with a court order. You represent ONLY the government's interest.

YOUR TASK: Synthesize ALL inputs from the previous 3 agents and make a definitive recommendation.

ANTI-PARROT RULE (CRITICAL):
- The "Ratio Decidendi" in the case details is the court's reasoning. When the government LOST, that reasoning IS the WINNING private party's argument that the court accepted.
- Your appeal_grounds MUST argue AGAINST that reasoning, never repeat it.
- Before writing each ground, ask: "Did the court ACCEPT this argument to rule against the government?" If yes, FLIP it.

HALLUCINATION GUARDRAILS:
- Do NOT cite any constitutional article (Article 14, 19, 21, 25, 26, 300A) unless the judgment text in front of you cites that article.
- Do NOT invent case names, citation numbers, or statutory section numbers.
- If a piece of information is not in the inputs, omit it rather than guess.

DECISION FRAMEWORK:

1. IF disposition is DISMISSED / petition rejected (government WON):
   → Recommend COMPLY with confidence 0.85+
   → appeal_grounds = [] (empty list)
   → primary_reasoning explains why no further action is needed

2. IF disposition is ALLOWED / petitioner won (government LOST):
   → Run the FINANCIAL CALCULUS first:
     • Estimate principal exposure from the operative order
     • Estimate interest accumulation over a 3-5 year appeal (typically 6-9% p.a.)
     • Compare to: (potential savings × win probability)
   → APPEAL only if BOTH conditions hold:
     a) A specific identifiable LEGAL ERROR exists (not just disagreement with the outcome)
     b) Financial calculus shows appeal-savings > interest-cost+litigation-cost
   → Otherwise COMPLY honestly. Appeal is NOT a default.

3. APPEAL is JUSTIFIED:
   → Confidence: 0.75-0.90 if precedents support, math is clear, and a real error exists
   → 0.55-0.75 if the legal ground is real but uncertain
   → Never claim >0.90 unless the error is undeniable and SC precedent is directly on point

4. COMPLY is JUSTIFIED:
   → Confidence: 0.80-0.95 if government won, OR financial exposure is small (under ₹50 lakh principal)
   → 0.60-0.80 if mixed signals
   → Higher confidence is APPROPRIATE for clear-cut compliance cases; do not hedge artificially.

5. APPEAL FORUM — use the CORRECT NEXT APPELLATE FORUM from case details:
   - Single Judge HC → Division Bench of same HC
   - Division Bench HC → Supreme Court (SLP under Art. 136)
   - Supreme Court → Review / Curative Petition
   NEVER recommend appealing a Division Bench order back to "High Court".

6. CONTEMPT URGENCY (use Agent 3's deterministic assessment — do not override):
   - LOW unless directive has explicit deadline + "failing which" / "coercive steps" / "punishable as contempt" language.

7. PRIMARY REASONING: 3-5 sentences. Reference the financial calculus and the specific legal error (or absence thereof). State explicitly whether the government won or lost.

8. ACTION PLAN: specific, dated steps for the nodal officer. No generic advice."""

    agent4_sys = build_agent_prompt(4, domain_key, agent4_sys_base)

    # Deterministic contempt assessment from the actual order text — used to override
    # the LLM's tendency to hallucinate MEDIUM/HIGH on cases with no contempt language.
    from apps.action_plans.services.risk_classifier import classify_contempt_risk
    contempt_input = (operative_order_text or "") + " " + json.dumps(court_directions or [])
    deterministic_contempt = classify_contempt_risk(contempt_input).upper()
    logger.info(f"Deterministic contempt classifier: {deterministic_contempt} (overrides LLM)")

    agent4_prompt = f"""{case_context}
{math_validation_text}

⚠️ COURT'S RATIO DECIDENDI — TREAT AS HOSTILE WITNESS ⚠️
The text below is what THIS court reasoned. If the government LOST, every line is what the
OTHER side persuaded the court of. Your job is to DISPROVE this reasoning, not echo it.

{ratio_decidendi or 'Not available'}
=== END RATIO ===

=== AGENT 1: PRECEDENT RESEARCH ===
Overall Trend: {agent1_out.overall_trend}
Precedent Strength: {agent1_out.precedent_strength}
Key Precedents: {json.dumps([{"case": p.case_title, "outcome": p.outcome, "applicability": p.applicability} for p in agent1_out.precedents[:5]], indent=2)}
=== END AGENT 1 ===

=== AGENT 2: ARGUMENT ANALYSIS ===
Balance Assessment: {agent2_out.balance_assessment}
Strongest Appeal Ground: {agent2_out.strongest_appeal_ground}
Strongest Compliance Reason: {agent2_out.strongest_compliance_reason}
Pro-Appeal Arguments: {json.dumps(agent2_out.pro_appeal_arguments, indent=2)}
Pro-Compliance Arguments: {json.dumps(agent2_out.pro_compliance_arguments, indent=2)}
=== END AGENT 2 ===

=== AGENT 3: RISK ASSESSMENT ===
Contempt Risk (LLM): {agent3_out.contempt_urgency}
Contempt Risk (Deterministic from text — authoritative): {deterministic_contempt}
Limitation Analysis: {agent3_out.limitation_analysis}
Financial Risk: {agent3_out.financial_risk}
Procedural Issues: {json.dumps(agent3_out.procedural_loopholes, indent=2)}
=== END AGENT 3 ===

=== HISTORICAL STATISTICS ===
{stats_text}
=== END STATISTICS ===

Make your final recommendation following the DECISION FRAMEWORK and ANTI-PARROT rule.
Reminders:
  • Use the CORRECT NEXT APPELLATE FORUM from case details (never appeal a DB order back to HC).
  • Appeal is NOT the default — run the financial calculus honestly. Small exposure → COMPLY.
  • Appeal grounds must DISPROVE the court's ratio, not repeat it."""

    agent4_out = _call_synthesis(agent4_prompt, Agent4Output, agent4_sys)

    # ---------------------------------------------------------
    # Limitation Deadline Calculation
    # ---------------------------------------------------------
    appeal_days = 90 if "supreme" in appeal_info["next"].lower() else 30
    
    # Base deadline off the judgment date if available
    base_date = date.today()
    if date_of_order:
        if isinstance(date_of_order, (date, datetime)):
            base_date = date_of_order.date() if isinstance(date_of_order, datetime) else date_of_order
        else:
            try:
                # Try to parse ISO format first, or basic string
                if "T" in str(date_of_order):
                    base_date = date.fromisoformat(str(date_of_order).split("T")[0])
                else:
                    base_date = date.fromisoformat(str(date_of_order))
            except ValueError:
                pass # fallback to today if parsing fails
            
    deadline_date = base_date + timedelta(days=appeal_days)
    deadline = deadline_date.isoformat()
    
    # Calculate days remaining relative to today
    days_remaining = (deadline_date - date.today()).days

    # ---------------------------------------------------------
    # Final Assembly
    # ---------------------------------------------------------
    # ALWAYS use the deterministic forum from court hierarchy — the LLM
    # routinely writes "High Court" when the answer is "Division Bench of the
    # same High Court" or "Supreme Court of India". Override LLM here.
    forced_appeal_to = appeal_info["next"]
    if agent4_out.verdict.decision == "COMPLY":
        # When complying, "appeal_to" is informational only — still surface the
        # forum the State would use if it later changes course.
        pass

    final_json = {
        "recommendation_id": str(uuid.uuid4()),
        "case_id": case_id,
        "status": "COMPLETED",
        "verdict": {
            "decision": agent4_out.verdict.decision,
            "appeal_to": forced_appeal_to,
            "appeal_type": appeal_info["appeal_type"],
            "confidence": agent4_out.verdict.confidence,
            "urgency": agent4_out.verdict.urgency,
            "limitation_deadline": deadline,
            "days_remaining": days_remaining,
            "government_role": govt_role,
        },
        "statistical_basis": {
            "similar_cases_analyzed": len(retrieved_chunks),
            "government_appeal_win_rate": stats.get("allowed_rate", 0),
            "dismissed_rate": stats.get("dismissed_rate", 0),
            "total_cases_in_corpus": stats.get("total_cases_analyzed", 0),
            "financial_exposure_if_comply": 0,
        },
        "primary_reasoning": agent4_out.primary_reasoning,
        "appeal_grounds": agent4_out.appeal_grounds,
        "alternative_routes": agent4_out.alternative_routes,
        "action_plan": agent4_out.action_plan.model_dump(),
        "risk_summary": agent4_out.risk_summary,
        "agent_outputs": {
            "precedent_strength": agent1_out.precedent_strength,
            "overall_trend": agent1_out.overall_trend,
            "precedents": [p.model_dump() for p in agent1_out.precedents],
            "rag_precedents": extracted_precedents,
            "balance_assessment": agent2_out.balance_assessment,
            "strongest_appeal_ground": agent2_out.strongest_appeal_ground,
            "strongest_compliance_reason": agent2_out.strongest_compliance_reason,
            "pro_appeal_count": len(agent2_out.pro_appeal_arguments),
            "pro_compliance_count": len(agent2_out.pro_compliance_arguments),
            # contempt_urgency: trust the deterministic classifier over the LLM
            "contempt_urgency": deterministic_contempt,
            "contempt_urgency_llm": agent3_out.contempt_urgency,
            "contempt_risk_assessment": agent3_out.contempt_risk_assessment,
            "limitation_analysis": agent3_out.limitation_analysis,
            "financial_risk": agent3_out.financial_risk,
            "procedural_loopholes": agent3_out.procedural_loopholes,
        },
    }

    # Override the verdict's urgency with deterministic contempt if higher
    # (Agent 4's urgency reflects limitation, but contempt should escalate it)
    if deterministic_contempt == "HIGH" and final_json["verdict"]["urgency"] != "HIGH":
        final_json["verdict"]["urgency"] = "HIGH"

    logger.info("Recommendation pipeline V2 complete.")
    return final_json
