from backend.agents.base import BaseResearchAgent

class BusinessSegmentsAgent(BaseResearchAgent):
    def __init__(self):
        super().__init__(dimension_name="business_segments")

# Factory-style export
business_segments_agent = BusinessSegmentsAgent()
