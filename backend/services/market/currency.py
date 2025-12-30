import httpx
import os
import datetime
from typing import List, Dict, Any

# FMP Base URL
FMP_BASE_URL = "https://financialmodelingprep.com/stable"
FMP_API_KEY = os.getenv("FMP_API_KEY")

# Mapping FRED Series ID to FMP Symbols
# DEXUSEU: US Dollars to Euro -> EURUSD
# DEXJPUS: Yen to US Dollar -> USDJPY
# DEXCHUS: Yuan to US Dollar -> USDCNY
# We can enable more if needed.
CURRENCY_MAPPING = {
    "DEXUSEU": "EURUSD",
    "DEXJPUS": "USDJPY",
    "DEXCHUS": "USDCNY"
}

async def fetch_currency_data(timeframe: str = "daily") -> Dict[str, Any]:
    """
    Fetch currency data using FMP API.
    Returns a dict keyed by FRED Series ID (for compatibility with macro.py)
    """
    results = {}
    
    # Calculate date range
    today = datetime.datetime.now()
    days_map = {
        "daily": 30,
        "weekly": 90,
        "monthly": 365,
        "yearly": 365*5,
        "5y": 365*5,
        "max": 365*20 # 20 years
    }
    days = days_map.get(timeframe, 365)
    start_date = (today - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")

    async with httpx.AsyncClient() as client:
        # We can fetch them in parallel if we want, but loop is fine for 3 items
        for fred_id, fmp_symbol in CURRENCY_MAPPING.items():
            try:
                # User requested: historical-price-eod/light?symbol=EURUSD&from=...&to=...
                # Note: FMP 'light' endpoint is typically fixed 1 year, but we accept user instruction to pass params.
                # If 'from'/'to' don't work on light, we might get just 1 year.
                
                url = f"{FMP_BASE_URL}/historical-price-eod/light"
                params = {
                    "symbol": fmp_symbol,
                    "apikey": FMP_API_KEY,
                    "from": start_date,
                    "to": end_date
                }
                
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    
                    # FMP Light returns list of objects
                    if isinstance(data, list):
                        # Sort by date
                        data.sort(key=lambda x: x["date"])
                        
                        # Convert to standard format
                        # FMP light uses 'price' (and sometimes 'close'?)
                        formatted_history = []
                        for item in data:
                            if item["date"] < start_date: continue # Client side filter if API didn't respect it
                            formatted_history.append({
                                "date": item["date"],
                                "value": float(item.get("price", item.get("close", 0)))
                            })
                            
                        if formatted_history:
                            results[fred_id] = formatted_history
                    else:
                        print(f"Unexpected FMP Currency format for {fmp_symbol}")
                else:
                    print(f"FMP Currency Error {fmp_symbol}: {response.status_code}")
                    
            except Exception as e:
                print(f"Error fetching currency {fmp_symbol}: {e}")
                
    return results
