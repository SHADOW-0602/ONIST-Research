from backend.agents.base import BaseResearchAgent

class SectorClassificationAgent(BaseResearchAgent):
    def __init__(self):
        super().__init__(dimension_name="sector_classification")

# Factory-style export
sector_agent = SectorClassificationAgent()
