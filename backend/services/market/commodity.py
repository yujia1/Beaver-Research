import httpx
import os
import datetime
import json
from typing import List, Dict, Any, Optional
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


async def fetch_yf_data(symbol: str, start_date: str, end_date: str) -> tuple:
    def _fetch(sym, start, end):
        try:
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
        except Exception as e:
            print(f"Error in yfinance internal fetch for {sym}: {e}")
            return pd.DataFrame(), 0.0, 0.0, 0.0

    return await asyncio.to_thread(_fetch, symbol, start_date, end_date)

async def process_item(client, item, start_date, end_date, days):
    try:
        symbol = item["symbol"]
        resource = item.get("resource", "FMP")
        
        if resource == "yfinance":
            # fetch_yf_data is already async/threaded
            hist_df, current_price, change, change_p = await fetch_yf_data(symbol, start_date, end_date)
            
            history = []
            if not hist_df.empty:
                hist_df = hist_df.reset_index()
                for _, row in hist_df.iterrows():
                    date_val = row['Date']
                    if isinstance(date_val, (pd.Timestamp, datetime.date, datetime.datetime)):
                            date_str = date_val.strftime('%Y-%m-%d')
                    else:
                            date_str = str(date_val).split(' ')[0]
                    val = row['Close']
                    vol = row.get('Volume', 0)
                    if pd.isna(val): continue
                    
                    history.append({
                        "date": date_str,
                        "value": float(val),
                        "volume": float(vol)
                    })
            
            if current_price or history:
                    return {
                    "symbol": symbol,
                    "name": item["name"],
                    "type": item["type"],
                    "resource": resource,
                    "price": round(float(current_price or 0.0), 4),
                    "change": round(float(change or 0.0), 4),
                    "changePercent": round(float(change_p or 0.0), 2),
                    "history": history
                }

        else:
            # FMP Logic
            # 1. Quote
            quote_url = f"{FMP_BASE_URL}/quote"
            quote_params = {"symbol": symbol, "apikey": FMP_API_KEY}
            
            # 2. History
            hist_url = f"{FMP_BASE_URL}/historical-price-eod/light"
            hist_params = {
                "symbol": symbol,
                "apikey": FMP_API_KEY,
                "from": start_date,
                "to": end_date
            }
            
            # Run FMP requests concurrently for this item
            q_res, h_res = await asyncio.gather(
                client.get(quote_url, params=quote_params),
                client.get(hist_url, params=hist_params),
                return_exceptions=True
            )
            
            current_price = 0.0
            change = 0.0
            change_p = 0.0
            
            if not isinstance(q_res, Exception) and q_res.status_code == 200:
                q_data = q_res.json()
                if isinstance(q_data, list) and len(q_data) > 0:
                    q = q_data[0]
                    current_price = float(q.get("price", 0))
                    change = float(q.get("change", 0))
                    change_p = float(q.get("changesPercentage", 0))
            
            history = []
            if not isinstance(h_res, Exception) and h_res.status_code == 200:
                h_data = h_res.json()
                if isinstance(h_data, list) and len(h_data) > 0:
                    h_data.sort(key=lambda x: x["date"])
                    filtered_data = [d for d in h_data if d["date"] >= start_date]
                    if not filtered_data and h_data:
                        limit = min(len(h_data), days)
                        filtered_data = h_data[-limit:]
                    
                    if filtered_data:
                        for h in filtered_data:
                            history.append({
                                "date": h["date"],
                                "value": float(h.get("price", h.get("close", 0))),
                                "volume": float(h.get("volume", 0))
                            })
            
            if current_price == 0 and history:
                current_price = history[-1]["value"]
                if len(history) > 1:
                    prev_price = history[-2]["value"]
                    change = current_price - prev_price
                    change_p = (change / prev_price * 100) if prev_price != 0 else 0

            if current_price != 0 or history:
                return {
                    "symbol": symbol,
                    "name": item["name"],
                    "type": item["type"],
                    "resource": item.get("resource", "FMP"),
                    "price": round(current_price, 4),
                    "change": round(change, 4),
                    "changePercent": round(change_p, 2),
                    "history": history
                }
            else:
                pass
                
    except Exception as e:
        print(f"Error fetching commodity {item['symbol']}: {e}")
        return None

async def fetch_single_commodity(symbol: str, timeframe: str = "daily") -> Optional[Dict[str, Any]]:
    # Find item config
    item_config = None
    for cat, items in COMMODITY_CATEGORIES.items():
        for i in items:
            if i['symbol'] == symbol:
                item_config = i
                break
        if item_config: break
    
    if not item_config:
        item_config = {"symbol": symbol, "name": symbol, "type": "Unknown", "resource": "FMP"}

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

    # Reuse concurrent process_item logic but for single item
    async with httpx.AsyncClient() as client:
        return await process_item(client, item_config, start_date, end_date, days)

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
    
    # We can perform concurrent fetches
    async with httpx.AsyncClient() as client:
        # Create tasks for all items across all categories
        tasks = []
        item_map = [] # To map results back to categories

        for category, items in COMMODITY_CATEGORIES.items():
            # print(f"[COMMODITY] Preparing fetch for category: {category}")
            for item in items:
                tasks.append(process_item(client, item, start_date, end_date, days))
                item_map.append(category)
        
        # Execute all fetches concurrently
        results_list = await asyncio.gather(*tasks)
        
        # Group results by category
        for i, result in enumerate(results_list):
            if result:
                cat = item_map[i]
                if cat not in results:
                    results[cat] = []
                results[cat].append(result)
                
    return results
