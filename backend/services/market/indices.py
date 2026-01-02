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
            {"symbol": "^RUT", "name": "Russell 2000"}
        ],
        "Europe": [
            {"symbol": "^FTSE", "name": "FTSE 100"}
        ],
        "Asia-Pacific": [
            {"symbol": "^N225", "name": "Nikkei 225"},
            {"symbol": "^HSI", "name": "Hang Seng"}
        ]
    }
    
    # 1. Collect all symbols to batch fetch quotes
    all_symbols = []
    for region in regional_indices.values():
        for index in region:
            all_symbols.append(index["symbol"])
            
    # 2. Fetch Live Quotes in Batch
    quotes_map = {}
    try:
        import urllib.parse
        # URL encode individual symbols but keep the comma separators
        safe_symbols = [urllib.parse.quote(s) for s in all_symbols]
        safe_symbols_str = ",".join(safe_symbols)
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Note: httpx will auto-encode path params if not careful, but we are constructing path.
            # Using encoded string in f-string path should work as httpx default assumes path is encoded?
            # Actually, standard practice is let client handle it or careful construction.
            # safe_symbols_str like %5EGSPC,%5EDJI
            quotes_url = f"{FMP_BASE_URL}/quote/{safe_symbols_str}"
            
            # print(f"DEBUG: Fetching quotes from {quotes_url}")
            quotes_resp = await client.get(quotes_url, params={"apikey": FMP_API_KEY})
            if quotes_resp.status_code == 200:
                quotes_data = quotes_resp.json()
                # print(f"DEBUG: Received {len(quotes_data)} quotes")
                if isinstance(quotes_data, list):
                    for q in quotes_data:
                        sym = q["symbol"]
                        quotes_map[sym] = q
                        # Handle potential mismatch where FMP returns "GSPC" for "^GSPC"
                        if sym.startswith("^"):
                             quotes_map[sym[1:]] = q
                        # Or vice versa, if response is GSPC but we asked for ^GSPC and stored that in all_symbols
                        # We will look up by index["symbol"] which has ^.
                        # So if response has "GSPC", we map "GSPC"->q.
                        # But lookup will be "^GSPC".
                        # So we should validly map GSPC -> ^GSPC logic? 
                        # No, just ensure we can find it.
                        if not sym.startswith("^"):
                            quotes_map[f"^{sym}"] = q
            else:
                 print(f"Error fetching quotes: Status {quotes_resp.status_code} - {quotes_resp.text}")
    except Exception as e:
        print(f"Error fetching batch quotes: {e}")

    result = {}
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            for region, indices in regional_indices.items():
                region_data = []
                
                for index in indices:
                    try:
                        symbol = index["symbol"]
                        
                        # Fetch historical data
                        endpoint = "historical-price-eod/light"
                        url = f"{FMP_BASE_URL}/{endpoint}"
                        
                        params = {
                            "symbol": symbol,
                            "apikey": FMP_API_KEY
                        }
                        
                        response = await client.get(url, params=params)
                        
                        history = []
                        if response.status_code == 200:
                            data = response.json()
                            if data and isinstance(data, list):
                                # Get historical data (last 1 year)
                                for item in data[:252]:
                                    history.append({
                                        "symbol": symbol,
                                        "date": item.get("date"),
                                        "price": item.get("price", 0) or item.get("close", 0),
                                        "volume": item.get("volume", 0)
                                    })
                        
                        # Use Live Quote if available, otherwise fallback to history
                        quote = quotes_map.get(symbol)
                        
                        if quote:
                            current_price = quote.get("price", 0)
                            change = quote.get("change", 0)
                            change_percent = quote.get("changesPercentage", 0) # FMP Key is changesPercentage
                            
                            # Update History with Live Point?
                            # If the quote timestamp/date is newer than the last history point, append it.
                            # FMP history dates are string YYYY-MM-DD. Quote timestamp is unix.
                            # Usually, EOD is previous day. Live is today.
                            # So we should append live point to history for chart continuity.
                            if history:
                                last_date_str = history[0]["date"] # History is newest first from API? yes.
                                # Check if we need to insert today
                                # Simple check: just insert it at the beginning (newest)
                                # But verify we don't duplicate via date check?
                                # Ideally convert quote timestamp to YYYY-MM-DD
                                import datetime
                                ts = quote.get("timestamp")
                                if ts:
                                    quote_date = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                                    if quote_date != last_date_str:
                                         history.insert(0, {
                                            "symbol": symbol,
                                            "date": quote_date,
                                            "price": current_price,
                                            "volume": quote.get("volume", 0)
                                        })
                                    else:
                                        # Update today's bar
                                        history[0]["price"] = current_price
                                        history[0]["volume"] = quote.get("volume", 0)
                            
                        elif history:
                            # Fallback to historical calculation
                            latest = history[0]
                            previous = history[1] if len(history) > 1 else latest
                            current_price = latest["price"]
                            prev_price = previous["price"]
                            change = current_price - prev_price
                            change_percent = (change / prev_price * 100) if prev_price != 0 else 0
                        else:
                            current_price = 0
                            change = 0 
                            change_percent = 0

                        region_data.append({
                            "symbol": symbol,
                            "name": index["name"],
                            "price": round(current_price, 2),
                            "change": round(change, 2),
                            "changePercent": round(change_percent, 2),
                            "history": list(reversed(history[:200]))  # Limit and Oldest to newest
                        })
                            
                    except Exception as e:
                        # print(f"Error fetching {index['symbol']}: {e}")
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

async def fetch_sector_performance():
    """
    Fetch sector performance from FMP.
    Returns list of {sector, changesPercentage}.
    """
    if not FMP_API_KEY:
        return []

    url = f"{FMP_BASE_URL}/sector-performance"
    params = {"apikey": FMP_API_KEY}
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                # Clean percentages
                for item in data:
                    c = item.get('changesPercentage', 0)
                    if isinstance(c, str):
                        try:
                            item['changesPercentage'] = float(c.strip('%'))
                        except:
                            item['changesPercentage'] = 0.0
                return data
    except Exception as e:
        print(f"Error fetching sector performance: {e}")
    return []

async def fetch_industry_performance():
    """
    Fetch industry performance from FMP.
    Returns list of top 5 and bottom 5 industries.
    """
    if not FMP_API_KEY:
        return []

    url = f"{FMP_BASE_URL}/stock-market-performance/industry-performance"
    params = {"apikey": FMP_API_KEY}
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                   for item in data:
                       c = item.get('changesPercentage', 0)
                       if isinstance(c, str):
                           try:
                               item['changesPercentage'] = float(c.strip('%'))
                           except:
                               item['changesPercentage'] = 0.0
                   
                   # Sort descending
                   data.sort(key=lambda x: x.get('changesPercentage', 0), reverse=True)
                   
                   top_5 = data[:5]
                   bottom_5 = data[-5:]
                   return top_5 + bottom_5
    except Exception as e:
        print(f"Error fetching industry performance: {e}")
    return []
