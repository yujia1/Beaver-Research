import httpx
import os
import datetime
import json
from typing import List, Dict, Any

# FMP Base URL
FMP_BASE_URL = "https://financialmodelingprep.com/stable"
FMP_API_KEY = os.getenv("FMP_API_KEY")

# Commodity Categories and Symbols configuration
COMMODITY_CATEGORIES = {
    "Financials": [
        # {"symbol": "ZQUSD", "name": "30 Day Fed Fund Futures", "type": "Interest Rates"},
        # {"symbol": "ZTUSD", "name": "2-Year T-Note Futures", "type": "Interest Rates"},
        # {"symbol": "ZFUSD", "name": "Five-Year US Treasury Note", "type": "Interest Rates"},
        # {"symbol": "ZNUSD", "name": "10-Year T-Note Futures", "type": "Interest Rates"},
        # {"symbol": "ZBUSD", "name": "30 Year U.S. Treasury Bond", "type": "Interest Rates"},
        {"symbol": "DXUSD", "name": "US Dollar", "type": "Currency"},
        {"symbol": "ESUSD", "name": "E-Mini S&P 500", "type": "Equity Index"},
        {"symbol": "NQUSD", "name": "Nasdaq 100", "type": "Equity Index"},
        {"symbol": "YMUSD", "name": "Mini Dow Jones Industrial", "type": "Equity Index"},
        {"symbol": "RTYUSD", "name": "Micro E-mini Russell 2000", "type": "Equity Index"}
    ],
    "Metals": [
        {"symbol": "GCUSD", "name": "Gold", "type": "Metal"},
        {"symbol": "SIUSD", "name": "Silver", "type": "Metal"},
        {"symbol": "PLUSD", "name": "Platinum", "type": "Metal"},
        {"symbol": "PAUSD", "name": "Palladium", "type": "Metal"},
        {"symbol": "HGUSD", "name": "Copper", "type": "Metal"},
        {"symbol": "ALIUSD", "name": "Aluminum", "type": "Metal"}
    ],
    "Energy": [
        {"symbol": "CLUSD", "name": "Crude Oil (WTI)", "type": "Energy"},
        {"symbol": "BZUSD", "name": "Brent Crude Oil", "type": "Energy"},
        {"symbol": "NGUSD", "name": "Natural Gas", "type": "Energy"},
        {"symbol": "RBUSD", "name": "Gasoline RBOB", "type": "Energy"},
        {"symbol": "HOUSD", "name": "Heating Oil", "type": "Energy"}
    ],
    "Agriculture": [
        {"symbol": "ZCUSX", "name": "Corn Futures", "type": "Agriculture"},
        {"symbol": "KEUSX", "name": "Wheat Futures", "type": "Agriculture"},
        {"symbol": "ZOUSX", "name": "Oat Futures", "type": "Agriculture"},
        {"symbol": "ZRUSD", "name": "Rough Rice Futures", "type": "Agriculture"},
        {"symbol": "ZSUSX", "name": "Soybean Futures", "type": "Agriculture"}
    ],
    "Softs & Livestock": [
        {"symbol": "KCUSX", "name": "Coffee", "type": "Softs"},
        {"symbol": "CCUSD", "name": "Cocoa", "type": "Softs"},
        {"symbol": "SBUSX", "name": "Sugar", "type": "Softs"},
        {"symbol": "CTUSX", "name": "Cotton", "type": "Softs"},
        {"symbol": "OJUSX", "name": "Orange Juice", "type": "Softs"},
        {"symbol": "LBUSD", "name": "Lumber Futures", "type": "Softs"},
        {"symbol": "LEUSX", "name": "Live Cattle Futures", "type": "Livestock"},
        {"symbol": "GFUSX", "name": "Feeder Cattle Futures", "type": "Livestock"},
        {"symbol": "HEUSX", "name": "Lean Hogs Futures", "type": "Livestock"},
        {"symbol": "DCUSD", "name": "Class III Milk Futures", "type": "Livestock/Dairy"}
    ]
}

async def fetch_commodity_data(timeframe: str = "daily") -> Dict[str, Any]:
    """
    Fetch commodity data categorized by sector using FMP API.
    Returns a dict structure: { Category: [ { symbol, name, price, change, history... } ] }
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
        "max": 365*20
    }
    days = days_map.get(timeframe, 365)
    start_date = (today - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")
    
    async with httpx.AsyncClient() as client:
        for category, items in COMMODITY_CATEGORIES.items():
            category_data = []
            
            for item in items:
                try:
                    symbol = item["symbol"]
                    
                    # 1. Fetch Real-time Quote (Primary source for current price)
                    quote_url = f"{FMP_BASE_URL}/quote/{symbol}"
                    quote_params = {"apikey": FMP_API_KEY}
                    
                    current_price = 0.0
                    change = 0.0
                    change_p = 0.0
                    
                    quote_response = await client.get(quote_url, params=quote_params)
                    if quote_response.status_code == 200:
                        q_data = quote_response.json()
                        if isinstance(q_data, list) and len(q_data) > 0:
                            q = q_data[0]
                            current_price = float(q.get("price", 0))
                            change = float(q.get("change", 0))
                            change_p = float(q.get("changesPercentage", 0))
                    
                    # 2. Fetch History (Secondary, may be stale)
                    hist_url = f"{FMP_BASE_URL}/historical-price-eod/light"
                    hist_params = {
                        "symbol": symbol,
                        "apikey": FMP_API_KEY,
                        "from": start_date,
                        "to": end_date
                    }
                    
                    history = []
                    hist_response = await client.get(hist_url, params=hist_params)
                    
                    if hist_response.status_code == 200:
                        h_data = hist_response.json()
                        if isinstance(h_data, list) and len(h_data) > 0:
                            # Sort by date
                            h_data.sort(key=lambda x: x["date"])
                            
                            # Filter client side
                            filtered_data = [d for d in h_data if d["date"] >= start_date]
                            
                            if filtered_data:
                                for h in filtered_data:
                                    history.append({
                                        "date": h["date"],
                                        "value": float(h.get("price", h.get("close", 0))),
                                        "volume": float(h.get("volume", 0))
                                    })
                    
                    # If we have current price, add to results even if history is empty
                    if current_price != 0 or history:
                        # If history is empty but we have quote, maybe fake a single point or leave empty?
                        # Frontend handles empty history (sparkline will be blank).
                        
                        category_data.append({
                            "symbol": symbol,
                            "name": item["name"],
                            "type": item["type"],
                            "price": round(current_price, 4),
                            "change": round(change, 4),
                            "changePercent": round(change_p, 2),
                            "history": history
                        })
                    else:
                        print(f"No data for commodity {symbol}")

                except Exception as e:
                    print(f"Error fetching commodity {item['symbol']}: {e}")
            
            if category_data:
                results[category] = category_data
                
    return results
