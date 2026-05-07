import json
import logging
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from django.conf import settings

from apps.cases.models import Judgment
from apps.action_plans.services.rag_engine import HybridRAGEngine

logger = logging.getLogger(__name__)

class AppealStrategySchema(BaseModel):
    appeal_viability: str = Field(description="High, Medium, or Low")
    appeal_strategy: str = Field(description="Detailed legal strategy for appeal")
    appeal_precedents: list[str] = Field(description="List of case numbers that support the appeal")

def generate_appeal_strategy(judgment_id: str) -> dict:
    """
    Synthesize an appeal strategy using Gemini Pro and retrieved precedents.
    """
    try:
        judgment = Judgment.objects.select_related("case").get(id=judgment_id)
        
        # 1. Prepare context from current judgment
        current_case_context = f"""
        Case: {judgment.case.case_number} ({judgment.case.court_name})
        Type: {judgment.case.case_type}
        Disposition: {judgment.disposition}
        Winning Party: {judgment.winning_party_type}
        
        Summary of Facts:
        {judgment.summary_of_facts}
        
        Ratio Decidendi:
        {judgment.ratio_decidendi}
        
        Court Directions:
        {judgment.court_directions}
        """

        # 2. Retrieve Precedents
        rag = HybridRAGEngine()
        # Find cases where the government/our side won in similar contexts
        # (Assuming the system wants precedents where the "losing" side in the current case won in the past)
        # Here we just retrieve similar cases by facts/ratio
        query = f"{judgment.summary_of_facts}\n{judgment.ratio_decidendi}"
        
        # We can filter for cases that were "Allowed" if our side is the appellant
        # For now, just top 3 similar cases
        precedents = rag.retrieve(query=query, top_k=3)
        
        precedents_context = ""
        for i, p in enumerate(precedents):
            meta = p.get("metadata", {})
            precedents_context += f"\n--- Precedent {i+1} ---\n"
            precedents_context += f"Case: {meta.get('case_number')} ({meta.get('court_name')})\n"
            precedents_context += f"Disposition: {meta.get('disposition')}\n"
            precedents_context += f"Text:\n{p.get('text')}\n"

        # 3. Call Gemini Pro
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        sys_prompt = """
        You are an expert appellate lawyer. Based on the current judgment and the retrieved precedents, 
        advise whether an appeal is viable and outline the best legal strategy.
        Provide your reasoning clearly. Focus on identifying legal errors in the current judgment 
        that can be challenged in a higher court.
        """
        
        prompt = f"""
        CURRENT JUDGMENT:
        {current_case_context}
        
        RETRIEVED PRECEDENTS:
        {precedents_context}
        """
        
        response = client.models.generate_content(
            model=settings.GEMINI_PRO_MODEL,
            contents=f"System: {sys_prompt}\n\n{prompt}",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AppealStrategySchema,
                temperature=0.2
            ),
        )
        
        result = json.loads(response.text)
        return result
        
    except Exception as e:
        logger.error(f"Error generating appeal strategy: {e}")
        raise e
