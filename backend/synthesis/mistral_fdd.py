from langchain_mistralai import ChatMistralAI
from backend.config import config
import logging
import json
from backend.models import Compendium

logger = logging.getLogger(__name__)

class MistralFDDSynthesizer:
    def __init__(self, model_name: str = "mistral-large-latest"):
        self.llm = ChatMistralAI(
            api_key=config.MISTRAL_API_KEY,
            model=model_name,
            temperature=0.2
        )

    async def synthesize(self, compendium: Compendium) -> str:
        """
        Takes the canonical Notebook Compendium and generates the Fundamental Due Diligence (FDD) Report.
        Only considers data points where investment_relevance.relevant == True.
        """
        logger.info(f"Initiating Mistral FDD Synthesis for {compendium.entity.ticker}")
        
        # 1. Filter the compendium for only material, relevant claims
        material_claims = []
        for section_name, section_data in compendium.sections.model_dump().items():
            for dp in section_data.get("data_points", []):
                if dp.get("investment_relevance", {}).get("relevant", False):
                    material_claims.append({
                        "section": section_name,
                        "claim": dp.get("claim"),
                        "confidence": dp.get("confidence_tier")
                    })
        
        if not material_claims:
            return "No material claims found to synthesize."

        # 2. Construct the prompt
        prompt = f"""
        You are the Lead Financial Analyst synthesizing the Fundamental Due Diligence (FDD) Report for {compendium.entity.legal_name} ({compendium.entity.ticker}).
        
        Below are the strictly filtered, materially relevant claims from the internal Notebook:
        {json.dumps(material_claims, indent=2)}
        
        Write a concise, institutional-grade FDD Report (under 10 pages). Structure it with:
        - Executive Summary
        - Corporate Identity & Moat
        - Segment Performance
        - Risks & Tailwinds
        - Management Evaluation
        
        Ensure you do not hallucinate outside of the provided material claims.
        """
        
        try:
            response = await self.llm.ainvoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"Mistral FDD Synthesis Error: {str(e)}")
            return "Error generating FDD Report."

fdd_synthesizer = MistralFDDSynthesizer()