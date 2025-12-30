from fastapi import APIRouter, HTTPException
from redis_client import redis_client
import httpx
import os

router = APIRouter()

# FMP Base URL extracted and centralized, similar to how it's done in other routers if applicable,
# but here specifically defined for clarity as requested.
FMP_BASE_URL = "https://financialmodelingprep.com/stable"
# Using the same constant base URL logic as implied by the user request reference to portfolio.py
# In portfolio.py: FMP_BASE_URL = "https://financialmodelingprep.com/stable"

# Define API KEY at module level
FMP_API_KEY = os.getenv("FMP_API_KEY", "")

@router.get("/regional")
async def get_regional_indices():
    """
    Fetch global market indices organized by region using Financial Modeling Prep API.
    Returns indices grouped by: United States, Europe, Asia-Pacific, Canada, Emerging Markets, Global
    """
    
    if not FMP_API_KEY:
        raise HTTPException(status_code=500, detail="FMP_API_KEY not configured")
    
    # Define indices by region
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
        ],
        "Canada": [
            {"symbol": "^GSPTSE", "name": "TSX Composite"},
            {"symbol": "TX60.TS", "name": "TSX 60"},
            {"symbol": "^SPCDNX", "name": "TSX Venture"}
        ],
        "Emerging Markets": [
            {"symbol": "^BVSP", "name": "Bovespa"},
            {"symbol": "^MXX", "name": "IPC Mexico"},
            {"symbol": "^TASI.SR", "name": "Tadawul"},
            {"symbol": "^JKSE", "name": "Jakarta Composite"},
            {"symbol": "XU100.IS", "name": "BIST 100"}
        ],
        "Global": [
            {"symbol": "MSCIWORLD", "name": "MSCI World"},
            {"symbol": "^W1DOW", "name": "DJ Global"}
        ]
    }
    
    # Check cache first
    cache_key = "indices:regional:all"
    cached_data = redis_client.get_cache(cache_key)
    if cached_data:
        return cached_data
    
    result = {}
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            for region, indices in regional_indices.items():
                region_data = []
                
                for index in indices:
                    try:
                        # Fetch current price data from FMP using the centralized BASE URL
                        # Endpoint: /historical-price-eod/light matches the one used before but now using FMP_BASE_URL
                        # Note: portfolio.py constructs url as f"{FMP_BASE_URL}/{endpoint}"
                        
                        endpoint = "historical-price-eod/light"
                        url = f"{FMP_BASE_URL}/{endpoint}"
                        
                        params = {
                            "symbol": index["symbol"],
                            "apikey": FMP_API_KEY
                        }
                        
                        response = await client.get(url, params=params)
                        
                        if response.status_code == 200:
                            data = response.json()
                            
                            if data and isinstance(data, list) and len(data) > 0:
                                latest = data[0]
                                previous = data[1] if len(data) > 1 else latest
                                
                                current_price = latest.get("close", 0)
                                previous_close = previous.get("close", current_price)
                                change = current_price - previous_close
                                change_percent = (change / previous_close * 100) if previous_close != 0 else 0
                                
                                # Get historical data for chart (last 30 days)
                                history = []
                                for item in data[:30]:
                                    history.append({
                                        "symbol": index["symbol"],
                                        "date": item.get("date"),
                                        "price": item.get("close", 0),
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
        
        # Cache for 15 minutes
        if result:
            redis_client.set_cache(cache_key, result, ttl=900)
        
        return result
        
    except Exception as e:
        print(f"Error fetching regional indices: {e}")
        return {}
