import os
import logging
import re
from typing import Dict, Any, Optional
from sec_edgar_downloader import Downloader

logger = logging.getLogger(__name__)

class EdgarClient:
    def __init__(self, download_dir: str = "./downloads/sec"):
        self.download_dir = download_dir
        # Initialize downloader with your company name and email (required by SEC)
        self.dl = Downloader("ONIST-Research", "analyst@onist-research.com", self.download_dir)
        os.makedirs(self.download_dir, exist_ok=True)

    def parse_dei_from_header(self, file_path: str) -> Dict[str, Any]:
        """
        Robustly parse Document and Entity Information (DEI) from SEC full-submission.txt SGML header.
        """
        dei = {}
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                # Read first 5MB to ensure we catch auditor and exhibit references
                content_sample = f.read(5000000) 

            # Core patterns (Header usually in first 100KB)
            patterns = {
                "legal_name": r"COMPANY CONFORMED NAME:\s+(.+)",
                "cik": r"CENTRAL INDEX KEY:\s+(\d+)",
                "sic": r"STANDARD INDUSTRIAL CLASSIFICATION:\s+(.+)",
                "incorporation_jurisdiction": r"STATE OF INCORPORATION:\s+(\w+)",
                "fiscal_year_end": r"FISCAL YEAR END:\s+(\d+)"
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, content_sample[:100000], re.IGNORECASE)
                if match:
                    dei[key] = match.group(1).strip()
            
            # Extract Business Address for HQ Location
            # We look for the section starting with BUSINESS ADDRESS:
            # and then pull the fields that follow.
            address_match = re.search(r"BUSINESS ADDRESS:\s*(.*?)MAIL ADDRESS:", content_sample[:100000], re.DOTALL | re.IGNORECASE)
            if not address_match:
                address_match = re.search(r"BUSINESS ADDRESS:\s*(.*?)COMPANY DATA:", content_sample[:100000], re.DOTALL | re.IGNORECASE)
            
            target_content = address_match.group(1) if address_match else content_sample[:100000]
            
            address_parts = []
            for field in ["STREET 1", "CITY", "STATE", "ZIP"]:
                # Use a pattern that matches the field and then anything until the end of line or next field
                f_match = re.search(rf"{field}:\s+(.+)", target_content, re.IGNORECASE)
                if f_match:
                    address_parts.append(f_match.group(1).strip())
            
            if address_parts:
                dei["hq_location"] = ", ".join(address_parts)

            # --- EXTENDED EXTRACTION (From Sample) ---
            # Search for Auditor (Big Four + others)
            # We unescape HTML for easier matching
            text_to_search = content_sample.replace("&amp;", "&")
            
            auditor_names = ["Ernst & Young", "PricewaterhouseCoopers", "Deloitte", "KPMG", "BDO", "Grant Thornton", "RSM"]
            for name in auditor_names:
                # Look for the name specifically in the context of accounting/audit
                # Use word boundaries to avoid matching partial strings like CarriersMember
                if re.search(rf"\b{re.escape(name)}\b", text_to_search, re.IGNORECASE):
                    # Basic confirmation: is it near an audit keyword?
                    context_match = re.search(rf"(?:Accounting|Accountant|Auditor|Audit|Firm)(?:.{{0,1000}}){re.escape(name)}", text_to_search, re.DOTALL | re.IGNORECASE)
                    if not context_match:
                         context_match = re.search(rf"{re.escape(name)}(?:.{{0,1000}})(?:Accounting|Accountant|Auditor|Audit|Firm)", text_to_search, re.DOTALL | re.IGNORECASE)
                    
                    if context_match:
                        dei["auditor"] = name + " LLP" if "LLP" not in name else name
                        break
            
            # Search for LEI (Legal Entity Identifier)
            lei_match = re.search(r"LEI[:\s]+([A-Z0-9]{20})", text_to_search, re.IGNORECASE)
            if lei_match:
                dei["lei"] = lei_match.group(1).strip()
                
            # Search for Subsidiaries Note (Exhibit 21)
            if re.search(r"Exhibit 21|EX-21", text_to_search, re.IGNORECASE):
                dei["subsidiaries_note"] = "List of subsidiaries is available in Exhibit 21 to this report."
            
            # Parent Company
            # If the company is listed, it's often the top-level parent
            if "legal_name" in dei:
                dei["parent_company"] = "None" # Default to none if it's the main registrant

        except Exception as e:
            logger.error(f"Error parsing DEI from {file_path}: {e}")
            
        return dei

    def download_filings(self, ticker: str, amount: int = 1) -> Dict[str, Any]:
        """Downloads latest filings and returns extracted DEI metadata."""
        metadata = {"ticker": ticker, "dei": {}}
        try:
            logger.info(f"Downloading {amount} latest 10-K for {ticker}...")
            self.dl.get("10-K", ticker, limit=amount)
            
            logger.info(f"Downloading {amount} latest 10-Q for {ticker}...")
            self.dl.get("10-Q", ticker, limit=amount)
            
            # Try to find the latest 10-K to parse DEI
            ticker_dir = os.path.join(self.download_dir, "sec-edgar-filings", ticker, "10-K")
            if os.path.exists(ticker_dir):
                accessions = sorted(os.listdir(ticker_dir), reverse=True)
                if accessions:
                    submission_path = os.path.join(ticker_dir, accessions[0], "full-submission.txt")
                    if os.path.exists(submission_path):
                        metadata["dei"] = self.parse_dei_from_header(submission_path)
            
            return metadata
        except Exception as e:
            logger.error(f"SEC Edgar download failed for {ticker}: {str(e)}")
            return metadata

edgar_client = EdgarClient()