from backend.agents.base import BaseResearchAgent

class ManagementBiographiesAgent(BaseResearchAgent):
    def __init__(self):
        super().__init__(dimension_name="management_bios")

# Factory-style export
management_bios_agent = ManagementBiographiesAgent()
