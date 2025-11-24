from fastapi import APIRouter, HTTPException
from services.edgar_service import edgar_service
from typing import List, Dict, Any

router = APIRouter()

@router.get("/filings/{ticker}")
async def get_sec_filings(ticker: str):
    """
    Get SEC filings for a specific ticker.
    Focuses on institutional holdings and major ownership (13F, 13D, 13G).
    """
    holdings = edgar_service.get_institutional_holdings(ticker)
    if not holdings:
        # Fallback or just empty list, don't raise error for empty data
        pass
    
    return {
        "ticker": ticker.upper(),
        "filings": holdings
    }

@router.get("/cik/{ticker}")
async def get_cik(ticker: str):
    """Get CIK for a ticker."""
    cik = edgar_service.get_cik(ticker)
    if not cik:
        raise HTTPException(status_code=404, detail="CIK not found")
    return {"ticker": ticker.upper(), "cik": cik}


