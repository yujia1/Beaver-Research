import httpx
import os
import datetime
import json
from typing import List, Dict, Any
import yfinance as yf
import pandas as pd
import asyncio

# FMP Base URL
FMP_BASE_URL = "https://financialmodelingprep.com/stable"
FMP_API_KEY = os.getenv("FMP_API_KEY")

# Commodity Categories and Symbols configuration
COMMODITY_CATEGORIES = {
    "Financials": [
        {"symbol": "ZQ=F", "name": "30 Day Fed Fund Futures", "type": "Interest Rates", "resource": "yfinance"},
        {"symbol": "ZT=F", "name": "2-Year T-Note Futures", "type": "Interest Rates", "resource": "yfinance"},
        {"symbol": "ZF=F", "name": "Five-Year US Treasury Note", "type": "Interest Rates", "resource": "yfinance"},
        {"symbol": "ZN=F", "name": "10-Year T-Note Futures", "type": "Interest Rates", "resource": "yfinance"},
        {"symbol": "ZB=F", "name": "30 Year U.S. Treasury Bond", "type": "Interest Rates", "resource": "yfinance"},
        {"symbol": "DX-Y.NYB", "name": "US Dollar", "type": "Currency", "resource": "yfinance"},
        {"symbol": "ESUSD", "name": "E-Mini S&P 500", "type": "Equity Index", "resource": "FMP"},
        {"symbol": "NQ=F", "name": "Nasdaq 100", "type": "Equity Index", "resource": "yfinance"},
        {"symbol": "YM=F", "name": "Mini Dow Jones Industrial", "type": "Equity Index", "resource": "yfinance"},
        {"symbol": "M2K=F", "name": "Micro E-mini Russell 2000", "type": "Equity Index", "resource": "yfinance"}
    ],
    "Metals": [
        {"symbol": "GCUSD", "name": "Gold", "type": "Metal", "resource": "FMP"},
        {"symbol": "SIUSD", "name": "Silver", "type": "Metal", "resource": "FMP"},
        {"symbol": "PL=F", "name": "Platinum", "type": "Metal", "resource": "yfinance"},
        {"symbol": "PA=F", "name": "Palladium", "type": "Metal", "resource": "yfinance"},
        {"symbol": "HG=F", "name": "Copper", "type": "Metal", "resource": "yfinance"},
        {"symbol": "ALI=F", "name": "Aluminum", "type": "Metal", "resource": "yfinance"}
    ],
    "Energy": [
        {"symbol": "CL=F", "name": "Crude Oil (WTI)", "type": "Energy", "resource": "yfinance"},
        {"symbol": "BZUSD", "name": "Brent Crude Oil", "type": "Energy", "resource": "FMP"},
        {"symbol": "NG=F", "name": "Natural Gas", "type": "Energy", "resource": "yfinance"},
        {"symbol": "RB=F", "name": "Gasoline RBOB", "type": "Energy", "resource": "yfinance"},
        {"symbol": "HO=F", "name": "Heating Oil", "type": "Energy", "resource": "yfinance"}
    ],
    "Agriculture": [
        {"symbol": "ZC=F", "name": "Corn Futures", "type": "Agriculture", "resource": "yfinance"},
        {"symbol": "KE=F", "name": "Wheat Futures", "type": "Agriculture", "resource": "yfinance"},
        {"symbol": "ZO=F", "name": "Oat Futures", "type": "Agriculture", "resource": "yfinance"},
        {"symbol": "ZR=F", "name": "Rough Rice Futures", "type": "Agriculture", "resource": "yfinance"},
        {"symbol": "ZS=F", "name": "Soybean Futures", "type": "Agriculture", "resource": "yfinance"}
    ],
    "Softs & Livestock": [
        {"symbol": "KC=F", "name": "Coffee", "type": "Softs", "resource": "yfinance"},
        {"symbol": "CC=F", "name": "Cocoa", "type": "Softs", "resource": "yfinance"},
        {"symbol": "SB=F", "name": "Sugar", "type": "Softs", "resource": "yfinance"},
        {"symbol": "CT=F", "name": "Cotton", "type": "Softs", "resource": "yfinance"},
        {"symbol": "OJ=F", "name": "Orange Juice", "type": "Softs", "resource": "yfinance"},
        {"symbol": "LBR=F", "name": "Lumber Futures", "type": "Softs", "resource": "yfinance"},
        {"symbol": "LE=F", "name": "Live Cattle Futures", "type": "Livestock", "resource": "yfinance"},
        {"symbol": "GF=F", "name": "Feeder Cattle Futures", "type": "Livestock", "resource": "yfinance"},
        {"symbol": "HE=F", "name": "Lean Hogs Futures", "type": "Livestock", "resource": "yfinance"},
        {"symbol": "DC=F", "name": "Class III Milk Futures", "type": "Livestock/Dairy", "resource": "yfinance"}
    ]
}

async def fetch_commodity_data(timeframe: str = "daily") -> Dict[str, Any]:
    """
    Fetch commodity data categorized by sector using FMP API or yfinance.
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
                    resource = item.get("resource", "FMP")
                    
                    if resource == "yfinance":
                        # Fetch from yfinance
                        # Run in executor to avoid blocking async loop since yfinance is synchronous
                        def fetch_yf(sym, start, end):
                            ticker = yf.Ticker(sym)
                            # Fetch history
                            hist = ticker.history(start=start, end=end)
                            # Fetch info for current price (fast_info is faster/reliable)
                            fi = ticker.fast_info
                            curr = fi.last_price if fi and fi.last_price else 0.0
                            prev = fi.previous_close if fi and fi.previous_close else 0.0
                            
                            if (curr is None or pd.isna(curr) or curr == 0.0) and not hist.empty:
                                curr = hist['Close'].iloc[-1]
                            
                            c = 0.0
                            cp = 0.0
                            if curr and prev:
                                c = curr - prev
                                cp = (c / prev) * 100
                                
                            return hist, curr, c, cp

                        # Use asyncio.to_thread for Python 3.9+
                        hist_df, current_price, change, change_p = await asyncio.to_thread(fetch_yf, symbol, start_date, end_date)
                        
                        history = []
                        if not hist_df.empty:
                            # Reset index to get Date
                            hist_df = hist_df.reset_index()
                            for _, row in hist_df.iterrows():
                                # yfinance Date is usually timestamp or datetime
                                date_str = row['Date'].strftime('%Y-%m-%d')
                                val = row['Close']
                                vol = row.get('Volume', 0)
                                if pd.isna(val): continue
                                
                                history.append({
                                    "date": date_str,
                                    "value": float(val),
                                    "volume": float(vol)
                                })
                        
                        # Add to result
                        if current_price or history:
                             category_data.append({
                                "symbol": symbol,
                                "name": item["name"],
                                "type": item["type"],
                                "resource": resource,
                                "price": round(float(current_price or 0.0), 4),
                                "change": round(float(change or 0.0), 4),
                                "changePercent": round(float(change_p or 0.0), 2),
                                "history": history
                            })

                    else:
                        # Existing FMP Logic
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
                                
                                # Fallback: If filter yields nothing (data is stale/old), use the most recent available data
                                if not filtered_data and h_data:
                                    # Use up to 'days' amount of recent points, or all if less
                                    limit = min(len(h_data), days)
                                    filtered_data = h_data[-limit:]
                                
                                if filtered_data:
                                    for h in filtered_data:
                                        history.append({
                                            "date": h["date"],
                                            "value": float(h.get("price", h.get("close", 0))),
                                            "volume": float(h.get("volume", 0))
                                        })
                        
                        # If we have current price, add to results. 
                        # If current_price is 0 (quote failed) but we have history, use history for price.
                        if current_price == 0 and history:
                            current_price = history[-1]["value"]
                            # Calculate change from history
                            if len(history) > 1:
                                prev_price = history[-2]["value"]
                                change = current_price - prev_price
                                change_p = (change / prev_price * 100) if prev_price != 0 else 0

                        if current_price != 0 or history:
                            category_data.append({
                                "symbol": symbol,
                                "name": item["name"],
                                "type": item["type"],
                                "resource": item.get("resource", "FMP"),
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
