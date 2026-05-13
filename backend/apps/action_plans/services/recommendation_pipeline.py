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
        model = "deepseek/deepseek-r1" if is_agent4 else "deepseek/deepseek-chat"
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
                        issues: List[str] = None) -> str:
    """Build a structured case summary that all agents receive."""
    appeal_info = _determine_appeal_forum(court, bench, case_type)
    issues_text = "\n".join(f"  {i+1}. {iss}" for i, iss in enumerate(issues or []))

    return f"""=== CURRENT CASE DETAILS ===
Court: {court}
Bench: {bench or 'Not specified'}
Case Type: {case_type or 'Not specified'}
Area of Law: {area_of_law}
Petitioner: {petitioner or 'Not specified'}
Respondent: {respondent or 'Not specified'}

CURRENT DISPOSITION: {disposition or 'Unknown'}
WINNING PARTY: {winning_party or 'Unknown'}

CORRECT NEXT APPELLATE FORUM: {appeal_info['next']}
APPEAL TYPE: {appeal_info['appeal_type']}

LEGAL ISSUES:
{issues_text or '  Not specified'}

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

═══ APPEAL_GROUNDS FIELD RULES ═══
- If your verdict is APPEAL: populate "appeal_grounds" with 2-4 specific legal grounds arguing why THIS COURT's order was wrong. Each ground must pass the government-perspective test above.
- If your verdict is COMPLY: set "appeal_grounds" to an EMPTY LIST []. Do NOT generate appeal arguments when recommending compliance. Instead, explain your reasoning in "primary_reasoning".

═══ FINANCIAL COST-OF-DELAY ANALYSIS ═══
For ANY monetary judgment against the government:
1. Estimate the statutory or commercial interest accumulating during a 3-5 year appeal process.
2. Compare: the potential savings if the government wins the appeal vs. the guaranteed accumulated interest cost if it loses.
3. If the interest cost significantly exceeds potential savings or the principal amount is small, strongly recommend COMPLY.

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

Ratio Decidendi (Court's Reasoning):
{ratio_decidendi or 'Not available'}
=== END EXTRACTED DETAILS ===

Make your final recommendation following the financial cost-of-delay rules and the court hierarchy disambiguation. Remember: use the CORRECT NEXT APPELLATE FORUM from the case details."""

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

    return {
        "recommendation_id": str(uuid.uuid4()),
        "case_id": case_id,
        "status": "COMPLETED",
        "verdict": {
            "decision": agent_out.verdict.decision,
            "appeal_to": agent_out.verdict.appeal_to,
            "confidence": agent_out.verdict.confidence,
            "urgency": agent_out.verdict.urgency,
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
            "contempt_urgency": agent_out.verdict.urgency,
            "contempt_risk_assessment": "",
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
    use_rag: bool = True
) -> Dict[str, Any]:
    """Main entry point for the 4-agent recommendation pipeline."""
    logger.info(f"Starting recommendation pipeline V2 for case {case_id}")

    # Build shared case context
    case_context = _build_case_context(
        case_text, area_of_law, court, disposition, winning_party,
        case_type, bench, petitioner, respondent, issues
    )
    appeal_info = _determine_appeal_forum(court, bench, case_type)

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

    # Group by case_id to provide multiple chunks per case (broader context)
    grouped_cases = {}
    from apps.action_plans.services.domain_prompts import RAG_THRESHOLDS
    rag_threshold = RAG_THRESHOLDS.get(domain_key, 0.75)
    
    for c in (raw_chunks or []):
        cid = c.get('metadata', {}).get('case_id', c.get('metadata', {}).get('title', ''))
        score = c.get('score', 0)
        
        # Scores are now cosine similarity (0.0 to 1.0) since we fixed the
        # cross-encoder to not overwrite them. Use a reasonable threshold.
        if score < rag_threshold:
            logger.info(f"Dropping weak chunk (cosine sim {score:.4f} < {rag_threshold}): {cid}")
            continue
        if cid not in grouped_cases:
            grouped_cases[cid] = {
                "metadata": c.get('metadata', {}),
                "score": score,
                "texts": []
            }
        else:
            # Keep the highest score for this case
            grouped_cases[cid]["score"] = max(grouped_cases[cid]["score"], score)
            
        # Keep up to 3 chunks per case
        if len(grouped_cases[cid]["texts"]) < 3:
            grouped_cases[cid]["texts"].append(c.get('text', ''))

    # Flatten and sort by highest score
    retrieved_chunks = list(grouped_cases.values())
    retrieved_chunks.sort(key=lambda x: x["score"], reverse=True)
    retrieved_chunks = retrieved_chunks[:8]  # Cap at 8 unique cases
    logger.info(f"RAG: {len(raw_chunks or [])} raw → {len(retrieved_chunks)} unique grouped precedents")

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
        extracted_precedents.append({
            "case_id": str(c['metadata'].get('case_id', '')),
            "case_title": str(c['metadata'].get('title', 'Unknown')),
            "relevance": relevance_label,
            "similarity_score": round(sim_score, 4),
            "key_holding": (" ".join(c['texts']))[:500] + "...",
            "outcome": str(c['metadata'].get('disposal_nature', 'UNKNOWN')),
            "applicability": ""
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
            f"Key Text: " + ("\n[...] ".join(c['texts']))[:500]
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
    agent2_sys_base = """You are a Senior Appellate Advocate practicing before the Supreme Court of India with expertise in Indian constitutional and statutory law.

YOUR TASK: Generate balanced pro-appeal and pro-compliance arguments for the current case.

INSTRUCTIONS:
1. Generate 3-5 SPECIFIC pro-appeal arguments citing actual legal principles, sections, or precedents.
2. Generate 3-5 SPECIFIC pro-compliance arguments.
3. Arguments must be GROUNDED in the case facts — no generic statements.
4. Consider the DISPOSITION — if the case was DISMISSED, compliance arguments are naturally stronger.
5. Consider the PRECEDENT ANALYSIS from Agent 1 — use the precedent trends to strengthen arguments.
6. Identify the SINGLE STRONGEST ground for each side.
7. Give a BALANCE ASSESSMENT: APPEAL_FAVORED, COMPLIANCE_FAVORED, or BALANCED.

CRITICAL RULES:
- If the petition was DISMISSED with costs, compliance is strongly favored.
- If there are constitutional violations (Art 14, 19, 21), appeal arguments gain weight.
- If precedents overwhelmingly favor one side, reflect that in your balance assessment."""

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
2. CONTEMPT RISK: If the government/party does NOT comply with the court order, what is the contempt risk? Consider:
   - Whether the order contains specific compliance directives with deadlines
   - Whether non-compliance could trigger contempt of court proceedings
   - Historical contempt actions in similar cases
3. LIMITATION ANALYSIS: Calculate the appeal limitation period based on Indian law:
   - High Court to Supreme Court (SLP): 90 days from the date of the order
   - Single Judge to Division Bench: 30 days
   - District Court to High Court: 90 days
4. FINANCIAL RISK: Assess costs, penalties, and financial exposure.

CRITICAL: Base your contempt urgency on the ACTUAL directives in the case, not hypotheticals."""

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
    agent4_sys_base = """You are the Chief Legal Advisor to the Government of India, responsible for making the final decision on whether to APPEAL or COMPLY with a court order.

YOUR TASK: Synthesize ALL inputs from the previous 3 agents and make a definitive recommendation.

DECISION FRAMEWORK — You MUST follow this logic:

1. IF the case was DISMISSED AND precedents are WEAK AND balance favors COMPLIANCE:
   → Recommend COMPLY with HIGH confidence
   → Only recommend APPEAL if there is a clear constitutional violation or jurisdictional error

2. IF the case was ALLOWED (petitioner won) AND there are strong compliance directives:
   → Carefully weigh appeal vs compliance
   → Consider contempt risk and financial exposure
   → If win rate in similar cases is >50%, lean toward APPEAL

3. IF precedents are STRONG in favor of appeal AND there are clear legal errors:
   → Recommend APPEAL with MODERATE-HIGH confidence

4. APPEAL FORUM — You MUST use the CORRECT NEXT APPELLATE FORUM provided in the case details:
   - Single Judge HC order → Division Bench of same HC
   - Division Bench HC order → Supreme Court (SLP under Art. 136)
   - Supreme Court order → Review Petition / Curative Petition
   NEVER recommend appealing a Division Bench order to "High Court"

5. CONFIDENCE SCORING:
   - 0.8-1.0: Overwhelming evidence supports the recommendation
   - 0.6-0.8: Strong evidence, some uncertainty
   - 0.4-0.6: Balanced case, could go either way
   - 0.2-0.4: Weak evidence, recommendation is precautionary

6. PRIMARY REASONING must be 3-5 sentences explaining the logic chain that led to your decision.

7. ACTION PLAN must include SPECIFIC deadlines and steps."""

    agent4_sys = build_agent_prompt(4, domain_key, agent4_sys_base)

    agent4_prompt = f"""{case_context}
{math_validation_text}
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
Contempt Risk: {agent3_out.contempt_urgency}
Contempt Assessment: {agent3_out.contempt_risk_assessment}
Limitation Analysis: {agent3_out.limitation_analysis}
Financial Risk: {agent3_out.financial_risk}
Procedural Issues: {json.dumps(agent3_out.procedural_loopholes, indent=2)}
=== END AGENT 3 ===

=== HISTORICAL STATISTICS ===
{stats_text}
=== END STATISTICS ===

Make your final recommendation. Remember: use the CORRECT NEXT APPELLATE FORUM from the case details."""

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
    final_json = {
        "recommendation_id": str(uuid.uuid4()),
        "case_id": case_id,
        "status": "COMPLETED",
        "verdict": {
            "decision": agent4_out.verdict.decision,
            "appeal_to": agent4_out.verdict.appeal_to,
            "confidence": agent4_out.verdict.confidence,
            "urgency": agent4_out.verdict.urgency,
            "limitation_deadline": deadline,
            "days_remaining": days_remaining,
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
            "rag_precedents": extracted_precedents,
            "precedents": [p.model_dump() for p in agent1_out.precedents],
            "balance_assessment": agent2_out.balance_assessment,
            "contempt_urgency": agent3_out.contempt_urgency,
        },
    }

    logger.info("Recommendation pipeline V2 complete.")
    return final_json
