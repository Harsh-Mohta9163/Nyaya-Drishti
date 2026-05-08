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
from typing import List, Dict, Any, Optional
from datetime import date, timedelta, datetime

from pydantic import BaseModel, Field
from django.conf import settings
from openai import OpenAI

from apps.action_plans.services.rag_engine import HybridRAGEngine
from apps.rag.parquet_store import DuckDBStore

logger = logging.getLogger(__name__)

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


def _call_nvidia(prompt: str, response_model, system_prompt: str, model: str = "meta/llama-3.3-70b-instruct") -> BaseModel:
    """Call NVIDIA NIM API with retry logic."""
    client = OpenAI(base_url=settings.NVIDIA_BASE_URL, api_key=settings.NVIDIA_API_KEY)
    example_json = _build_example_json(response_model)
    messages = [
        {"role": "system", "content": f"{system_prompt}\n\nIMPORTANT: Respond ONLY with valid JSON. No explanation or markdown.\nFollow this structure:\n{example_json}"},
        {"role": "user", "content": prompt}
    ]
    for attempt in range(3):
        try:
            logger.info(f"[NVIDIA] Calling {model} for {response_model.__name__} (attempt {attempt+1}/3)")
            response = client.chat.completions.create(
                model=model, messages=messages, temperature=0.15,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            logger.info(f"[NVIDIA] Response ({len(content)} chars): {content[:150]}...")
            return response_model.model_validate_json(content)
        except Exception as e:
            logger.warning(f"[NVIDIA] Attempt {attempt+1} failed: {e}")
            if attempt == 2: raise
            time.sleep(8 * (attempt + 1))


def _call_synthesis(prompt: str, response_model, system_prompt: str) -> BaseModel:
    """Call NVIDIA NIM for the synthesis agent (Agent 4).
    Uses Llama 3.3 70B as the primary model.
    """
    # Primary: Llama 3.3 70B (best available on NVIDIA NIM for reasoning)
    for model in ["meta/llama-3.3-70b-instruct"]:
        try:
            return _call_nvidia(prompt, response_model, system_prompt, model=model)
        except Exception as e:
            logger.warning(f"[Synthesis] {model} failed: {e}")
    raise RuntimeError("All LLM providers failed for Agent 4")


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
# The 4-Agent Pipeline
# ==============================================================================

def generate_recommendation(
    case_id: str, case_text: str, area_of_law: str, court: str,
    disposition: str = "", winning_party: str = "",
    case_type: str = "", bench: str = "",
    petitioner: str = "", respondent: str = "",
    issues: List[str] = None,
    date_of_order: str = ""
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
    # ---------------------------------------------------------
    rag = HybridRAGEngine()
    raw_chunks = rag.retrieve(case_text[:2000], top_k=15, filters=None)

    # Group by case_id to provide multiple chunks per case (broader context)
    grouped_cases = {}
    for c in (raw_chunks or []):
        cid = c.get('metadata', {}).get('case_id', c.get('metadata', {}).get('title', ''))
        score = c.get('score', 0)
        
        # Cross-encoder scores range from ~-10 to +10; 0+ is relevant.
        # Only keep genuinely relevant chunks (positive score) to avoid
        # noise diluting the synthesis agent's analysis.
        if score < 0.0:
            logger.info(f"Dropping weak chunk (score {score:.2f}): {cid}")
            continue
            
        if cid not in grouped_cases:
            grouped_cases[cid] = {
                "metadata": c.get('metadata', {}),
                "score": score,
                "texts": []
            }
            
        # Keep up to 3 chunks per case
        if len(grouped_cases[cid]["texts"]) < 3:
            grouped_cases[cid]["texts"].append(c.get('text', ''))

    # Flatten and sort by highest score
    retrieved_chunks = list(grouped_cases.values())
    retrieved_chunks.sort(key=lambda x: x["score"], reverse=True)
    retrieved_chunks = retrieved_chunks[:8]  # Cap at 8 unique cases
    logger.info(f"RAG: {len(raw_chunks or [])} raw → {len(retrieved_chunks)} unique grouped precedents")

    if not retrieved_chunks:
        logger.warning("No strong precedents found.")
        stuffed_context = "No direct precedents found in the database."
    else:
        stuffed_context = "\n\n".join([
            f"--- PRECEDENT {i+1} ---\n"
            f"Case: {c['metadata'].get('title', 'Unknown')}\n"
            f"Case ID: {c['metadata'].get('case_id', 'Unknown')}\n"
            f"Court: {c['metadata'].get('court', 'Unknown')}\n"
            f"Outcome: {c['metadata'].get('disposal_nature', 'Unknown')}\n"
            f"Similarity Score: {c.get('score', 0):.2f}\n"
            f"Judgment Excerpts:\n" + "\n[...] ".join(c['texts'])[:2500]
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
    agent1_sys = """You are a Senior Legal Researcher at the Supreme Court of India with 20+ years of experience analyzing case precedents.

YOUR TASK: Analyze the retrieved precedent cases and determine how they relate to the current case.

INSTRUCTIONS:
1. For each precedent, assess its RELEVANCE to the current case (consider: same area of law, similar facts, similar legal issues, same court hierarchy level).
2. Identify the KEY HOLDING — what did the court decide and why?
3. Determine the OUTCOME — was the appeal allowed or dismissed?
4. Assess APPLICABILITY — does this precedent SUPPORT or UNDERMINE the current case's position?
5. Provide an OVERALL TREND — what do the precedents collectively suggest about the likely outcome?
6. Rate PRECEDENT STRENGTH as STRONG (>70% precedents support one side), MODERATE (50-70%), or WEAK (<50% or insufficient data).

IMPORTANT: If the current case was DISMISSED by the court, precedents showing other DISMISSED cases WEAKEN the appeal case. Precedents showing ALLOWED appeals STRENGTHEN it."""

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
    agent2_sys = """You are a Senior Appellate Advocate practicing before the Supreme Court of India with expertise in Indian constitutional and statutory law.

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

    agent2_prompt = f"""{case_context}

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
    agent3_sys = """You are a Legal Risk Auditor specializing in Indian government litigation and contempt proceedings.

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

    agent3_prompt = f"""{case_context}

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
    agent4_sys = """You are the Chief Legal Advisor to the Government of India, responsible for making the final decision on whether to APPEAL or COMPLY with a court order.

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

    agent4_prompt = f"""{case_context}

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
            "precedents": [p.model_dump() for p in agent1_out.precedents],
            "balance_assessment": agent2_out.balance_assessment,
            "contempt_urgency": agent3_out.contempt_urgency,
        },
    }

    logger.info("Recommendation pipeline V2 complete.")
    return final_json
