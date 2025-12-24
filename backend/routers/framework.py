from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
import httpx
import os
import asyncio
from datetime import datetime, timedelta
from services.edgar_service import edgar_service

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
                # Some errors are dicts
                raise HTTPException(status_code=400, detail=data["Error Message"])
            
            # Return data directly; caller handles dict vs list
            return data
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"FMP API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")

async def fetch_fmp_v4_data(endpoint: str, params: Dict[str, Any] = None) -> List[Dict]:
    """
    Fetch data from Financial Modeling Prep API v4
    """
    if not FMP_API_KEY:
        raise HTTPException(status_code=500, detail="FMP_API_KEY not configured")
    
    if params is None:
        params = {}
    
    params["apikey"] = FMP_API_KEY
    
    url = f"https://financialmodelingprep.com/api/v4/{endpoint}"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, dict) and "Error Message" in data:
                raise HTTPException(status_code=400, detail=data["Error Message"])
            
            return data if isinstance(data, list) else []
    except httpx.HTTPStatusError as e:
         # Log but don't crash, return empty list for peers if v4 fails
        print(f"FMP V4 API error: {str(e)}")
        return []
    except Exception as e:
        print(f"Error fetching v4 data: {str(e)}")
        return []

    except Exception as e:
        print(f"Error fetching v4 data: {str(e)}")
        return []



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


@router.get("/employee-count/{ticker}")
async def get_employee_count(
    ticker: str
):
    """
    Fetch historical employee count for a ticker
    """
    ticker = ticker.upper()
    endpoint = f"historical-employee-count"
    params = {"symbol": ticker}
    
    data = await fetch_fmp_data(endpoint, params)
    
    return {
        "ticker": ticker,
        "data": data if data else []
    }


@router.get("/mergers-acquisitions")
async def get_mergers_acquisitions(
    ticker: str,
    limit: int = 10
):
    """
    Fetch mergers and acquisitions for a specific ticker
    If specific search is restricted, we fetch latest global and filter.
    """
    # Fallback to latest global feed as specific search is restricted for some keys
    endpoint = "mergers-acquisitions-latest"
    # Fetch a larger batch to filter from
    params = {"limit": 100}
    
    try:
        data = await fetch_fmp_data(endpoint, params)
        
        if not data:
            return {"data": []}
            
        # Filter for the requested ticker (either as acquirer or target)
        filtered_data = [
            item for item in data 
            if item.get("symbol") == ticker or item.get("targetedSymbol") == ticker
        ]
        
        return {
            "data": filtered_data[:limit]
        }
    except Exception as e:
        print(f"Error fetching M&A: {e}")
        return {"data": []}



@router.get("/sec-filings/{ticker}")
async def get_sec_filings(
    ticker: str,
    limit: int = 100
):
    """
    Fetch SEC filings for a ticker
    """
    ticker = ticker.upper()
    try:
        loop = asyncio.get_running_loop()
        formatted_data = await loop.run_in_executor(None, edgar_service.get_recent_filings, ticker, limit)
    except Exception as e:
        print(f"Error fetching SEC filings: {e}")
        formatted_data = []
    
    return {
        "ticker": ticker,
        "data": formatted_data
    }


    return {
        "ticker": ticker,
        "data": formatted_data
    }


@router.get("/key-metrics-ttm/{ticker}")
async def get_key_metrics_ttm(
    ticker: str
):
    """
    Fetch Key Metrics TTM for a ticker
    """
    ticker = ticker.upper()
    endpoint = "key-metrics-ttm"
    params = {"symbol": ticker}
    
    data = await fetch_fmp_data(endpoint, params)
    
    return {
        "ticker": ticker,
        "data": data if data else []
    }


async def get_financial_ratios_analysis(ticker: str):
    """
    Fetch Financial Ratios for ticker and its peers (Comparison)
    """
    ticker = ticker.upper()
    
    # 1. Get Peers
    try:
        peers_data = await fetch_fmp_data("stock-peers", {"symbol": ticker})
        peers = []
        if peers_data and isinstance(peers_data, list):
             # Response is list of peer objects: [{"symbol": "PEER1", ...}, ...]
             peers = [p.get("symbol") for p in peers_data if p.get("symbol")]
    except Exception as e:
        print(f"Error fetching peers: {e}")
        peers = []

    # Limit peers to keep table manageable (e.g. 6 peers)
    target_tickers = [ticker] + peers[:6]
    
    # 2. Fetch Ratios for each
    tasks = []
    for t in target_tickers:
        # ratios-ttm
        tasks.append(fetch_fmp_data("ratios-ttm", {"symbol": t}))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    final_data = []
    for i, res in enumerate(results):
        symbol = target_tickers[i]
        if isinstance(res, Exception):
            print(f"Error fetching ratios for {symbol}: {res}")
            continue
            
        # res is typically [{"dividendYielTTM": ... }]
        ratio_obj = res[0] if res and isinstance(res, list) and len(res) > 0 else {}
        if ratio_obj:
            # Inject symbol into the object for the frontend to identify column
            ratio_obj["symbol"] = symbol
            final_data.append(ratio_obj)
            
    return final_data




async def get_historical_price_full(ticker: str, from_date: str = None, to_date: str = None) -> Dict[str, Any]:
    """
    Fetch full historical price data (Daily)
    """
    endpoint = "historical-price-eod/full"
    params = {"symbol": ticker}
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date
        
    try:
        data = await fetch_fmp_data(endpoint, params)
        if isinstance(data, dict):
             return data
        if isinstance(data, list):
             return {"historical": data}
        return {"historical": []}
    except Exception as e:
        print(f"Error fetching historical price: {e}")
        return {"historical": []}




@router.get("/economic-calendar")
async def get_economic_calendar(from_date: Optional[str] = None, to_date: Optional[str] = None):
    """
    Fetch economic calendar from FMP.
    If no dates provided, defaults to today.
    """
    if not from_date:
        from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    if not to_date:
        to_date = datetime.now().strftime("%Y-%m-%d")

    params = {"from": from_date, "to": to_date}
    try:
        data = await fetch_fmp_data("economic-calendar", params)
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"Error fetching economic calendar: {e}")
        return []


@router.get("/earnings/{ticker}")
async def get_earnings_data(ticker: str):
    """Fetch earnings data"""
    ticker = ticker.upper()
    data = await fetch_fmp_data("earnings", {"symbol": ticker})
    return {"ticker": ticker, "data": data if data else []}


@router.get("/dividends/{ticker}")
async def get_stock_dividends(ticker: str):
    """Fetch dividends data"""
    ticker = ticker.upper()
    data = await fetch_fmp_data("dividends", {"symbol": ticker})
    return {"ticker": ticker, "data": data if data else []}


@router.get("/splits/{ticker}")
async def get_stock_splits(ticker: str):
    """Fetch splits data"""
    ticker = ticker.upper()
    data = await fetch_fmp_data("splits", {"symbol": ticker})
    return {"ticker": ticker, "data": data if data else []}


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


@router.get("/insider-trading/{ticker}")
async def get_insider_trading(ticker: str, page: int = 0, limit: int = 50):
    """
    Fetch insider trading data
    """
    ticker = ticker.upper()
    # Endpoint: insider-trading/search?symbol=AAPL&page=0&limit=50
    # Base URL is stable (v3), so we pass "insider-trading/search"
    endpoint = "insider-trading/search"
    params = {"symbol": ticker, "page": page, "limit": limit}
    
    try:
        data = await fetch_fmp_data(endpoint, params)
        return {"ticker": ticker, "data": data if isinstance(data, list) else []}
    except Exception as e:
        print(f"Error fetching insider trading: {e}")
        return {"ticker": ticker, "data": []}




@router.get("/senate-trades/{ticker}")
async def get_senate_trades(ticker: str):
    """
    Fetch Senate trades
    """
    ticker = ticker.upper()
    endpoint = "senate-trades"
    params = {"symbol": ticker}
    
    try:
        data = await fetch_fmp_data(endpoint, params)
        return {"ticker": ticker, "data": data if isinstance(data, list) else []}
    except Exception as e:
        print(f"Error fetching senate trades: {e}")
        return {"ticker": ticker, "data": []}


@router.get("/house-trades/{ticker}")
async def get_house_trades(ticker: str):
    """
    Fetch House trades
    """
    ticker = ticker.upper()
    endpoint = "house-trades"
    params = {"symbol": ticker}
    
    try:
        data = await fetch_fmp_data(endpoint, params)
        return {"ticker": ticker, "data": data if isinstance(data, list) else []}
    except Exception as e:
        print(f"Error fetching house trades: {e}")
        return {"ticker": ticker, "data": []}


@router.get("/senate-trades-by-name")
async def get_senate_trades_by_name(name: str):
    """
    Fetch Senate trades by Name
    """
    endpoint = "senate-trades"
    params = {"name": name}
    
    try:
        data = await fetch_fmp_data(endpoint, params)
        return {"name": name, "data": data if isinstance(data, list) else []}
    except Exception as e:
        print(f"Error fetching senate trades by name: {e}")
        return {"name": name, "data": []}


@router.get("/house-trades-by-name")
async def get_house_trades_by_name(name: str):
    """
    Fetch House trades by Name
    """
    endpoint = "house-trades"
    params = {"name": name}
    
    try:
        data = await fetch_fmp_data(endpoint, params)
        return {"name": name, "data": data if isinstance(data, list) else []}
    except Exception as e:
        print(f"Error fetching house trades by name: {e}")
        return {"name": name, "data": []}


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
        dcf = await get_dcf(ticker)
        earnings_calendar = await get_earnings_calendar(ticker)
        employee_count = await get_employee_count(ticker)
        mergers_acquisitions = {"data": []} # await get_mergers_acquisitions(ticker)
        
        # Fetch Filings from SEC (via EdgarService)
        try:
            loop = asyncio.get_running_loop()
            filings_data = await loop.run_in_executor(None, edgar_service.get_recent_filings, ticker, 100)
        except Exception as e:
            print(f"Error fetching SEC filings: {e}")
            filings_data = []


        key_metrics = await get_key_metrics_ttm(ticker)
        financial_ratios = await get_financial_ratios_analysis(ticker)
        earnings = await get_earnings_data(ticker)
        dividends = await get_stock_dividends(ticker)
        splits = await get_stock_splits(ticker)
        insider_trading = await get_insider_trading(ticker)
        senate_trades = await get_senate_trades(ticker)
        house_trades = await get_house_trades(ticker)

        # Fetch Business Description from 10-K (Item 1)
        business_description = ""
        try:
            loop = asyncio.get_running_loop()
            ten_k_content = await loop.run_in_executor(None, edgar_service.get_latest_10k_content, ticker)
            if ten_k_content and "chunk_a" in ten_k_content:
                business_description = ten_k_content["chunk_a"]
        except Exception as e:
            print(f"Error fetching 10-K content: {e}")

        # Fetch Historical Price
        historical_price = await get_historical_price_full(ticker)
        
        return {
            "ticker": ticker,
            "business_description": business_description,
            "historical_price": historical_price.get("historical", []),
            "period": period,
            "income_statement": income["data"],
            "cash_flow": cash_flow["data"],
            "balance_sheet": balance_sheet["data"],
            "revenue_segmentation": revenue_seg["data"],
            "dcf": dcf["data"],
            "earnings_calendar": earnings_calendar["data"],
            "employee_count": employee_count["data"],
            "mergers_acquisitions": mergers_acquisitions["data"],
            "filings": filings_data,
            "key_metrics": key_metrics["data"],
            "financial_ratios": financial_ratios,
            "earnings": earnings["data"],
            "dividends": dividends["data"],
            "splits": splits["data"],
            "insider_trading": insider_trading["data"],
            "senate_trades": senate_trades["data"],
            "house_trades": house_trades["data"]
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching statements: {str(e)}")
