import http.client
import json
import logging
from backend.config import config

logger = logging.getLogger(__name__)

class FinvizClient:
    def __init__(self):
        self.host = "finviz-data-api.p.rapidapi.com"
        self.headers = {
            'x-rapidapi-key': config.RAPIDAPI_KEY,
            'x-rapidapi-host': self.host,
            'Content-Type': "application/json"
        }

    def get_metrics(self, ticker: str) -> dict:
        """Fetches comprehensive ticker data from Finviz via RapidAPI."""
        try:
            conn = http.client.HTTPSConnection(self.host)
            conn.request("GET", f"/quote?ticker={ticker}", headers=self.headers)
            
            res = conn.getresponse()
            data = res.read()
            
            result = json.loads(data.decode("utf-8"))
            
            # Extract and flatten the structure
            metrics = result.get("quote", {})
            metrics["analyst_ratings"] = result.get("analystRatings", [])
            metrics["news"] = result.get("news", [])
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error fetching Finviz data for {ticker}: {str(e)}")
            return {}

finviz_client = FinvizClient()