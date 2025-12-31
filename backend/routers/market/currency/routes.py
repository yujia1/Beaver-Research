from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from redis_client import redis_client

router = APIRouter()

class CurrencyData(BaseModel):
    symbol: str
    name: str
    description: str
    value: Optional[float] = None
    date: Optional[str] = None
    history: List[Dict[str, Any]]

# Currency metadata (matches currency.py)
CURRENCY_METADATA = {
    "EURUSD": {
        "name": "EUR/USD",
        "description": "Euro to U.S. Dollar"
    },
    "JPYUSD": {
        "name": "JPY/USD",
        "description": "Japanese Yen to U.S. Dollar"
    },
    "CNYUSD": {
        "name": "CNY/USD",
        "description": "Chinese Yuan to U.S. Dollar"
    }
}

@router.get("/", response_model=List[Dict[str, Any]])
async def get_all_currencies():
    """
    Get all currency data.
    Returns data from Redis cache populated by the scheduler.
    
    Returns:
        List of currency data with history
    """
    try:
        # Get cached data from scheduler
        cached_data = redis_client.get_cache("currency:data:monthly")
        
        if not cached_data:
            # Return empty list if no data yet
            return []
        
        # Transform to frontend format
        results = []
        for symbol, history in cached_data.items():
            if symbol in CURRENCY_METADATA:
                metadata = CURRENCY_METADATA[symbol]
                
                # Get latest value
                latest_value = history[-1]["value"] if history else 0.0
                latest_date = history[-1]["date"] if history else ""
                
                results.append({
                    "symbol": symbol,
                    "name": metadata["name"],
                    "description": metadata["description"],
                    "value": latest_value,
                    "date": latest_date,
                    "history": history,
                    "selectedTimeframe": "monthly",
                    "loading": False,
                    "chart_type": "line",
                    "category": "Currency"
                })
        
        return results
            
    except Exception as e:
        print(f"Error fetching currencies: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch currency data: {str(e)}")

@router.get("/{symbol}")
async def get_currency_by_symbol(symbol: str, timeframe: str = "monthly"):
    """
    Get a specific currency by its symbol.
    
    Args:
        symbol: The FMP forex symbol (e.g., 'EURUSD', 'USDJPY', 'USDCNY')
        timeframe: Time period (currently only 'monthly' is supported)
    
    Returns:
        Currency data with history
    """
    try:
        # For now, we only have monthly data cached by the scheduler
        # In the future, we could fetch different timeframes from FMP
        cached_data = redis_client.get_cache("currency:data:monthly")
        
        if not cached_data or symbol not in cached_data:
            raise HTTPException(status_code=404, detail=f"Currency {symbol} not found")
        
        if symbol not in CURRENCY_METADATA:
            raise HTTPException(status_code=404, detail=f"Unknown currency symbol: {symbol}")
        
        metadata = CURRENCY_METADATA[symbol]
        history = cached_data[symbol]
        
        # Get latest value
        latest_value = history[-1]["value"] if history else 0.0
        latest_date = history[-1]["date"] if history else ""
        
        return {
            "symbol": symbol,
            "name": metadata["name"],
            "description": metadata["description"],
            "value": latest_value,
            "date": latest_date,
            "history": history,
            "selectedTimeframe": timeframe,
            "loading": False,
            "chart_type": "line",
            "category": "Currency"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching currency {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch currency: {str(e)}")
