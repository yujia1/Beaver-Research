from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from redis_client import redis_client
from services.market.economic import fetch_all_economic_data, fetch_economic_series

router = APIRouter()

class MacroData(BaseModel):
    indicator: str
    value: Optional[float] = None
    date: Optional[str] = None
    description: str
    category: str
    series_id: Optional[str] = None
    history: Optional[List[Dict[str, Any]]] = None
    chart_type: str = "line"

# Mapping for timeframe to cache keys
period_map = {
    "monthly": "1y",
    "quarterly": "3y",
    "yearly": "5y",
    "5y": "5y",
    "max": "max"
}

@router.get("/macro", response_model=List[MacroData])
async def get_macro_data(timeframe: str = "monthly"):
    """
    Fetch macro economic data from FMP API.
    
    Args:
        timeframe: Time period (monthly, quarterly, yearly, 5y, max)
    
    Returns:
        List of economic indicators with historical data
    """
    cache_key = f"macro:{timeframe}"
    cached_data = redis_client.get_cache(cache_key)
    if cached_data:
        return cached_data
    
    try:
        # Fetch all economic data from FMP
        results = await fetch_all_economic_data(timeframe)
        
        # Add FedWatch Tool (mock data for now - can be replaced with real CME FedWatch data)
        results.append({
            "indicator": "FedWatch Tool",
            "value": 5.25,
            "date": str(datetime.today().date()),
            "description": "Target Rate Probabilities",
            "category": "Monetary",
            "chart_type": "bar",
            "series_id": "FEDWATCH",
            "history": [
                {"date": "Hold", "value": 60},
                {"date": "Cut 25bps", "value": 35},
                {"date": "Cut 50bps", "value": 5},
                {"date": "Hike 25bps", "value": 0}
            ]
        })
        
        # Cache for 4 hours
        redis_client.set_cache(cache_key, results, ttl=14400)
        return results
        
    except Exception as e:
        print(f"Error fetching macro data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch macro data: {str(e)}")

@router.get("/macro/series/{series_id}", response_model=MacroData)
async def get_macro_series(series_id: str, timeframe: str = "monthly"):
    """
    Fetch a specific economic series by ID.
    
    Args:
        series_id: The FMP indicator name (e.g., 'GDP', 'CPI', 'unemploymentRate')
        timeframe: Time period (monthly, quarterly, yearly, 5y, max)
    
    Returns:
        Economic indicator data with history
    """
    # Special handling for FedWatch
    if series_id == "FEDWATCH":
        return {
            "indicator": "FedWatch Tool",
            "value": 5.25,
            "date": str(datetime.today().date()),
            "description": "Target Rate Probabilities",
            "category": "Monetary",
            "chart_type": "bar",
            "series_id": "FEDWATCH",
            "history": [
                {"date": "Hold", "value": 60},
                {"date": "Cut 25bps", "value": 35},
                {"date": "Cut 50bps", "value": 5},
                {"date": "Hike 25bps", "value": 0}
            ]
        }
    
    try:
        # Fetch the specific series from FMP
        result = await fetch_economic_series(series_id, timeframe)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"Error fetching series {series_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch series: {str(e)}")
