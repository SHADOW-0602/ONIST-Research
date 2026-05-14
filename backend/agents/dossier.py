from backend.agents.base import BaseResearchAgent

class DossierAgent(BaseResearchAgent):
    def __init__(self):
        super().__init__(dimension_name="dossier")

# Factory-style export
dossier_agent = DossierAgent()