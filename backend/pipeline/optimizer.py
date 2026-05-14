import os
import json
import logging
from typing import List, Dict, Any
from google import genai
from backend.config import config
from backend.pipeline.notebook_client import notebook_client

logger = logging.getLogger(__name__)

class PromptOptimizer:
    def __init__(self, model_name: str = "gemini-2.0-pro-exp-02-05"):
        self.model_name = model_name
        self.client = genai.Client(api_key=config.GOOGLE_API_KEY)
        self.prompts_base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agents", "prompts")
        self.optimized_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agents", "prompts_optimized")
        
        if not os.path.exists(self.optimized_dir):
            os.makedirs(self.optimized_dir)

    async def fetch_telemetry(self, prompt_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetches recent telemetry for a specific prompt."""
        def _run():
            with notebook_client._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM prompt_telemetry 
                        WHERE prompt_name = %s 
                        AND final_approved_output IS NOT NULL
                        ORDER BY created_at DESC 
                        LIMIT %s
                    """, [prompt_name, limit])
                    return [dict(row) for row in cur.fetchall()]
        
        # We need RealDictCursor which is imported in notebook_client
        from psycopg2.extras import RealDictCursor
        return await asyncio.to_thread(_run)

    async def optimize_prompt(self, dimension: str, prompt_name: str):
        """Analyzes feedback and generates an optimized prompt in the shadow directory."""
        logger.info(f"--- Optimizing Prompt: {dimension}/{prompt_name} ---")
        
        # 1. Load Original Prompt
        original_path = os.path.join(self.prompts_base_dir, dimension, f"{prompt_name}.txt")
        if not os.path.exists(original_path):
            logger.error(f"Original prompt not found at {original_path}")
            return
            
        with open(original_path, "r", encoding="utf-8") as f:
            original_content = f.read()
            
        # 2. Fetch Telemetry
        telemetry = await self.fetch_telemetry(f"{dimension}/{prompt_name}")
        if not telemetry:
            logger.warning(f"No telemetry found for {dimension}/{prompt_name}. Skipping.")
            return

        # 3. Build Optimization Prompt
        examples = []
        for t in telemetry:
            examples.append(f"### EXAMPLE CASE\nINPUT CONTEXT: {t['input_context']}\n\nAI ORIGINAL OUTPUT: {t['raw_output']}\n\nHUMAN FINAL APPROVED: {t['final_approved_output']}\n---")

        dim_instructions = ""
        if dimension == "materiality":
            dim_instructions = "Focus on 'Sensitivity'. If humans suppressed many claims, the prompt is too sensitive. If they manually injected or complained about missing data, it is not sensitive enough."
        elif dimension == "report" and "conflict" in prompt_name:
            dim_instructions = "Focus on 'Bias & Resolution'. If the analyst chose one side consistently, ensure the resolution logic gives more weight to those specific dialectical patterns."

        optimization_instruction = f"""
You are an Expert Prompt Engineer specializing in Institutional Research Agents.
Your goal is to optimize the following prompt template based on recent human feedback.

### ORIGINAL PROMPT TEMPLATE
{original_content}

### RECENT FAILURES & HUMAN EDITS
{chr(10).join(examples)}

### CATEGORY SPECIFIC GUIDANCE
{dim_instructions}

### INSTRUCTIONS
1. Analyze the gap between 'AI ORIGINAL OUTPUT' and 'HUMAN FINAL APPROVED'.
2. Identify systematic errors (e.g., missing metrics, tone issues, hallucinations, or lack of depth).
3. Update the ORIGINAL PROMPT TEMPLATE to include specific new instructions, constraints, or 'Best Practices' that would prevent these errors.
4. DO NOT change the JSON schema structure or any technical delimiters.
5. Return ONLY the new updated prompt template. No conversational text.
"""

        # 4. Call High-Quality Model
        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model=self.model_name,
            contents=optimization_instruction,
            config={"temperature": 0.2}
        )
        
        optimized_content = response.text.strip()
        
        # 5. Write to Optimized Directory (Shadow File)
        target_dir = os.path.join(self.optimized_dir, dimension)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            
        optimized_path = os.path.join(target_dir, f"{prompt_name}.txt")
        with open(optimized_path, "w", encoding="utf-8") as f:
            f.write(optimized_content)
            
        logger.info(f"SUCCESS: Optimized prompt written to {optimized_path}")

# Import guard for async
import asyncio
from psycopg2.extras import RealDictCursor

if __name__ == "__main__":
    # Example usage for testing
    optimizer = PromptOptimizer()
    # asyncio.run(optimizer.optimize_prompt("report", "fdd_synthesis_cold"))
