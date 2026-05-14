from backend.agents.base import BaseResearchAgent

class BusinessMechanicsAgent(BaseResearchAgent):
    def __init__(self):
        super().__init__(dimension_name="business_mechanics")

# Factory-style export
business_mechanics_agent = BusinessMechanicsAgent()
