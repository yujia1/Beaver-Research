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


@router.get("/profile/{ticker}")
async def get_company_profile(
    ticker: str
):
    """
    Fetch company profile (description, etc)
    """
    ticker = ticker.upper()
    endpoint = f"profile"
    params = {"symbol": ticker}
    
    data = await fetch_fmp_data(endpoint, params)
    
    return {
        "ticker": ticker,
        "data": data if data else []
    }


@router.get("/executives/{ticker}")
async def get_key_executives(
    ticker: str
):
    """
    Fetch key executives
    """
    ticker = ticker.upper()
    endpoint = "key-executives"
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


async def fetch_financial_ratios_batch(tickers: List[str]) -> List[Dict]:
    """
    Helper function to fetch financial ratios for a batch of tickers
    """
    tasks = []
    for t in tickers:
        tasks.append(fetch_fmp_data("ratios-ttm", {"symbol": t}))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    final_data = []
    for i, res in enumerate(results):
        symbol = tickers[i]
        if isinstance(res, Exception):
            print(f"Error fetching ratios for {symbol}: {res}")
            continue
            
        ratio_obj = res[0] if res and isinstance(res, list) and len(res) > 0 else {}
        if ratio_obj:
            ratio_obj["symbol"] = symbol
            final_data.append(ratio_obj)
            
    return final_data


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
    
    # 2. Fetch Ratios using batch helper
    return await fetch_financial_ratios_batch(target_tickers)


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





@router.get("/historical-price/{ticker}")
async def get_historical_price(ticker: str):
    """
    Fetch historical price data for a ticker
    """
    ticker = ticker.upper()
    data = await get_historical_price_full(ticker)
    return {"ticker": ticker, "data": data.get("historical", []) if isinstance(data, dict) else []}

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
    endpoint = "senate-trades-by-name"
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
    endpoint = "house-trades-by-name"
    params = {"name": name}
    
    try:
        data = await fetch_fmp_data(endpoint, params)
        return {"name": name, "data": data if isinstance(data, list) else []}
    except Exception as e:
        print(f"Error fetching house trades by name: {e}")
        return {"name": name, "data": []}


@router.get("/news/{ticker}")
async def get_stock_news(ticker: str, limit: int = 20, page: int = 0):
    """
    Fetch stock news
    """
    ticker = ticker.upper()
    endpoint = "news/stock"
    params = {"symbols": ticker, "limit": limit, "page": page}
    
    try:
        data = await fetch_fmp_data(endpoint, params)
        return {"ticker": ticker, "data": data if isinstance(data, list) else []}
    except Exception as e:
        print(f"Error fetching stock news: {e}")
        return {"ticker": ticker, "data": []}


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
        loop = asyncio.get_running_loop()

        # Define all tasks
        tasks = [
            get_income_statement(ticker, period, limit),
            get_cash_flow(ticker, period, limit),
            get_balance_sheet(ticker, period, limit),
            get_revenue_segmentation(ticker),
            get_dcf(ticker),
            get_earnings_calendar(ticker),
            get_employee_count(ticker),
            get_key_metrics_ttm(ticker),
            get_financial_ratios_analysis(ticker),
            get_earnings_data(ticker),
            get_stock_dividends(ticker),
            get_stock_splits(ticker),
            get_insider_trading(ticker),
            get_senate_trades(ticker),
            get_house_trades(ticker),
            get_historical_price_full(ticker),
            get_company_profile(ticker),
            get_key_executives(ticker),
            get_stock_news(ticker),
            # Run SEC blocking calls in executor
            loop.run_in_executor(None, edgar_service.get_recent_filings, ticker, 100)
        ]

        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Unpack results safely
        def get_result(index, default_val=None):
            res = results[index]
            if isinstance(res, Exception):
                print(f"Task {index} failed for {ticker}: {res}")
                return default_val
            return res

        # Map results to variables (indices match task order)
        income = get_result(0, {"data": []})
        cash_flow = get_result(1, {"data": []})
        balance_sheet = get_result(2, {"data": []})
        revenue_seg = get_result(3, {"data": []})
        dcf = get_result(4, {"data": []})
        earnings_calendar = get_result(5, {"data": []})
        employee_count = get_result(6, {"data": []})
        key_metrics = get_result(7, {"data": []})
        financial_ratios = get_result(8, [])
        earnings = get_result(9, {"data": []})
        dividends = get_result(10, {"data": []})
        splits = get_result(11, {"data": []})
        insider_trading = get_result(12, {"data": []})
        senate_trades = get_result(13, {"data": []})
        house_trades = get_result(14, {"data": []})
        historical_price = get_result(15, {"historical": []})
        profile_res = get_result(16, {})
        executives_res = get_result(17, {})
        news_res = get_result(18, {"data": []})
        filings_data = get_result(19, [])

        # Process Business Description from FMP Profile
        business_description = ""
        profile_data = profile_res.get("data", [])
        if profile_data and isinstance(profile_data, list) and len(profile_data) > 0:
            business_description = profile_data[0].get("description", "")
        
        mergers_acquisitions = {"data": []}

        return {
            "ticker": ticker,
            "business_description": business_description,
            "historical_price": historical_price.get("historical", []) if isinstance(historical_price, dict) else [],
            "period": period,
            "income_statement": income.get("data", []) if isinstance(income, dict) else [],
            "cash_flow": cash_flow.get("data", []) if isinstance(cash_flow, dict) else [],
            "balance_sheet": balance_sheet.get("data", []) if isinstance(balance_sheet, dict) else [],
            "revenue_segmentation": revenue_seg.get("data", []) if isinstance(revenue_seg, dict) else [],
            "dcf": dcf.get("data", []) if isinstance(dcf, dict) else [],
            "earnings_calendar": earnings_calendar.get("data", []) if isinstance(earnings_calendar, dict) else [],
            "employee_count": employee_count.get("data", []) if isinstance(employee_count, dict) else [],
            "mergers_acquisitions": mergers_acquisitions["data"],
            "filings": filings_data if isinstance(filings_data, list) else [],
            "key_metrics": key_metrics.get("data", []) if isinstance(key_metrics, dict) else [],
            "financial_ratios": financial_ratios if isinstance(financial_ratios, list) else [],
            "earnings": earnings.get("data", []) if isinstance(earnings, dict) else [],
            "dividends": dividends.get("data", []) if isinstance(dividends, dict) else [],
            "splits": splits.get("data", []) if isinstance(splits, dict) else [],
            "insider_trading": insider_trading.get("data", []) if isinstance(insider_trading, dict) else [],
            "senate_trades": senate_trades.get("data", []) if isinstance(senate_trades, dict) else [],
            "house_trades": house_trades.get("data", []) if isinstance(house_trades, dict) else [],
            "executives": executives_res.get("data", []) if isinstance(executives_res, dict) else [],
            "stock_news": news_res.get("data", []) if isinstance(news_res, dict) else []
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching statements: {str(e)}")

from pydantic import BaseModel

class TickerList(BaseModel):
    tickers: List[str]

@router.post("/financial-ratios-comparison")
async def get_financial_ratios_comparison(payload: TickerList):
    """
    Fetch Financial Ratios for a specific list of tickers
    """
    target_tickers = [t.upper() for t in payload.tickers]
    return await fetch_financial_ratios_batch(target_tickers)
