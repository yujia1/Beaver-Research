from typing import List, Dict, Any
from redis_client import redis_client

# Direct symbol usage (no mapping needed)

def fetch_currency_from_yahoo(symbol: str, timeframe: str) -> List[Dict[str, Any]]:
    """
    Fetch currency exchange rate data.
    Legacy name kept for compatibility with macro.py, but now fetches from Redis (populated by FMP scheduler).
    Default fallback to empty if not in cache (Background worker handles fetching).
    """
    try:
        # Check cache populated by scheduler (services/market/currency.py)
        # Scheduler saves all currencies in one dict under "currency:data:monthly"
        # We assume 'monthly' cache is generally sufficient for the dashboard line charts.
        
        cached_data = redis_client.get_cache("currency:data:monthly")
        
        if cached_data and symbol in cached_data:
            print(f"[CURRENCY] Hit cache for {symbol}")
            return cached_data[symbol]
            
        print(f"[CURRENCY] Cache miss for {symbol}")
        return []
        
    except Exception as e:
        print(f"Error fetching currency {symbol}: {e}")
        return []
