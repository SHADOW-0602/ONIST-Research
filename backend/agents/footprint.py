from backend.agents.base import BaseResearchAgent

class FootprintAgent(BaseResearchAgent):
    def __init__(self):
        super().__init__(dimension_name="footprint")

# Factory-style export
footprint_agent = FootprintAgent()