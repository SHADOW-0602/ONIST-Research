import requests
import logging
from typing import Dict, Any, Optional
from backend.config import config

logger = logging.getLogger(__name__)

class PolygonClient:
    """
    Client for interacting with Polygon.io API to fetch ticker metadata (CIK, Exchange).
    """
    BASE_URL = "https://api.polygon.io/v3/reference/tickers"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.POLYGON_API_KEY
        self.params = {"apiKey": self.api_key}

    def get_ticker_details(self, ticker: str) -> Dict[str, Any]:
        """
        Fetches ticker details including CIK and primary exchange.
        """
        if not self.api_key:
            logger.warning("Polygon API key not found in config.")
            return {}

        url = f"{self.BASE_URL}/{ticker}"
        try:
            response = requests.get(url, params=self.params)
            response.raise_for_status()
            data = response.json()

            if "results" not in data:
                logger.warning(f"No results found in Polygon for {ticker}")
                return {}

            results = data["results"]
            
            return {
                "ticker": results.get("ticker"),
                "name": results.get("name"),
                "cik": results.get("cik"),
                "exchange": results.get("primary_exchange"),
                "market": results.get("market"),
                "locale": results.get("locale"),
                "description": results.get("description"),
                "homepage_url": results.get("homepage_url"),
                "total_employees": results.get("total_employees"),
                "list_date": results.get("list_date"),
                "address": results.get("address"),
                "phone_number": results.get("phone_number")
            }

        except Exception as e:
            logger.error(f"Error calling Polygon for {ticker}: {e}")
            return {}

polygon_client = PolygonClient()