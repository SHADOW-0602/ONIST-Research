import requests
import logging
from typing import Dict, Any, Optional, List
from backend.config import config

logger = logging.getLogger(__name__)

class OpenFigiClient:
    """
    Client for interacting with the OpenFIGI API to resolve financial instrument identifiers.
    """
    BASE_URL = "https://api.openfigi.com/v3/mapping"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.OPENFIGI_API_KEY
        self.headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            self.headers["X-OPENFIGI-APIKEY"] = self.api_key

    def map_ticker(self, ticker: str, exchange_code: Optional[str] = "US") -> Dict[str, Any]:
        """
        Maps a ticker symbol to financial identifiers like ISIN and FIGI.
        """
        payload = [
            {
                "idType": "TICKER",
                "idValue": ticker,
            }
        ]
        if exchange_code:
            payload[0]["exchCode"] = exchange_code

        try:
            response = requests.post(self.BASE_URL, json=payload, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            if not data or "data" not in data[0]:
                logger.warning(f"No FIGI data found for ticker: {ticker}")
                return {}

            # Usually the first result is the most relevant
            best_match = data[0]["data"][0]
            
            # Extract useful fields
            result = {
                "figi": best_match.get("figi"),
                "isin": best_match.get("metadata", {}).get("isin") or best_match.get("isin"),
                "exchange": best_match.get("exchCode"),
                "composite_figi": best_match.get("compositeFigi"),
                "share_class_figi": best_match.get("shareClassFigi"),
                "security_type": best_match.get("securityType"),
                "market_sector": best_match.get("marketSector"),
                "ticker": best_match.get("ticker"),
                "name": best_match.get("name")
            }
            
            # OpenFIGI sometimes puts ISIN in the top level of the match
            if not result["isin"]:
                # Try finding ISIN in other matches if multiple exist
                for match in data[0]["data"]:
                    if "isin" in match:
                        result["isin"] = match["isin"]
                        break

            return result

        except Exception as e:
            logger.error(f"Error calling OpenFIGI for {ticker}: {e}")
            return {}

openfigi_client = OpenFigiClient()
