from langchain_cohere import ChatCohere
from langchain_core.messages import HumanMessage, AIMessage
from backend.config import config
import logging

logger = logging.getLogger(__name__)

class CohereAdversarialDebate:
    def __init__(self, model_name: str = "command-r-plus"):
        # We use Command-R+ as it excels at RAG and multi-step reasoning
        self.bull_llm = ChatCohere(cohere_api_key=config.COHERE_API_KEY, model=model_name, temperature=0.6)
        self.bear_llm = ChatCohere(cohere_api_key=config.COHERE_API_KEY, model=model_name, temperature=0.6)
        
    async def run_debate(self, ticker: str, fdd_summary: str, rounds: int = 2) -> dict:
        """
        Simulates an AutoGen-style adversarial debate between a Bull and a Bear analyst.
        """
        logger.info(f"Starting Cohere Bull/Bear debate for {ticker}")
        
        bull_system = f"You are a fiercely bullish equity analyst for {ticker}. Defend the bull thesis aggressively against the Bear's critiques based on this summary: {fdd_summary}"
        bear_system = f"You are a fiercely bearish equity analyst for {ticker}. Attack the company's weaknesses and poke holes in the Bull's thesis based on this summary: {fdd_summary}"
        
        debate_transcript = []
        
        # Round 1: Bull Opening
        bull_opening = await self.bull_llm.ainvoke([HumanMessage(content=f"{bull_system}\n\nProvide your opening bullish thesis (max 2 paragraphs).")])
        debate_transcript.append({"agent": "Bull", "argument": bull_opening.content})
        
        # Round 1: Bear Rebuttal
        bear_opening = await self.bear_llm.ainvoke([
            HumanMessage(content=bear_system),
            AIMessage(content="Here is the Bull's opening: " + bull_opening.content + "\nProvide your bearish rebuttal.")
        ])
        debate_transcript.append({"agent": "Bear", "argument": bear_opening.content})
        
        # Subsequent rounds
        current_argument = bear_opening.content
        for i in range(1, rounds):
            # Bull responds
            bull_resp = await self.bull_llm.ainvoke([
                HumanMessage(content=bull_system),
                AIMessage(content="The Bear said: " + current_argument + "\nRefute this.")
            ])
            debate_transcript.append({"agent": "Bull", "argument": bull_resp.content})
            
            # Bear responds
            bear_resp = await self.bear_llm.ainvoke([
                HumanMessage(content=bear_system),
                AIMessage(content="The Bull said: " + bull_resp.content + "\nRefute this.")
            ])
            current_argument = bear_resp.content
            debate_transcript.append({"agent": "Bear", "argument": bear_resp.content})
            
        return {
            "ticker": ticker,
            "transcript": debate_transcript
        }

debate_framework = CohereAdversarialDebate()