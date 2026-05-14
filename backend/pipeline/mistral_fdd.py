import json
from typing import Dict, Any
from backend.agents.fdd_synthesis_agent import fdd_synthesis_agent

async def generate_fdd_report(ticker: str, notebook_entries: Dict[str, Any]) -> str:
    """
    Synthesizes the final FDD report from all notebook entries using Mistral.
    """
    # 1. Prepare context from all dimensions
    context_blocks = []
    for dimension, entry in notebook_entries.items():
        if entry:
            context_blocks.append(f"### DIMENSION: {dimension.replace('_', ' ').upper()}\n{json.dumps(entry, indent=2)}")
            
    full_context = "\n\n".join(context_blocks)
    
    # 2. Run the synthesis agent
    variables = {
        "ticker": ticker,
        "notebook_context": full_context
    }
    
    res = await fdd_synthesis_agent.process(variables)
    
    if res.get("status") == "success":
        # Extract raw report text
        return res.get("raw_output", "Failed to generate report content.")
    else:
        return f"Error in FDD Synthesis: {res.get('error')}"
