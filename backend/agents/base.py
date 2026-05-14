import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from google import genai
from backend.config import config
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

class BaseResearchAgent:
    def __init__(self, dimension_name: str, model_name: str = "gemini-2.5-flash"):
        self.dimension_name = dimension_name
        self.model_name = model_name
        self.client = genai.Client(api_key=config.GOOGLE_API_KEY)
        self.prompts_dir = os.path.join(os.path.dirname(__file__), "prompts", dimension_name)

    def _load_template(self, run_type: str) -> str:
        filename = f"{run_type}_run.txt"
        
        # [NEW] Shadow Prompting: Check optimized directory first
        optimized_dir = os.path.join(os.path.dirname(__file__), "prompts_optimized", self.dimension_name)
        optimized_path = os.path.join(optimized_dir, filename)
        
        original_path = os.path.join(self.prompts_dir, filename)
        
        if os.path.exists(optimized_path):
            logger.info(f"--- [LAYER 6] Using OPTIMIZED prompt: {self.dimension_name}/{filename} ---")
            path = optimized_path
        elif os.path.exists(original_path):
            path = original_path
        else:
            raise FileNotFoundError(f"Prompt template not found: {self.dimension_name}/{filename}")
            
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _render_prompt(self, template: str, variables: Dict[str, Any]) -> str:
        rendered = template
        for key, value in variables.items():
            placeholder = "{{" + key.upper() + "}}"
            rendered = rendered.replace(placeholder, str(value) if value is not None else "null")
        return rendered

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        before_sleep=lambda retry_state: logger.warning(f"Rate limit or API error hit. Retrying...")
    )
    async def _call_llm(self, prompt: str, run_type: str) -> str:
        """Calls Gemini with exponential backoff and dynamic parameters using google-genai SDK."""
        try:
            # Dynamic parameters based on run type
            # [PRD UPDATE] Increase max_output_tokens to handle large biographical datasets (e.g. NVDA)
            max_tokens = 16384 if run_type == "cold" else 8192
            
            # Generate content using the new SDK
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model_name,
                contents=prompt,
                config={
                    "max_output_tokens": max_tokens,
                    "temperature": 0.0,
                    "response_mime_type": "application/json"
                }
            )
            
            if not response or not response.text:
                raise Exception("Empty response from Gemini API")
                
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error in _call_llm for {self.dimension_name}: {e}")
            raise e

    async def analyze(self, variables: Dict[str, Any]) -> dict:

        """
        Executes the research agent with robust error handling and optimized Gemini parameters.
        """
        # 1. Source check
        source_chunks = variables.get("source_chunks", "")
        # Lenient check for cold runs or identity normalization to allow initial bootstrap
        if not source_chunks or len(source_chunks.strip()) < 20:
             logger.warning(f"[{self.dimension_name}] Minimal or no sources retrieved. Proceeding with fallback context.")
             source_chunks = f"No detailed SEC filings available in RAG yet. Use company context: {variables.get('company_name')} ({variables.get('ticker')})"
        
        variables["source_chunks"] = source_chunks # Ensure updated chunks are used in prompt

        run_type = "delta" if variables.get("notebook_entries") else "cold"
        template = self._load_template(run_type)
        final_prompt = self._render_prompt(template, variables)
        
        # Async stagger delay to prevent rate limit collisions
        await asyncio.sleep(0.2)
        
        attempts = 0
        max_json_retries = 2
        last_error = None
        
        while attempts < max_json_retries:
            try:
                # API Call with Tenacity Backoff and Dynamic Params
                content = await self._call_llm(final_prompt, run_type)
                
                # Robust JSON Extraction
                clean_content = self._clean_json(content)
                
                try:
                    parsed = json.loads(clean_content)
                except json.JSONDecodeError as jde:
                    # Second attempt: try to fix common issues like trailing commas
                    try:
                        repaired = self._repair_json_string(clean_content)
                        parsed = json.loads(repaired)
                    except:
                        # Third attempt: regex for the first object
                        import re
                        match = re.search(r'(\{.*\})', clean_content, re.DOTALL)
                        if match:
                            try:
                                parsed = json.loads(self._repair_json_string(match.group(1)))
                            except:
                                raise jde # Raise original error if repair fails
                        else:
                            raise jde
                
                return {
                    "dimension": self.dimension_name,
                    "status": "success",
                    "run_type": run_type,
                    "raw_output": content
                }
            
            except json.JSONDecodeError as e:
                attempts += 1
                last_error = str(e)
                logger.error(f"[{self.dimension_name}] Invalid JSON returned. Attempt {attempts}/{max_json_retries}.")
                logger.debug(f"[{self.dimension_name}] Raw output: {content}")
                # Explicit reminder for the second attempt
                final_prompt += "\n\nCRITICAL: Your previous response was not valid JSON. Return ONLY the raw JSON matching the schema."
            
            except Exception as e:
                logger.error(f"[{self.dimension_name}] Fatal API Error: {str(e)}")
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

    def _clean_json(self, content: str) -> str:
        """Strips markdown and whitespace from JSON strings."""
        clean = content.strip()
        if "```json" in clean:
            clean = clean.split("```json")[1].split("```")[0].strip()
        elif "```" in clean:
            clean = clean.split("```")[1].split("```")[0].strip()
        return clean

    def _repair_json_string(self, json_str: str) -> str:
        """Applies robust heuristics to fix common LLM JSON errors and truncation."""
        import re
        res = json_str.strip()
        
        # 1. Handle common truncation: if it ends with a comma or part of a key
        res = re.sub(r',\s*$', '', res)
        
        # 2. Fix unescaped newlines in strings (common in bios/summaries)
        def escape_newlines(match):
            return match.group(0).replace('\n', '\\n').replace('\r', '\\r')
        res = re.sub(r'("(?:\\.|[^"\\])*")', escape_newlines, res)

        # 3. Aggressive Truncation Repair: Close all open brackets/quotes
        # Track stack of open structures
        stack = []
        is_in_string = False
        escape = False
        
        fixed_chars = []
        for i, char in enumerate(res):
            if escape:
                fixed_chars.append(char)
                escape = False
                continue
            
            if char == '\\':
                fixed_chars.append(char)
                escape = True
                continue
                
            if char == '"':
                is_in_string = not is_in_string
            
            if not is_in_string:
                if char == '{': stack.append('}')
                elif char == '[': stack.append(']')
                elif char == '}' or char == ']':
                    if stack and stack[-1] == char:
                        stack.pop()
            
            fixed_chars.append(char)

        res = "".join(fixed_chars)
        
        # If we are still in a string, close the quote
        if is_in_string:
            res += '"'
            
        # Close all open objects/arrays in reverse order
        while stack:
            closing = stack.pop()
            # If the last char is a comma, remove it before closing
            res = res.strip()
            if res.endswith(','):
                res = res[:-1].strip()
            res += closing
            
        return res
