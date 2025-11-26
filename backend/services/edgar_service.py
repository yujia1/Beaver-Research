import requests
import json
import os
from typing import Optional, Dict, List, Any
import datetime

class EdgarService:
    """
    Service to interact with SEC EDGAR API.
    """
    def __init__(self):
        # SEC requires a User-Agent with contact info (email)
        self.headers = {
            "User-Agent": "FinancialDashboard contact@example.com"  # Replace with valid email in prod
        }
        self.cik_map = {}
        self._load_cik_map()

    def _load_cik_map(self):
        """Load ticker -> CIK mapping from SEC bulk data."""
        try:
            url = "https://www.sec.gov/files/company_tickers.json"
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Data format: {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}, ...}
                for entry in data.values():
                    self.cik_map[entry["ticker"]] = str(entry["cik_str"]).zfill(10)
        except Exception as e:
            print(f"Error loading CIK map: {e}")

    def get_cik(self, ticker: str) -> Optional[str]:
        """Get CIK for a ticker."""
        return self.cik_map.get(ticker.upper())

    def get_company_submissions(self, ticker: str) -> Dict[str, Any]:
        """Get company submissions including recent filings."""
        cik = self.get_cik(ticker)
        if not cik:
            # Try to reload map if not found
            self._load_cik_map()
            cik = self.get_cik(ticker)
            if not cik:
                return {"error": "CIK not found"}

        try:
            url = f"https://data.sec.gov/submissions/CIK{cik}.json"
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            return {"error": f"SEC API returned {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def get_institutional_holdings(self, ticker: str) -> List[Dict[str, Any]]:
        """
        Get institutional holdings from 13F filings.
        Note: SEC API provides raw filings. Parsing 13F XML/Text is complex.
        For this simplified version, we'll look for 13F-HR filings in submissions
        and return metadata, as parsing full holdings requires processing the primary document.
        """
        data = self.get_company_submissions(ticker)
        if "error" in data:
            return []

        filings = data.get("filings", {}).get("recent", {})
        if not filings:
            return []

        forms = filings.get("form", [])
        dates = filings.get("filingDate", [])
        accession_numbers = filings.get("accessionNumber", [])
        primary_docs = filings.get("primaryDocument", [])

        holdings_filings = []
        for i, form in enumerate(forms):
            if form in ["13F-HR", "13F-NT", "13D", "13G", "SC 13D", "SC 13G"]:
                accession = accession_numbers[i].replace("-", "")
                primary_doc = primary_docs[i]
                filing_url = f"https://www.sec.gov/Archives/edgar/data/{data['cik']}/{accession}/{primary_doc}"
                
                holdings_filings.append({
                    "form": form,
                    "date": dates[i],
                    "link": filing_url,
                    "description": f"Institutional/Beneficial Ownership Filing ({form})"
                })
        
        return holdings_filings

edgar_service = EdgarService()



