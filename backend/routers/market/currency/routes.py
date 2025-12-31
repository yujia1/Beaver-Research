from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from redis_client import redis_client

router = APIRouter()

class CurrencyData(BaseModel):
    series_id: str
    indicator: str
    description: str
    value: Optional[float] = None
    date: Optional[str] = None
    history: List[Dict[str, Any]]

# Currency metadata
CURRENCY_METADATA = {
    "DEXUSEU": {
        "indicator": "U.S. / Euro Foreign Exchange Rate",
        "description": "U.S. Dollars to One Euro"
    },
    "DEXJPUS": {
        "indicator": "Japanese Yen to U.S. Dollar Spot Exchange Rate",
        "description": "Japanese Yen to One U.S. Dollar"
    },
    "DEXCHUS": {
        "indicator": "China / U.S. Foreign Exchange Rate",
        "description": "Chinese Yuan to One U.S. Dollar"
    }
}

@router.get("/currencies", response_model=List[Dict[str, Any]])
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
        for series_id, history in cached_data.items():
            if series_id in CURRENCY_METADATA:
                metadata = CURRENCY_METADATA[series_id]
                
                # Get latest value
                latest_value = history[-1]["value"] if history else 0.0
                latest_date = history[-1]["date"] if history else ""
                
                results.append({
                    "series_id": series_id,
                    "indicator": metadata["indicator"],
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

@router.get("/currencies/{series_id}")
async def get_currency_by_series(series_id: str):
    """
    Get a specific currency by its series ID.
    
    Args:
        series_id: The FRED series ID (e.g., 'DEXUSEU', 'DEXJPUS', 'DEXCHUS')
    
    Returns:
        Currency data with history
    """
    try:
        cached_data = redis_client.get_cache("currency:data:monthly")
        
        if not cached_data or series_id not in cached_data:
            raise HTTPException(status_code=404, detail=f"Currency {series_id} not found")
        
        if series_id not in CURRENCY_METADATA:
            raise HTTPException(status_code=404, detail=f"Unknown currency series: {series_id}")
        
        metadata = CURRENCY_METADATA[series_id]
        history = cached_data[series_id]
        
        # Get latest value
        latest_value = history[-1]["value"] if history else 0.0
        latest_date = history[-1]["date"] if history else ""
        
        return {
            "series_id": series_id,
            "indicator": metadata["indicator"],
            "description": metadata["description"],
            "value": latest_value,
            "date": latest_date,
            "history": history,
            "selectedTimeframe": "monthly",
            "loading": False,
            "chart_type": "line",
            "category": "Currency"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching currency {series_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch currency: {str(e)}")
