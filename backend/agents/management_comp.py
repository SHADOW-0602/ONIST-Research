from backend.agents.base import BaseResearchAgent

class ManagementCompensationAgent(BaseResearchAgent):
    def __init__(self):
        super().__init__(dimension_name="management_comp")

# Factory-style export
management_comp_agent = ManagementCompensationAgent()
