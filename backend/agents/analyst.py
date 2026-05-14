import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from langchain_openai import AzureChatOpenAI
from backend.config import config
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

class AnalystAgent:
    def __init__(self, model_name: Optional[str] = None):
        self.deployment_name = config.AZURE_OPENAI_DEPLOYMENT
        self.model_name = model_name or config.AZURE_OPENAI_MODEL
        # Use a general prompt for the analyst fallback
        self.prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")
        
    def _get_llm(self):
        """Returns an AzureChatOpenAI instance."""
        return AzureChatOpenAI(
            azure_deployment=self.deployment_name,
            api_key=config.AZURE_OPENAI_KEY,
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
            api_version="2024-02-15-preview",
            temperature=0.0
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=1, max=5),
        retry=retry_if_exception_type(Exception),
        before_sleep=lambda retry_state: logger.warning(f"Analyst Agent (Azure) Error. Retrying...")
    )
    async def analyze(self, variables: Dict[str, Any]) -> dict:
        """
        Executes a general analysis using GPT-4 (Azure).
        This is primarily used as a fallback for other models.
        """
        llm = self._get_llm()
        
        # We don't have a specific prompt file for "analyst" yet, 
        # so we'll build a general fallback prompt or use the one passed in context if possible.
        # For now, we'll assume the caller wants a robust JSON response matching the variables intent.
        
        system_prompt = "You are an institutional-grade financial analyst. Your task is to process the following context and return a structured JSON response."
        user_content = f"Context Variables: {json.dumps(variables, indent=2)}\n\nPlease provide a detailed analysis based on the provided variables. Ensure the output is valid JSON."
        
        try:
            # Bind JSON mode
            bound_llm = llm.bind(response_format={"type": "json_object"})
            
            messages = [
                ("system", system_prompt),
                ("user", user_content)
            ]
            
            response = await bound_llm.ainvoke(messages)
            content = response.content.strip()
            
            # Strip markdown if present
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
                
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Analyst Agent Error: {str(e)}")
            return {"status": "error", "message": str(e)}

analyst_agent = AnalystAgent()
