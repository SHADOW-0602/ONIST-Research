import os
from typing import Dict, Any
from backend.agents.base_mistral import BaseMistralAgent

class FDDSynthesisAgent(BaseMistralAgent):
    def __init__(self):
        super().__init__(
            agent_name="fdd_synthesis",
            model_name="mistral-large-latest"
        )
        # Override prompts dir to point to report folder
        self.prompts_dir = os.path.join(os.path.dirname(__file__), "prompts", "report")

fdd_synthesis_agent = FDDSynthesisAgent()
