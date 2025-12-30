import yfinance as yf
from typing import List, Dict, Any

# Mapping of commodity series IDs to Yahoo Finance ticker symbols
# Mapping of commodity series IDs to FMP/Yahoo tickers (kept for reference or cache keys)
# Updated to match new categorization strategy using FMP symbols where possible
commodity_ticker_map = {
    # Financials
    "ZQUSD": "ZQUSD", "ZTUSD": "ZTUSD", "ZFUSD": "ZFUSD", "ZNUSD": "ZNUSD", "ZBUSD": "ZBUSD",
    "DXUSD": "DXUSD", "ESUSD": "ESUSD", "NQUSD": "NQUSD", "YMUSD": "YMUSD", "RTYUSD": "RTYUSD",
    
    # Metals (Legacy IDs -> FMP Symbols)
    "GOLDAMGBD228NLBM": "GCUSD", # Gold
    "SILVER": "SIUSD",           # Silver
    "PLATINUM": "PLUSD",         # Platinum
    "PCOPPUSDM": "HGUSD",        # Copper
    "PALUMINUM": "ALIUSD",       # Aluminum
    
    # Energy
    "POILBREUSDM": "CLUSD",      # Crude Oil (WTI)
    "PNRGINDEXM": "NGUSD",       # Natural Gas
    
    # Agriculture
    "PWHEAMTUSDM": "KEUSX",      # Wheat
    "PCORNUSDM": "ZCUSX",        # Corn
    "PSOYBUSDM": "ZSUSX",        # Soybeans
    "ZOUSX": "ZOUSX",            # Oats
    "ZRUSD": "ZRUSD",            # Rough Rice

    # Softs & Livestock (Legacy IDs -> FMP Symbols if generic, or direct FMP symbols)
    "PCOFFUSDM": "KCUSX",        # Coffee
    "PSUGAR": "SBUSX",           # Sugar
    "CCUSD": "CCUSD",            # Cocoa
    "CTUSX": "CTUSX",            # Cotton
    "OJUSX": "OJUSX",            # Orange Juice
    "PLUMBER": "LBUSD",          # Lumber
    "LEUSX": "LEUSX",            # Live Cattle
    "GFUSX": "GFUSX",            # Feeder Cattle
    "HEUSX": "HEUSX",            # Lean Hogs
    "PMILK": "DCUSD",            # Class III Milk
}

from redis_client import redis_client

def fetch_commodity_from_yahoo(series_id: str, timeframe: str) -> List[Dict[str, Any]]:
    """
    Fetch commodity data.
    Legacy name kept for compatibility with macro.py, but now fetches from Redis (populated by FMP scheduler).
    Default fallback to empty if not in cache (Background worker handles fetching).
    """
    try:
        # Check cache populated by scheduler (services/market/commodity.py)
        # Scheduler saves data as { Category: [ { symbol, ... }, ... ] } under "commodity:data:monthly"
        
        cached_data = redis_client.get_cache("commodity:data:monthly")
        
        if cached_data:
            # We need to find the specific series_id (mapped to FMP symbol) in the categorized data
            target_symbol = commodity_ticker_map.get(series_id, series_id)
            
            for category, items in cached_data.items():
                for item in items:
                    if item.get("symbol") == target_symbol:
                        print(f"[COMMODITY] Hit cache for {series_id} ({target_symbol})")
                        # The item["history"] is already in the right format
                        return item.get("history", [])
                        
        print(f"[COMMODITY] Cache miss for {series_id}")
        return []
        
    except Exception as e:
        print(f"Error fetching commodity {series_id}: {e}")
        return []
