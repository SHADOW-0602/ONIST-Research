from backend.agents.base import BaseResearchAgent

class BusinessStrategyAgent(BaseResearchAgent):
    def __init__(self):
        super().__init__(dimension_name="business_strategy")

# Factory-style export
business_strategy_agent = BusinessStrategyAgent()
