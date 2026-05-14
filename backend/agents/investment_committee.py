import json
import logging
import json
import logging
from typing import Dict, Any
from backend.agents.base_mistral import BaseMistralAgent
from backend.agents.base_cohere import BaseCohereAgent

logger = logging.getLogger(__name__)

class InvestmentCommitteeAgent:
    def __init__(self):
        self.skeptic = BaseMistralAgent("report", "committee_skeptic")
        self.optimist = BaseMistralAgent("report", "committee_optimist")
        self.cio = BaseCohereAgent("report", "committee_cio")

    async def run_committee(self, report_draft: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Runs an adversarial committee meeting on the report draft."""
        logger.info(f"--- [LAYER 7] Investment Committee Meeting Convened ---")
        
        variables = {
            "report_draft": json.dumps(report_draft, indent=2),
            "ticker": context.get("ticker"),
            "company_name": context.get("company_name")
        }
        
        # 1. Skeptic's Cross-Examination
        print("  > IC: Skeptic is reviewing for risks...", flush=True)
        skeptic_minutes = await self.skeptic.process(variables)
        
        # 2. Optimist's Rebuttal
        print("  > IC: Optimist is defending the thesis...", flush=True)
        variables["skeptic_critique"] = json.dumps(skeptic_minutes)
        optimist_minutes = await self.optimist.process(variables)
        
        # 3. CIO's Final Verdict & Guidance
        print("  > IC: CIO is issuing final guidance...", flush=True)
        variables["optimist_defense"] = json.dumps(optimist_minutes)
        final_verdict = await self.cio.process(variables)
        
        return {
            "skeptic_critique": skeptic_minutes,
            "optimist_defense": optimist_minutes,
            "cio_verdict": final_verdict
        }

investment_committee = InvestmentCommitteeAgent()
