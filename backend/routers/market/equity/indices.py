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

from services.market.indices import fetch_regional_indices_data, fetch_major_indices_data

# ... (Previous code)

@router.get("/regional")
async def get_regional_indices():
    """
    Fetch global market indices organized by region.
    Serves data from Redis cache (populated by background scheduler).
    Fallbacks to on-demand fetch if cache is empty.
    """
    cache_key = "indices:regional:all:v2"
    cached_data = redis_client.get_cache(cache_key)
    if cached_data:
        return cached_data
    
    # Fallback if scheduler hasn't run or cache expired
    print("Cache miss for regional indices, fetching on-demand...")
    data = await fetch_regional_indices_data()
    if data:
        redis_client.set_cache(cache_key, data, ttl=900)
    return data

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
                
                # Fetch Live Quote to append/update
                current_price = formatted_history[-1]["price"] if formatted_history else 0
                change = 0
                change_percent = 0
                
                try:
                    quote_url = f"{FMP_BASE_URL}/quote/{symbol}"
                    quote_resp = await client.get(quote_url, params={"apikey": FMP_API_KEY})
                    if quote_resp.status_code == 200:
                        q_data = quote_resp.json()
                        if isinstance(q_data, list) and len(q_data) > 0:
                            quote = q_data[0]
                            current_price = quote.get("price", current_price)
                            change = quote.get("change", 0)
                            change_percent = quote.get("changesPercentage", 0)
                            
                            # Merge into history
                            if formatted_history:
                                last_hist_date = formatted_history[-1]["date"]
                                ts = quote.get("timestamp")
                                if ts:
                                    quote_date = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                                    if quote_date != last_hist_date:
                                        formatted_history.append({
                                            "symbol": symbol,
                                            "date": quote_date,
                                            "price": current_price,
                                            "volume": quote.get("volume", 0)
                                        })
                                    else:
                                        # Update last bar
                                        formatted_history[-1]["price"] = current_price
                                        formatted_history[-1]["volume"] = quote.get("volume", 0)
                except Exception as e:
                    print(f"Error merging live quote for {symbol}: {e}")
                    # Fallback to calc from history
                    if formatted_history:
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
    Fetch real-time data for major market indices.
    Serves data from Redis cache (populated by background scheduler).
    Fallbacks to on-demand fetch if cache is empty.
    """
    cache_key = "indices:data"
    cached_data = redis_client.get_cache(cache_key)
    if cached_data:
        return cached_data

    # Fallback
    print("Cache miss for major indices, fetching on-demand...")
    data = await fetch_major_indices_data()
    if data:
        redis_client.set_cache(cache_key, data, ttl=900)
    return data
