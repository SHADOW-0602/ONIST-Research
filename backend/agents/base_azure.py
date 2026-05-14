import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from langchain_openai import AzureChatOpenAI
from backend.config import config
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

class BaseAzureAgent:
    def __init__(self, gate_name: str, model_name: Optional[str] = None):
        self.gate_name = gate_name
        # Use deployment name if model_name is not provided
        self.deployment_name = config.AZURE_OPENAI_DEPLOYMENT
        self.model_name = model_name or config.AZURE_OPENAI_MODEL
        self.prompts_dir = os.path.join(os.path.dirname(__file__), "prompts", "verification")
        
    def _get_llm(self):
        """Returns an AzureChatOpenAI instance."""
        return AzureChatOpenAI(
            azure_deployment=self.deployment_name,
            api_key=config.AZURE_OPENAI_KEY,
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
            api_version="2024-02-15-preview", # Standard stable version
            temperature=0.0
        )

    def _load_template(self, gate_name: str, run_type: str = "cold") -> str:
        # Try specific run type first, e.g. gate1_hallucination_delta.txt
        path_run_type = os.path.join(self.prompts_dir, f"{gate_name}_{run_type}.txt")
        path_generic = os.path.join(self.prompts_dir, f"{gate_name}.txt")
        
        if os.path.exists(path_run_type):
            path = path_run_type
        elif os.path.exists(path_generic):
            path = path_generic
        else:
            raise FileNotFoundError(f"Verification prompt not found: {gate_name} (run_type: {run_type})")
            
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _render_prompt(self, template: str, variables: Dict[str, Any]) -> str:
        rendered = template
        for key, value in variables.items():
            placeholder = "{{" + key.upper() + "}}"
            val_str = str(value) if value is not None else "null"
            rendered = rendered.replace(placeholder, val_str)
        return rendered

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=1, max=5),
        retry=retry_if_exception_type(Exception),
        before_sleep=lambda retry_state: logger.warning(f"Azure OpenAI Error. Retrying...")
    )
    async def verify(self, variables: Dict[str, Any]) -> dict:
        """
        Executes the verification gate.
        """
        run_type = variables.get("run_type", "cold")
        template = self._load_template(self.gate_name, run_type)
        final_prompt = self._render_prompt(template, variables)
        
        # Sub-second inference, minimal stagger
        await asyncio.sleep(0.05)
        
        try:
            llm = self._get_llm()
            # Azure OpenAI supports response_format in newer API versions
            bound_llm = llm.bind(
                response_format={"type": "json_object"}
            )
            
            response = await bound_llm.ainvoke(final_prompt)
            content = response.content.strip()
            
            # Strip markdown if present
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
                
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                # If LLM returned a string or list instead of object
                return {
                    "gate": self.gate_name,
                    "status": "malformed_output",
                    "raw_output": content,
                    f"{self.gate_name}_enriched_agent_output": json.loads(variables.get("agent_output", "{}"))
                }
            return parsed
            
        except Exception as e:
            logger.error(f"Azure Gate Error [{self.gate_name}]: {str(e)}")
            # Fallback: Return the input unchanged if verification fails
            # We wrap it in a pseudo gate response to maintain structure
            return {
                "gate": self.gate_name,
                "error": str(e),
                f"{self.gate_name}_enriched_agent_output": json.loads(variables.get("agent_output", "{}"))
            }
