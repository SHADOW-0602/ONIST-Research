import logging
from typing import Dict, Any, Optional
from backend.ingestion.edgar_client import edgar_client
from backend.ingestion.openfigi_client import openfigi_client
from backend.ingestion.polygon_client import polygon_client

logger = logging.getLogger(__name__)

class IdentityEnricher:
    """
    Unified service to enrich company identity from multiple sources:
    1. SEC EDGAR (CIK, Legal Name, Auditor, Subsidiaries, Parent)
    2. OpenFIGI (Exchange Codes, FIGI, Composite identifiers)
    3. Polygon.io (CIK verification, Primary Exchange, Company Metadata)
    """

    def enrich_identity(self, ticker: str) -> Dict[str, Any]:
        """
        Performs a multi-stage identity enrichment for a given ticker.
        Returns a structured dictionary with values, sources, and confidence levels.
        """
        logger.info(f"Starting identity enrichment for {ticker}")
        
        # 1. Fetch data from all sources
        metadata = edgar_client.download_filings(ticker, amount=1)
        edgar_dei = metadata.get("dei", {})
        
        figi_data = openfigi_client.map_ticker(ticker)
        poly_data = polygon_client.get_ticker_details(ticker)

        # 2. Build the structured profile
        profile = {
            "primary_ticker": {
                "value": ticker,
                "exchange": poly_data.get("exchange") or figi_data.get("exchange"),
                "source": "Polygon.io" if poly_data.get("exchange") else ("OpenFIGI" if figi_data.get("exchange") else "System"),
                "verified": True if poly_data.get("ticker") == ticker else False,
                "confidence": "high"
            },
            "trading_name": {
                "value": poly_data.get("name") or edgar_dei.get("legal_name"),
                "source": "Polygon.io" if poly_data.get("name") else "SEC EDGAR",
                "verified": True if poly_data.get("name") else False,
                "confidence": "high" if poly_data.get("name") else "medium"
            },
            "cik": {
                "value": poly_data.get("cik") or edgar_dei.get("cik"),
                "source": "Polygon.io" if poly_data.get("cik") else "SEC EDGAR",
                "verified": True if poly_data.get("cik") and edgar_dei.get("cik") and str(int(poly_data.get("cik"))) == str(int(edgar_dei.get("cik"))) else False,
                "confidence": "high" if poly_data.get("cik") else "medium"
            },
            "isin": {
                "value": figi_data.get("isin"),
                "source": "OpenFIGI" if figi_data.get("isin") else None,
                "verified": False,
                "confidence": "medium" if figi_data.get("isin") else "low"
            },
            "lei": {
                "value": edgar_dei.get("lei"),
                "source": "SEC EDGAR" if edgar_dei.get("lei") else None,
                "verified": False,
                "confidence": "medium" if edgar_dei.get("lei") else "low"
            },
            "incorporation_jurisdiction": {
                "value": edgar_dei.get("incorporation_jurisdiction"),
                "source": "SEC EDGAR" if edgar_dei.get("incorporation_jurisdiction") else None,
                "verified": False,
                "confidence": "medium" if edgar_dei.get("incorporation_jurisdiction") else "low"
            },
            "hq_location": {
                "value": self._format_hq_location(edgar_dei.get("hq_location"), poly_data.get("address")),
                "source": "SEC EDGAR / Polygon.io",
                "verified": False,
                "confidence": "high" if edgar_dei.get("hq_location") or poly_data.get("address") else "low"
            },
            "sic_code": {
                "value": poly_data.get("sic_code") or edgar_dei.get("sic"),
                "description": poly_data.get("sic_description"),
                "source": "Polygon.io" if poly_data.get("sic_code") else "SEC EDGAR",
                "verified": False,
                "confidence": "high" if poly_data.get("sic_code") else "medium"
            },
            "total_employees": {
                "value": poly_data.get("total_employees"),
                "source": "Polygon.io",
                "verified": False,
                "confidence": "high" if poly_data.get("total_employees") else "low"
            },
            "auditor": {
                "value": edgar_dei.get("auditor"),
                "source": "SEC EDGAR (Header/Text)",
                "verified": False,
                "confidence": "medium" if edgar_dei.get("auditor") else "low"
            },
            "parent_company": {
                "value": edgar_dei.get("parent_company"),
                "source": "SEC EDGAR",
                "verified": False,
                "confidence": "medium" if edgar_dei.get("parent_company") else "low"
            },
            "subsidiaries_note": {
                "value": edgar_dei.get("subsidiaries_note"),
                "source": "SEC EDGAR",
                "verified": False,
                "confidence": "medium" if edgar_dei.get("subsidiaries_note") else "low"
            },
            "business_description": {
                "value": poly_data.get("description"),
                "source": "Polygon.io",
                "verified": False,
                "confidence": "medium" if poly_data.get("description") else "low"
            },
            "website": {
                "value": poly_data.get("homepage_url"),
                "source": "Polygon.io",
                "verified": False,
                "confidence": "medium" if poly_data.get("homepage_url") else "low"
            },
            "additional_tickers": []
        }
            
        return profile

    def _format_hq_location(self, edgar_hq: Optional[str], poly_address: Optional[Dict[str, Any]]) -> Optional[str]:
        if edgar_hq:
            return edgar_hq
        if poly_address:
            parts = [
                poly_address.get("address1"),
                poly_address.get("city"),
                poly_address.get("state"),
                poly_address.get("postal_code")
            ]
            return ", ".join([p for p in parts if p])
        return None

identity_enricher = IdentityEnricher()
