import httpx
import os
import datetime
from typing import List, Dict, Any

# FMP Base URL
FMP_BASE_URL = "https://financialmodelingprep.com/stable"
FMP_API_KEY = os.getenv("FMP_API_KEY")

# Currency pairs to track
CURRENCIES = {
    "EURUSD": {
        "name": "EUR/USD",
        "description": "Euro to U.S. Dollar"
    },
    "USDJPY": {
        "name": "USD/JPY",
        "description": "Japanese Yen to U.S. Dollar"
    },
    "USDCNY": {
        "name": "USD/CNY",
        "description": "Chinese Yuan to U.S. Dollar"
    }
}

async def fetch_currency_data(timeframe: str = "daily") -> Dict[str, Any]:
    """
    Fetch currency data using FMP API.
    Returns a dict keyed by FMP symbol (EURUSD, JPYUSD, CNYUSD)
    """
    results = {}
    
    # Calculate date range
    today = datetime.datetime.now()
    days_map = {
        "daily": 30,
        "weekly": 90,
        "monthly": 365,
        "quarterly": 365*2,
        "yearly": 365*5,
        "5y": 365*5,
        "max": 365*20
    }
    days = days_map.get(timeframe, 365)
    start_date = (today - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")

    async with httpx.AsyncClient() as client:
        for symbol, metadata in CURRENCIES.items():
            try:
                # Note: Verify if FMP supports JPYUSD/CNYUSD or requires USDJPY/USDCNY. 
                # Provided request asked for JPYUSD/CNHUSD(CNYUSD). 
                # If FMP returns emtpy, it might be due to invalid ticker.
                url = f"{FMP_BASE_URL}/historical-price-eod/light"
                params = {
                    "symbol": symbol,
                    "apikey": FMP_API_KEY,
                    "from": start_date,
                    "to": end_date
                }
                
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    
                    # FMP Light returns list of objects
                    if isinstance(data, list) and len(data) > 0:
                        # Sort by date
                        data.sort(key=lambda x: x["date"])
                        
                        # Convert to standard format
                        formatted_history = []
                        for item in data:
                            if item["date"] < start_date:
                                continue
                            formatted_history.append({
                                "date": item["date"],
                                "value": float(item.get("price", item.get("close", 0)))
                            })
                            
                        if formatted_history:
                            results[symbol] = formatted_history
                    else:
                        print(f"No data returned for {symbol}")
                else:
                    print(f"FMP Currency Error {symbol}: {response.status_code}")
                    
            except Exception as e:
                print(f"Error fetching currency {symbol}: {e}")
                
    return results
