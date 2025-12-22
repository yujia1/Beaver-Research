from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
import httpx
import os
from datetime import datetime

router = APIRouter()

# Get FMP API key from environment
FMP_API_KEY = os.getenv("FMP_API_KEY", "")
FMP_BASE_URL = "https://financialmodelingprep.com/stable"



async def fetch_fmp_data(endpoint: str, params: Dict[str, Any] = None) -> List[Dict]:
    """
    Fetch data from Financial Modeling Prep API
    """
    if not FMP_API_KEY:
        raise HTTPException(status_code=500, detail="FMP_API_KEY not configured")
    
    if params is None:
        params = {}
    
    params["apikey"] = FMP_API_KEY
    
    url = f"{FMP_BASE_URL}/{endpoint}"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, dict) and "Error Message" in data:
                raise HTTPException(status_code=400, detail=data["Error Message"])
            
            return data if isinstance(data, list) else []
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"FMP API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")


@router.get("/income-statement/{ticker}")
async def get_income_statement(
    ticker: str,
    period: str = "annual",  # annual or quarter
    limit: int = 5
):
    """
    Fetch income statement data for a ticker
    """
    ticker = ticker.upper()
    endpoint = f"income-statement"
    params = {"symbol": ticker, "period": period, "limit": limit}
    
    data = await fetch_fmp_data(endpoint, params)
    
    if not data:
        raise HTTPException(status_code=404, detail=f"No income statement data found for {ticker}")
    
    return {
        "ticker": ticker,
        "period": period,
        "data": data
    }



@router.get("/cash-flow/{ticker}")
async def get_cash_flow(
    ticker: str,
    period: str = "annual",
    limit: int = 5
):
    """
    Fetch cash flow statement data for a ticker
    """
    ticker = ticker.upper()
    endpoint = f"cash-flow-statement"
    params = {"symbol": ticker, "period": period, "limit": limit}
    
    data = await fetch_fmp_data(endpoint, params)
    
    if not data:
        raise HTTPException(status_code=404, detail=f"No cash flow data found for {ticker}")
    
    return {
        "ticker": ticker,
        "period": period,
        "data": data
    }


@router.get("/balance-sheet/{ticker}")
async def get_balance_sheet(
    ticker: str,
    period: str = "annual",
    limit: int = 5
):
    """
    Fetch balance sheet data for a ticker
    """
    ticker = ticker.upper()
    endpoint = f"balance-sheet-statement"
    params = {"symbol": ticker, "period": period, "limit": limit}
    
    data = await fetch_fmp_data(endpoint, params)
    
    if not data:
        raise HTTPException(status_code=404, detail=f"No balance sheet data found for {ticker}")
    
    return {
        "ticker": ticker,
        "period": period,
        "data": data
    }


@router.get("/key-metrics/{ticker}")
async def get_key_metrics(
    ticker: str,
    period: str = "annual",
    limit: int = 5
):
    """
    Fetch key metrics for a ticker
    """
    ticker = ticker.upper()
    endpoint = f"key-metrics"
    params = {"symbol": ticker, "period": period, "limit": limit}
    
    data = await fetch_fmp_data(endpoint, params)
    
    if not data:
        raise HTTPException(status_code=404, detail=f"No key metrics data found for {ticker}")
    
    return {
        "ticker": ticker,
        "period": period,
        "data": data
    }


@router.get("/dcf/{ticker}")
async def get_dcf(
    ticker: str
):
    """
    Fetch DCF (Discounted Cash Flow) valuation for a ticker
    """
    ticker = ticker.upper()
    endpoint = f"discounted-cash-flow"
    params = {"symbol": ticker}
    
    data = await fetch_fmp_data(endpoint, params)
    
    return {
        "ticker": ticker,
        "data": data if data else []
    }


@router.get("/earnings-calendar/{ticker}")
async def get_earnings_calendar(
    ticker: str
):
    """
    Fetch earnings calendar for a ticker
    """
    ticker = ticker.upper()
    endpoint = f"earnings-calendar"
    params = {"symbol": ticker}
    
    data = await fetch_fmp_data(endpoint, params)
    
    return {
        "ticker": ticker,
        "data": data if data else []
    }


@router.get("/earnings-transcript/{ticker}")
async def get_earnings_transcript(
    ticker: str
):
    """
    Fetch latest earnings call transcript for a ticker
    """
    ticker = ticker.upper()
    endpoint = f"earning-call-transcript-latest"
    params = {"symbol": ticker}
    
    data = await fetch_fmp_data(endpoint, params)
    
    return {
        "ticker": ticker,
        "data": data if data else []
    }


@router.get("/revenue-segmentation/{ticker}")
async def get_revenue_segmentation(
    ticker: str
):
    """
    Fetch revenue product segmentation for a ticker
    """
    ticker = ticker.upper()
    endpoint = f"revenue-product-segmentation"
    params = {"symbol": ticker}
    
    data = await fetch_fmp_data(endpoint, params)
    
    return {
        "ticker": ticker,
        "data": data if data else []
    }


@router.get("/all/{ticker}")
async def get_all_statements(
    ticker: str,
    period: str = "annual",
    limit: int = 5
):
    """
    Fetch all financial statements for a ticker
    """
    ticker = ticker.upper()
    
    try:
        income = await get_income_statement(ticker, period, limit)
        cash_flow = await get_cash_flow(ticker, period, limit)
        balance_sheet = await get_balance_sheet(ticker, period, limit)
        revenue_seg = await get_revenue_segmentation(ticker)
        key_metrics = await get_key_metrics(ticker, period, limit)
        dcf = await get_dcf(ticker)
        earnings_calendar = await get_earnings_calendar(ticker)
        earnings_transcript = await get_earnings_transcript(ticker)
        
        return {
            "ticker": ticker,
            "period": period,
            "income_statement": income["data"],
            "cash_flow": cash_flow["data"],
            "balance_sheet": balance_sheet["data"],
            "revenue_segmentation": revenue_seg["data"],
            "key_metrics": key_metrics["data"],
            "dcf": dcf["data"],
            "earnings_calendar": earnings_calendar["data"],
            "earnings_transcript": earnings_transcript["data"]
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching statements: {str(e)}")
