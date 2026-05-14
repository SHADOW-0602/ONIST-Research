import json
import logging
from typing import Dict, Any, List, Tuple
from backend.agents.base_azure import BaseAzureAgent

logger = logging.getLogger(__name__)

class VerificationPipeline:
    def __init__(self):
        # Use Azure OpenAI for verification to bypass Groq rate limits
        self.gate1 = BaseAzureAgent(gate_name="gate1_hallucination")
        self.gate2 = BaseAzureAgent(gate_name="gate2_source")
        self.gate3 = BaseAzureAgent(gate_name="gate3_staleness")

    async def verify_agent_output(self, handoff_data: Dict[str, Any], variables: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Runs the sequential three-gate verification.
        Returns (notebook_ready_output, full_gate_responses)
        """
        agent_name = handoff_data.get("agent_name", "unknown")
        
        # 1. Gate 1: Hallucination Detector
        gate1_vars = {
            **variables,
            "agent_name": agent_name,
            "agent_output": json.dumps(handoff_data["agent_output"]),
            "source_documents": json.dumps(handoff_data["source_documents"]),
            "run_type": handoff_data["run_type"],
            "company_name": handoff_data["company"],
            "ticker": handoff_data["ticker"]
        }
        gate1_res = await self.gate1.verify(gate1_vars)
        
        # 2. Gate 2: Source Auditor
        gate2_vars = {
            **gate1_vars,
            "gate1_output": json.dumps(gate1_res),
            "source_tier_map": json.dumps(handoff_data.get("source_tier_map", {}))
        }
        gate2_res = await self.gate2.verify(gate2_vars)
        
        # 3. Gate 3: Staleness Reviewer
        gate3_vars = {
            **gate2_vars,
            "gate2_output": json.dumps(gate2_res),
            "freshness_thresholds": json.dumps(variables.get("freshness_thresholds", {}))
        }
        gate3_res = await self.gate3.verify(gate3_vars)
        
        notebook_ready = gate3_res.get("notebook_ready_output", handoff_data["agent_output"])
        
        full_responses = {
            "gate1": gate1_res,
            "gate2": gate2_res,
            "gate3": gate3_res
        }
        
        return notebook_ready, full_responses

verification_pipeline = VerificationPipeline()
