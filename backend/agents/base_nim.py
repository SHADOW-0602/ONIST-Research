import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from backend.config import config
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

class BaseNIMAgent:
    def __init__(self, dimension_name: str, model_name: str = "meta/llama-3.1-405b-instruct"):
        self.dimension_name = dimension_name
        self.model_name = model_name
        # Base LLM
        self.base_llm = ChatNVIDIA(
            model=model_name,
            nvidia_api_key=config.NVIDIA_API_KEY,
            temperature=0.1
        )
        self.prompts_dir = os.path.join(os.path.dirname(__file__), "prompts", dimension_name)

    def _load_template(self, run_type: str) -> str:
        path = os.path.join(self.prompts_dir, f"{run_type}_run.txt")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Prompt template not found: {path}")
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
        wait=wait_exponential(multiplier=2, min=3, max=15), # Layer 2: Start at 3s backoff
        retry=retry_if_exception_type(Exception),
        before_sleep=lambda retry_state: logger.warning(f"Layer 2 NIM Rate limit. Retrying...")
    )
    async def _call_llm(self, prompt: str, run_type: str) -> str:
        """Calls NVIDIA NIM with Layer 2 optimized parameters."""
        max_tokens = 16384 if run_type == "cold" else 8192
        
        # Bind parameters
        # Note: 'response_format' is passed in model_kwargs for ChatNVIDIA
        bound_llm = self.base_llm.bind(
            max_tokens=max_tokens,
            model_kwargs={"response_format": {"type": "json_object"}}
        )
        
        response = await bound_llm.ainvoke(prompt)
        return response.content.strip()

    async def analyze(self, variables: Dict[str, Any]) -> dict:
        """
        Executes the specialist NIM agent with Layer 2 constraints.
        """
        # 1. Source check (Footprint Agent specific check is handled in orchestrator or here)
        source_chunks = variables.get("source_chunks", "")
        chunk_count = variables.get("chunk_count", 0)
        
        # Footprint Agent: Lenient bootstrap for discovery
        if self.dimension_name == "footprint" and chunk_count < 1:
            logger.warning(f"[{self.dimension_name}] No qualitative sources retrieved. Proceeding with fallback context.")
            source_chunks = f"No detailed qualitative sources available in RAG. Use context: {variables.get('company_name')}"
        
        if not source_chunks or len(source_chunks.strip()) < 20:
            logger.warning(f"[{self.dimension_name}] Minimal or no sources retrieved. Proceeding with fallback context.")
            source_chunks = f"No detailed sources available in RAG. Use company context: {variables.get('company_name')}"
        
        variables["source_chunks"] = source_chunks

        run_type = "delta" if variables.get("notebook_entries") else "cold"
        template = self._load_template(run_type)
        final_prompt = self._render_prompt(template, variables)
        
        # Async stagger delay
        await asyncio.sleep(0.15)
        
        attempts = 0
        max_json_retries = 2
        last_error = None
        
        while attempts < max_json_retries:
            try:
                content = await self._call_llm(final_prompt, run_type)
                
                # Strip potential markdown
                if content.startswith("```json"):
                    content = content[7:-3].strip()
                elif content.startswith("```"):
                    content = content[3:-3].strip()
                
                # JSON Validation
                parsed = json.loads(content)
                return {
                    "dimension": self.dimension_name,
                    "status": "success",
                    "run_type": run_type,
                    "raw_output": content,
                    "source_count": chunk_count
                }
            
            except json.JSONDecodeError as e:
                attempts += 1
                last_error = str(e)
                logger.error(f"[{self.dimension_name}] Invalid JSON from NIM. Attempt {attempts}/{max_json_retries}.")
                final_prompt += "\n\nCRITICAL: Your previous response was not valid JSON. Return ONLY the raw JSON matching the schema."
            
            except Exception as e:
                logger.error(f"[{self.dimension_name}] Fatal NIM API Error: {str(e)}")
                return {
                    "dimension": self.dimension_name,
                    "status": "agent_failure",
                    "error": str(e)
                }

        return {
            "dimension": self.dimension_name,
            "status": "agent_failure",
            "error": f"JSON parsing failed after {max_json_retries} attempts: {last_error}"
        }
