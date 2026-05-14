import logging
from typing import List, Dict, Any
from backend.pipeline.notebook_client import notebook_client

logger = logging.getLogger(__name__)

class ContagionAnalyzer:
    async def analyze_systemic_risks(self, ticker: str, dimensions: List[str]) -> List[Dict[str, Any]]:
        """
        Identifies related tickers that might be affected by the findings of the current research.
        Uses semantic similarity and common themes in the notebook.
        """
        logger.info(f"--- [LAYER 7] Running Contagion Analysis for {ticker} ---")
        
        # 1. Fetch current findings
        findings = await notebook_client.get_notebook_entries(ticker)
        
        # 2. Extract key themes (for now, using a simple keyword-based approach)
        # In a real system, we would use an LLM to summarize the themes.
        key_themes = []
        for dim in dimensions:
            claims = findings.get(dim, [])
            for c in claims:
                text = c.get("value", {}).get("claim", "")
                # Simple extraction of proper nouns or themes
                # (Simulated for this implementation)
                if "supply chain" in text.lower(): key_themes.append("supply_chain_disruption")
                if "regulatory" in text.lower(): key_themes.append("regulatory_headwinds")
                if "interest rate" in text.lower(): key_themes.append("macro_sensitivity")
        
        # 3. Find other tickers with similar themes in their notebooks
        # (Simulated database query for related tickers)
        # In production, we'd query: SELECT DISTINCT ticker FROM notebook_entries WHERE text % theme
        related_tickers = []
        if "supply_chain_disruption" in key_themes:
            related_tickers.append({"ticker": "TSMC", "reason": "Supply chain contagion", "severity": "High"})
            related_tickers.append({"ticker": "FOXCONN", "reason": "Manufacturing bottleneck", "severity": "Medium"})
        
        if "macro_sensitivity" in key_themes:
            related_tickers.append({"ticker": "JPM", "reason": "Financial sector exposure", "severity": "Low"})

        return related_tickers

contagion_analyzer = ContagionAnalyzer()
