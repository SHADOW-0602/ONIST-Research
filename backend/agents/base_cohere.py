import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from langchain_cohere import ChatCohere
from backend.config import config
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

class BaseCohereAgent:
    def __init__(self, dimension: str, agent_name: str, model_name: str = "command-r-plus-08-2024"):
        self.dimension = dimension
        self.agent_name = agent_name
        self.model_name = model_name
        self.llm = ChatCohere(
            model=model_name,
            cohere_api_key=config.COHERE_API_KEY,
            temperature=0.0
        )
        self.prompts_dir = os.path.join(os.path.dirname(__file__), "prompts", dimension)

    def _load_template(self, agent_name: str, run_type: str = "cold") -> str:
        filename_rt = f"{agent_name}_{run_type}.txt"
        filename_gen = f"{agent_name}.txt"
        
        # [NEW] Shadow Prompting
        optimized_dir = os.path.join(os.path.dirname(__file__), "prompts_optimized", self.dimension)
        
        candidates = [
            os.path.join(optimized_dir, filename_rt),
            os.path.join(optimized_dir, filename_gen),
            os.path.join(self.prompts_dir, filename_rt),
            os.path.join(self.prompts_dir, filename_gen)
        ]
        
        path = None
        for p in candidates:
            if os.path.exists(p):
                if "prompts_optimized" in p:
                    logger.info(f"--- [LAYER 6] Using OPTIMIZED Cohere prompt: {os.path.basename(p)} ---")
                path = p
                break
                
        if not path:
            raise FileNotFoundError(f"Cohere prompt not found: {agent_name} (run_type: {run_type})")
            
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
        wait=wait_exponential(multiplier=2, min=3, max=10),
        retry=retry_if_exception_type(Exception),
        before_sleep=lambda retry_state: logger.warning(f"Cohere API Error. Retrying...")
    )
    async def process(self, variables: Dict[str, Any]) -> dict:
        """
        Executes the Cohere agent.
        """
        run_type = variables.get("run_type", "cold")
        template = self._load_template(self.agent_name, run_type)
        final_prompt = self._render_prompt(template, variables)
        
        content = ""
        try:
            # We don't have json_object for all cohere models natively in langchain, 
            # but command-r-plus respects prompt formatting well.
            response = await self.llm.ainvoke(final_prompt)
            content = response.content.strip()
            
            # Robust JSON extraction
            import re
            json_match = re.search(r'(\{.*\}|\[.*\])', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
            
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                logger.warning(f"Cohere Agent [{self.agent_name}] returned non-dict JSON. Wrapping.")
                return {"malformed_output": content, "parsed_result": parsed}
            return parsed
            
        except Exception as e:
            logger.error(f"Cohere Agent Error [{self.agent_name}]: {str(e)}\nRaw Content: {content[:500]}...")
            raise e
