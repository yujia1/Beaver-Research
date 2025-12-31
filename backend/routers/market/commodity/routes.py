from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from redis_client import redis_client

router = APIRouter()

class CommodityData(BaseModel):
    symbol: str
    name: str
    type: str
    price: float
    change: float
    changePercent: float
    history: List[Dict[str, Any]]

@router.get("/commodities", response_model=Dict[str, List[Dict[str, Any]]])
async def get_all_commodities():
    """
    Get all commodity data organized by category.
    Returns data from Redis cache populated by the scheduler.
    
    Returns:
        Dict with categories as keys (Financials, Metals, Energy, Agriculture, Softs & Livestock)
        and lists of commodity data as values
    """
    try:
        # Get cached data from scheduler
        cached_data = redis_client.get_cache("commodity:data:monthly")
        
        if cached_data:
            return cached_data
        else:
            # Return empty structure if no data yet
            return {
                "Financials": [],
                "Metals": [],
                "Energy": [],
                "Agriculture": [],
                "Softs & Livestock": []
            }
            
    except Exception as e:
        print(f"Error fetching commodities: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch commodity data: {str(e)}")

@router.get("/commodities/{symbol}")
async def get_commodity_by_symbol(symbol: str):
    """
    Get a specific commodity by its symbol.
    
    Args:
        symbol: The FMP commodity symbol (e.g., 'GCUSD', 'SIUSD')
    
    Returns:
        Commodity data with history
    """
    try:
        cached_data = redis_client.get_cache("commodity:data:monthly")
        
        if not cached_data:
            raise HTTPException(status_code=404, detail="Commodity data not available")
        
        # Search through all categories
        for category, items in cached_data.items():
            for item in items:
                if item.get("symbol") == symbol:
                    return item
        
        raise HTTPException(status_code=404, detail=f"Commodity {symbol} not found")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching commodity {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch commodity: {str(e)}")
