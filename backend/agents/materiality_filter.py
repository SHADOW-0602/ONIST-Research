from backend.agents.base_mistral import BaseMistralAgent

class MaterialityFilterAgent(BaseMistralAgent):
    def __init__(self):
        super().__init__(dimension="materiality", agent_name="materiality_filter")

materiality_filter_agent = MaterialityFilterAgent()
