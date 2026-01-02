from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import yfinance as yf
import pandas as pd
import datetime
from redis_client import redis_client

router = APIRouter()

class CryptoData(BaseModel):
    ticker: str
    name: str
    price: float
    date: str
    description: str
    series_id: str
    history: List[Dict[str, Any]]
    selectedTimeframe: str
    loading: bool
    chart_type: str

@router.get("/all")
async def get_all_crypto_data(timeframe: str = "daily"):
    """
    Fetch data for major cryptocurrencies using Financial Modeling Prep (FMP) API.
    Returns data for BTC-USD, ETH-USD, etc.
    Includes history data for the specified timeframe.
    Caches results for 15 minutes.
    """
    cache_key = f"crypto:all:{timeframe}:v2"
    cached_data = redis_client.get_cache(cache_key)
    if cached_data:
        return cached_data

    try:
        from services.market.crypto import fetch_crypto_data
        
        results = await fetch_crypto_data(timeframe)
        
        if results:
            redis_client.set_cache(cache_key, results, ttl=3600)  # 1 hour cache
            
        return results
    except Exception as e:
        print(f"Error in crypto router: {e}")
        return []
