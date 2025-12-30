import httpx
import yfinance as yf
import os
import pandas as pd
from datetime import datetime, timedelta

# FMP Base URL extracted and centralized
FMP_BASE_URL = "https://financialmodelingprep.com/stable"
# Define API KEY at module level
FMP_API_KEY = os.getenv("FMP_API_KEY", "")

async def fetch_regional_indices_data():
    """
    Fetch global market indices organized by region using Financial Modeling Prep API.
    Returns indices grouped by: United States, Europe, Asia-Pacific
    """
    if not FMP_API_KEY:
        print("FMP_API_KEY not configured")
        return {}
    
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
        ]
    }
    
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
        
        return result
        
    except Exception as e:
        print(f"Error fetching regional indices: {e}")
        return {}

async def fetch_major_indices_data():
    """
    Fetch real-time data for major market indices: Dow Jones, NASDAQ, S&P 500, Russell 2000.
    """
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
        
        return results
    except Exception as e:
        print(f"Error fetching indices: {e}")
        # Return empty results on critical failure
        return [{"name": idx["name"], "key": idx["key"], "value": 0.0, "change": 0.0, "history": []} for idx in indices_config]
