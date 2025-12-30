from fastapi import APIRouter, HTTPException
from redis_client import redis_client
import httpx
import os
import yfinance as yf
import pandas as pd
from typing import List, Dict, Any

router = APIRouter()

# FMP Base URL extracted and centralized
FMP_BASE_URL = "https://financialmodelingprep.com/stable"

# Define API KEY at module level
FMP_API_KEY = os.getenv("FMP_API_KEY", "")

@router.get("/regional")
async def get_regional_indices():
    """
    Fetch global market indices organized by region using Financial Modeling Prep API.
    Returns indices grouped by: United States, Europe, Asia-Pacific, Canada, Emerging Markets, Global
    """
    
    if not FMP_API_KEY:
        raise HTTPException(status_code=500, detail="FMP_API_KEY not configured")
    
    # Define indices by region - using verified indices symbols
    regional_indices = {
        "United States": [
            {"symbol": "^GSPC", "name": "S&P 500"},
            {"symbol": "^DJI", "name": "Dow Jones"},
            {"symbol": "^IXIC", "name": "NASDAQ"},
            {"symbol": "^NYA", "name": "NYSE Composite"},
            {"symbol": "^RUT", "name": "Russell 2000"},
            {"symbol": "^RUA", "name": "Russell 3000"}
        ],
        "Europe": [
            {"symbol": "^STOXX", "name": "STOXX 600"},
            {"symbol": "^GDAXI", "name": "DAX"},
            {"symbol": "^FCHI", "name": "CAC 40"},
            {"symbol": "^FTSE", "name": "FTSE 100"},
            {"symbol": "^IBEX", "name": "IBEX 35"},
            {"symbol": "FTSEMIB.MI", "name": "FTSE MIB"}
        ],
        "Asia-Pacific": [
            {"symbol": "^N225", "name": "Nikkei 225"},
            {"symbol": "^HSI", "name": "Hang Seng"},
            {"symbol": "^AXJO", "name": "ASX 200"},
            {"symbol": "^NSEI", "name": "NIFTY 50"},
            {"symbol": "000001.SS", "name": "SSE Composite"},
            {"symbol": "^KS11", "name": "KOSPI"}
        ],
        # "Canada": [
        #     {"symbol": "^GSPTSE", "name": "TSX Composite"},
        #     {"symbol": "TX60.TS", "name": "TSX 60"},
        #     {"symbol": "^SPCDNX", "name": "TSX Venture"}
        # ],
        # "Emerging Markets": [
        #     {"symbol": "^BVSP", "name": "Bovespa"},
        #     {"symbol": "^MXX", "name": "IPC Mexico"},
        #     {"symbol": "^TASI.SR", "name": "Tadawul"},
        #     {"symbol": "^JKSE", "name": "Jakarta Composite"},
        #     {"symbol": "XU100.IS", "name": "BIST 100"}
        # ],
        # "Global": [
        #     {"symbol": "MSCIWORLD", "name": "MSCI World"},
        #     {"symbol": "^W1DOW", "name": "DJ Global"}
        # ]
    }
    
    # Check cache first
    cache_key = "indices:regional:all:v2"
    cached_data = redis_client.get_cache(cache_key)
    if cached_data:
        return cached_data
    
    result = {}
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            for region, indices in regional_indices.items():
                region_data = []
                
                for index in indices:
                    try:
                        # Fetch current price data from FMP using the centralized BASE URL
                        endpoint = "historical-price-eod/light"
                        url = f"{FMP_BASE_URL}/{endpoint}"
                        
                        params = {
                            "symbol": index["symbol"],
                            "apikey": FMP_API_KEY
                        }
                        
                        response = await client.get(url, params=params)
                        
                        if response.status_code == 200:
                            data = response.json()
                            
                            # Handle potential FMP error responses in JSON
                            if isinstance(data, dict) and "Error Message" in data:
                                print(f"FMP API Error for {index['symbol']}: {data['Error Message']}")
                                continue

                            if data and isinstance(data, list) and len(data) > 0:
                                latest = data[0]
                                previous = data[1] if len(data) > 1 else latest
                                
                                # Fix: 'light' endpoint uses 'price' instead of 'close'
                                current_price = latest.get("price", 0)
                                previous_close = previous.get("price", current_price)
                                change = current_price - previous_close
                                change_percent = (change / previous_close * 100) if previous_close != 0 else 0
                                
                                # Get historical data for chart (last 1 year)
                                history = []
                                for item in data[:252]:
                                    history.append({
                                        "symbol": index["symbol"],
                                        "date": item.get("date"),
                                        "price": item.get("price", 0),
                                        "volume": item.get("volume", 0)
                                    })
                                
                                region_data.append({
                                    "symbol": index["symbol"],
                                    "name": index["name"],
                                    "price": round(current_price, 2),
                                    "change": round(change, 2),
                                    "changePercent": round(change_percent, 2),
                                    "history": list(reversed(history))  # Oldest to newest
                                })
                        else:
                            print(f"FMP API error for {index['symbol']}: {response.status_code}")
                            
                    except Exception as e:
                        print(f"Error fetching {index['symbol']}: {e}")
                        continue
                
                if region_data:
                    result[region] = region_data
        
        # Cache for 15 minutes if we have data
        if result:
            redis_client.set_cache(cache_key, result, ttl=900)
        
        return result
        
        # Cache for 15 minutes if we have data
        if result:
            redis_client.set_cache(cache_key, result, ttl=900)
        
        return result
        
    except Exception as e:
        print(f"Error fetching regional indices: {e}")
        return {}

@router.get("/regional/series/{symbol}")
async def get_regional_index_series(symbol: str, timeframe: str = "1Y"):
    """
    Fetch historical data for a specific regional index with timeframe support.
    Timeframes: 1M, 3M, 1Y, 5Y, Max
    """
    # Normalize symbol (decode URL encoded if needed, usually handled by FastAPI)
    symbol = symbol.strip()
    
    cache_key = f"indices:regional:{symbol}:{timeframe}"
    cached_data = redis_client.get_cache(cache_key)
    if cached_data:
        return cached_data

    from datetime import datetime, timedelta
    
    # Calculate date range
    today = datetime.now()
    start_date = None
    
    tf_map = {
        "1M": 30,
        "3M": 90,
        "1Y": 365,
        "5Y": 365 * 5,
        "MAX": None
    }
    
    days = tf_map.get(timeframe.upper(), 365)
    
    endpoint = "historical-price-eod/full"  # Default to full for flexibility, or filter light
    # But full is heavy. 
    # If days <= 365, use light? light is last 1 year (approx 252 trading days).
    # Actually 'full' with 'from' date is best.
    
    url = f"{FMP_BASE_URL}/{endpoint}/{symbol}"
    params = {"apikey": FMP_API_KEY}
    
    if days:
        start_date = (today - timedelta(days=days)).strftime("%Y-%m-%d")
        params["from"] = start_date
        params["to"] = today.strftime("%Y-%m-%d")
        
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # FMP 'full' endpoint returns { "symbol": "...", "historical": [...] }
                historical = []
                if isinstance(data, dict) and "historical" in data:
                    historical = data["historical"]
                elif isinstance(data, list):
                    # Some endpoints return list directly
                    historical = data
                
                if not historical:
                    return {"symbol": symbol, "history": []}
                
                # Sort ascending
                historical = sorted(historical, key=lambda x: x["date"])
                
                # Format history
                formatted_history = []
                for item in historical:
                    formatted_history.append({
                        "symbol": symbol,
                        "date": item.get("date"),
                        "price": item.get("close", item.get("price", 0)), # 'full' uses 'close', 'light' uses 'price'
                        "volume": item.get("volume", 0)
                    })
                
                # Calculate change stats
                current_price = formatted_history[-1]["price"] if formatted_history else 0
                prev_price = formatted_history[-2]["price"] if len(formatted_history) > 1 else current_price
                change = current_price - prev_price
                change_percent = (change / prev_price * 100) if prev_price != 0 else 0
                
                result = {
                    "symbol": symbol,
                    "price": round(current_price, 2),
                    "change": round(change, 2),
                    "changePercent": round(change_percent, 2),
                    "history": formatted_history
                }
                
                redis_client.set_cache(cache_key, result, ttl=300) # 5 min cache for specific queries
                return result
                
            else:
                print(f"Error fetching index series {symbol}: {response.status_code}")
                return {"symbol": symbol, "history": []}
                
    except Exception as e:
        print(f"Error fetching index series {symbol}: {e}")
        return {"symbol": symbol, "history": []}

@router.get("/major")
async def get_indices():
    """
    Fetch real-time data for major market indices: Dow Jones, NASDAQ, S&P 500, Russell 2000.
    Returns current value, change percentage, and 30-day history for each index.
    Caches result for 15 minutes.
    """
    cache_key = "indices:data"
    cached_data = redis_client.get_cache(cache_key)
    if cached_data:
        return cached_data

    indices_config = [
        {"name": "Dow Jones", "ticker": "^DJI", "key": "dow_jones"},
        {"name": "NASDAQ", "ticker": "^IXIC", "key": "nasdaq"},
        {"name": "S&P 500", "ticker": "^GSPC", "key": "sp_500"},
        {"name": "Russell 2000", "ticker": "^RUT", "key": "russell_2000"}
    ]
    
    results = []
    try:
        for idx in indices_config:
            try:
                ticker = yf.Ticker(idx["ticker"])
                # Get last 1 year of data
                history = ticker.history(period="1y")
                
                if history.empty:
                    # Fallback to default values if data unavailable
                    results.append({
                        "name": idx["name"],
                        "key": idx["key"],
                        "value": 0.0,
                        "change": 0.0,
                        "history": []
                    })
                    continue

                # Get current and previous close
                current_price = float(history['Close'].iloc[-1])
                prev_close = float(history['Close'].iloc[-2]) if len(history) > 1 else current_price
                change_percent = ((current_price - prev_close) / prev_close) * 100 if prev_close > 0 else 0.0
                
                # Convert history to list format
                history_list = []
                for date, row in history.iterrows():
                    history_list.append({
                        "date": date.strftime('%Y-%m-%d'),
                        "value": float(row['Close'])
                    })
                
                results.append({
                    "name": idx["name"],
                    "key": idx["key"],
                    "value": round(current_price, 2),
                    "change": round(change_percent, 2),
                    "history": history_list
                })
            except Exception as e:
                print(f"Error fetching {idx['name']}: {e}")
                # Fallback to default values
                results.append({
                    "name": idx["name"],
                    "key": idx["key"],
                    "value": 0.0,
                    "change": 0.0,
                    "history": []
                })
                continue
        
        # Cache outcome (TTL 15 mins)
        redis_client.set_cache(cache_key, results, ttl=900)
        
        return results
    except Exception as e:
        print(f"Error fetching indices: {e}")
        # Return empty results on critical failure
        return [{"name": idx["name"], "key": idx["key"], "value": 0.0, "change": 0.0, "history": []} for idx in indices_config]
