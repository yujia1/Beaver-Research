import httpx
import os
import datetime
from typing import List, Dict, Any

# FMP Base URL
FMP_BASE_URL = "https://financialmodelingprep.com/stable"
FMP_API_KEY = os.getenv("FMP_API_KEY")

async def fetch_crypto_data(timeframe: str = "daily") -> List[Dict[str, Any]]:
    """
    Fetch crypto data using FMP API for Bitcoin (BTCUSD) and Ethereum (ETHUSD).
    For others (USDT, BNB, SOL), we might stick to YFinance or implement FMP if available.
    For this implementation, we focus on the requested BTC and ETH switch to FMP.
    """
    
    # Configuration for requested FMP symbols vs our internal schema
    # FMP uses 'BTCUSD', we use 'BTC-USD' as frontend key
    crypto_config = [
        {"ticker": "BTC-USD", "fmp_symbol": "BTCUSD", "name": "Bitcoin (BTC)", "description": "Bitcoin Price"},
        {"ticker": "ETH-USD", "fmp_symbol": "ETHUSD", "name": "Ethereum (ETH)", "description": "Ethereum Price"}
    ]
    
    # Map frontend timeframe to number of days for FMP 'from' param
    # light endpoint: "https://financialmodelingprep.com/stable/historical-price-eod/light?symbol=BTCUSD"
    # light endpoint returns last 1 year (approx 252-365 days).
    # If timeframe > 1 year, we might need 'full' endpoint.
    
    endpoint_type = "light"
    # full endpoint: historical-price-eod/full/{symbol}
    
    timeframe_days_map = {
        "daily": 30,      # 1mo
        "weekly": 90,     # 3mo
        "monthly": 365,   # 1y
        "yearly": 365*5   # 5y
    }
    
    days_needed = timeframe_days_map.get(timeframe, 30)
    
    results = []
    
    async with httpx.AsyncClient() as client:
        for item in crypto_config:
            try:
                # Use FMP for all configured ones
                symbol = item["fmp_symbol"]
                
                # Construct URL
                # Using 'light' endpoint for < 1 year content as per prompt request/hint
                # Prompt: "https://financialmodelingprep.com/stable/historical-price-eod/light?symbol=BTCUSD..."
                # But 'light' endpoint doesn't support 'from/to', it just gives last year.
                # If we need less data (daily/1mo), we just slice the result.
                # If we need 5y, we must use 'full'.
                
                if days_needed > 365:
                   url = f"{FMP_BASE_URL}/historical-price-eod/full/{symbol}"
                   params = { "apikey": FMP_API_KEY }
                   # Full endpoint returns all history, we might want to clip it?
                   # Or use from/to
                   start_date = (datetime.datetime.now() - datetime.timedelta(days=days_needed)).strftime("%Y-%m-%d")
                   params["from"] = start_date
                   params["to"] = datetime.datetime.now().strftime("%Y-%m-%d")
                else:
                    # Use the requested "light" endpoint
                    url = f"{FMP_BASE_URL}/historical-price-eod/light"
                    params = {
                        "symbol": symbol,
                        "apikey": FMP_API_KEY
                    }
                
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # FMP 'light' returns list: [{date:..., price:..., volume:...} ...]
                    # FMP 'full' returns dict: { symbol:..., historical: [...] }
                    
                    historical = []
                    if isinstance(data, list):
                        historical = data
                    elif isinstance(data, dict) and "historical" in data:
                        historical = data["historical"]
                        
                    if not historical:
                         # Fallback or empty
                         results.append(create_empty_result(item, timeframe))
                         continue

                    # Sort by date ascending
                    historical.sort(key=lambda x: x["date"])
                    
                    # Filter for timeframe if needed (if light returned 365 days but we only want 30)
                    start_date_limit = (datetime.datetime.now() - datetime.timedelta(days=days_needed)).strftime("%Y-%m-%d")
                    historical = [h for h in historical if h["date"] >= start_date_limit]
                    
                    # Format for frontend
                    history_list = []
                    for h in historical:
                        # light endpoint -> 'price', full endpoint -> 'close'
                        price = h.get("price", h.get("close", 0))
                        history_list.append({
                            "date": h["date"],
                            "value": float(price),
                            "volume": float(h.get("volume", 0))
                        })
                    
                    current_price = history_list[-1]["value"] if history_list else 0
                    
                    results.append({
                        "ticker": item["ticker"],
                        "name": item["name"],
                        "price": float(current_price),
                        "date": datetime.datetime.now().strftime('%Y-%m-%d'),
                        "description": item["description"],
                        "series_id": item["ticker"],
                        "history": history_list,
                        "selectedTimeframe": timeframe,
                        "loading": False,
                        "chart_type": "line"
                    })
                else:
                    # print(f"FMP error for {symbol}: {response.status_code}")
                    results.append(create_empty_result(item, timeframe))
            
            except Exception as e:
                # print(f"Error fetching {item['ticker']} from FMP: {e}")
                results.append(create_empty_result(item, timeframe))
                
    return results

def create_empty_result(item, timeframe):
    return {
        "ticker": item["ticker"],
        "name": item["name"],
        "price": 0,
        "date": datetime.datetime.now().strftime('%Y-%m-%d'),
        "description": item["description"],
        "series_id": item["ticker"],
        "history": [],
        "selectedTimeframe": timeframe,
        "loading": False,
        "chart_type": "line"
    }
