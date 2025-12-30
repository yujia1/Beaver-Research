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
    Fetch data for all major cryptocurrencies WITH history.
    Returns data for BTC-USD, ETH-USD, USDT-USD, BNB-USD, SOL-USD
    Includes history data for the specified timeframe.
    Caches results for 15 minutes.
    """
    cache_key = f"crypto:all:{timeframe}"
    cached_data = redis_client.get_cache(cache_key)
    if cached_data:
        return cached_data

    try:
        crypto_pairs = [
            {"ticker": "BTC-USD", "name": "Bitcoin (BTC)", "description": "Bitcoin Price"},
            {"ticker": "ETH-USD", "name": "Ethereum (ETH)", "description": "Ethereum Price"},
            {"ticker": "USDT-USD", "name": "Tether USDt (USDT)", "description": "Tether USDt Price"},
            {"ticker": "BNB-USD", "name": "BNB (BNB)", "description": "BNB Price"},
            {"ticker": "SOL-USD", "name": "Solana (SOL)", "description": "Solana Price"}
        ]
        
        # Map frontend timeframes to yfinance periods
        period_map = {
            "daily": "1mo",
            "weekly": "3mo",
            "monthly": "1y",
            "yearly": "5y"
        }
        
        yf_period = period_map.get(timeframe, "1mo")
        
        results = []
        for pair in crypto_pairs:
            try:
                crypto = yf.Ticker(pair["ticker"])
                # Fetch history with the specified timeframe
                history = crypto.history(period=yf_period)
                
                if history.empty:
                    print(f"[WARNING] {pair['ticker']}: History DataFrame is empty")
                    results.append({
                        "ticker": pair["ticker"],
                        "name": pair["name"],
                        "price": 0,
                        "date": datetime.datetime.now().strftime('%Y-%m-%d'),
                        "description": pair["description"],
                        "series_id": pair["ticker"],
                        "history": [],
                        "selectedTimeframe": timeframe,
                        "loading": False,
                        "chart_type": "line"
                    })
                    continue
                
                # Convert history to list with volume
                history_list = []
                has_volume_column = 'Volume' in history.columns
                
                for date, row in history.iterrows():
                    try:
                        volume_value = 0
                        if has_volume_column:
                            try:
                                vol = row['Volume']
                                if pd.notna(vol) and vol != 0:
                                    volume_value = float(vol)
                            except (KeyError, ValueError, TypeError):
                                volume_value = 0
                        
                        close_value = row['Close']
                        if pd.isna(close_value):
                            continue
                        
                        history_list.append({
                            "date": date.strftime('%Y-%m-%d'),
                            "value": float(close_value),
                            "volume": volume_value
                        })
                    except Exception as e:
                        print(f"[WARNING] {pair['ticker']}: Error processing row for date {date}: {e}")
                
                current_price = history['Close'].iloc[-1] if not history.empty else 0
                
                results.append({
                    "ticker": pair["ticker"],
                    "name": pair["name"],
                    "price": float(current_price),
                    "date": datetime.datetime.now().strftime('%Y-%m-%d'),
                    "description": pair["description"],
                    "series_id": pair["ticker"],
                    "history": history_list,
                    "selectedTimeframe": timeframe,
                    "loading": False,
                    "chart_type": "line"
                })
            except Exception as e:
                print(f"Error fetching {pair['ticker']}: {e}")
                continue
        
        redis_client.set_cache(cache_key, results, ttl=900)
        return results
    except Exception as e:
        print(f"Error fetching crypto data: {e}")
        return []
