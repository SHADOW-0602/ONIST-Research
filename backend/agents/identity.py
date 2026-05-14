from backend.agents.base import BaseResearchAgent

class IdentityNormalizationAgent(BaseResearchAgent):
    def __init__(self):
        super().__init__(dimension_name="identity_normalization")

# Factory-style export
identity_agent = IdentityNormalizationAgent()
