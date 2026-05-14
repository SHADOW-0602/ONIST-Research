from backend.agents.base_cohere import BaseCohereAgent

class BullBearAgent(BaseCohereAgent):
    def __init__(self):
        super().__init__(
            dimension="report",
            agent_name="bull_bear_debate",
            model_name="command-r-plus-08-2024"
        )

class ConflictResolutionAgent(BaseCohereAgent):
    def __init__(self):
        super().__init__(
            dimension="report",
            agent_name="conflict_resolution",
            model_name="command-r-plus-08-2024"
        )

bull_bear_agent = BullBearAgent()
conflict_resolution_agent = ConflictResolutionAgent()
