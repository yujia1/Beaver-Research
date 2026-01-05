from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
import httpx
import pandas as pd
import os
from typing import Optional

router = APIRouter()

# FMP API Configuration
FMP_API_KEY = os.getenv("FMP_API_KEY", "l4DHwKBRg3uFTkojVxlRAV1KE90I9gOm")
FMP_BASE_URL = "https://financialmodelingprep.com"


async def fetch_fmp_historical_data(
    ticker: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
) -> pd.DataFrame:
    """
    Fetch historical OHLCV data from Financial Modeling Prep API.
    
    Args:
        ticker: Stock ticker symbol
        from_date: Start date in YYYY-MM-DD format (optional)
        to_date: End date in YYYY-MM-DD format (optional)
    
    Returns:
        DataFrame with columns: date, open, high, low, close, volume
    """
    url = f"{FMP_BASE_URL}/stable/historical-price-eod/full"
    params = {
        "symbol": ticker.upper(),
        "apikey": FMP_API_KEY
    }
    
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # FMP API returns a list directly for this endpoint
            if not data or not isinstance(data, list):
                raise HTTPException(
                    status_code=404,
                    detail=f"No historical data found for ticker {ticker}"
                )
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Ensure proper data types and sort chronologically
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            
            # Select relevant columns
            df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
            
            return df
            
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"FMP API error: {e.response.text}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching data from FMP: {str(e)}"
            )


def detect_trend(df: pd.DataFrame) -> dict:
    """
    Detect market trend using Simple Moving Averages.
    
    Logic:
    - Bullish: Price > SMA(50) > SMA(200)
    - Bearish: Price < SMA(50) < SMA(200)
    - Neutral: No clear alignment
    
    Returns:
        Dictionary with trend status and SMA values
    """
    # Calculate SMAs
    df['sma_50'] = df['close'].rolling(window=50).mean()
    df['sma_200'] = df['close'].rolling(window=200).mean()
    
    # Get latest values
    latest = df.iloc[-1]
    current_price = latest['close']
    sma_50 = latest['sma_50']
    sma_200 = latest['sma_200']
    
    # Determine trend
    if pd.isna(sma_50) or pd.isna(sma_200):
        status = "Insufficient Data"
    elif current_price > sma_50 > sma_200:
        status = "Uptrend"
    elif current_price < sma_50 < sma_200:
        status = "Downtrend"
    else:
        status = "Neutral"
    
    return {
        "status": status,
        "sma_50": round(float(sma_50), 2) if not pd.isna(sma_50) else None,
        "sma_200": round(float(sma_200), 2) if not pd.isna(sma_200) else None
    }


def calculate_fibonacci_levels(df: pd.DataFrame, trend: str, lookback_days: int = 90) -> dict:
    """
    Calculate Fibonacci retracement and extension levels.
    
    Args:
        df: DataFrame with OHLCV data
        trend: Current trend status ("Uptrend", "Downtrend", or "Neutral")
        lookback_days: Number of days to look back for swing points
    
    Returns:
        Dictionary with setup type, swing points, and Fibonacci levels
    """
    # Get lookback period
    lookback_df = df.tail(lookback_days)
    
    if len(lookback_df) < 2:
        raise HTTPException(
            status_code=400,
            detail="Insufficient data for Fibonacci calculation"
        )
    
    # Find swing high and low
    swing_high = lookback_df['high'].max()
    swing_low = lookback_df['low'].min()
    current_price = df.iloc[-1]['close']
    
    # Determine setup type based on trend
    if trend == "Uptrend":
        setup_type = "Long"
        # For long setup: measure from swing low to swing high
        diff = swing_high - swing_low
        
        # Retracement levels (potential buy zones)
        fib_0_382 = swing_high - (diff * 0.382)
        fib_0_5 = swing_high - (diff * 0.5)
        fib_0_618 = swing_high - (diff * 0.618)
        
        # Extension levels (price targets)
        target_1_272 = swing_high + (diff * 0.272)
        target_1_618 = swing_high + (diff * 0.618)
        
    elif trend == "Downtrend":
        setup_type = "Short"
        # For short setup: measure from swing high to swing low
        diff = swing_high - swing_low
        
        # Retracement levels (potential short entry zones)
        fib_0_382 = swing_low + (diff * 0.382)
        fib_0_5 = swing_low + (diff * 0.5)
        fib_0_618 = swing_low + (diff * 0.618)
        
        # Extension levels (price targets downwards)
        target_1_272 = swing_low - (diff * 0.272)
        target_1_618 = swing_low - (diff * 0.618)
        
    else:  # Neutral
        setup_type = "Neutral"
        diff = swing_high - swing_low
        
        # Provide both long and short levels for neutral trend
        fib_0_382 = swing_high - (diff * 0.382)
        fib_0_5 = swing_high - (diff * 0.5)
        fib_0_618 = swing_high - (diff * 0.618)
        target_1_272 = swing_high + (diff * 0.272)
        target_1_618 = swing_high + (diff * 0.618)
    
    return {
        "setup": {
            "type": setup_type,
            "swing_low": round(float(swing_low), 2),
            "swing_high": round(float(swing_high), 2)
        },
        "levels": {
            "entry_zone_0.382": round(float(fib_0_382), 2),
            "entry_zone_0.5": round(float(fib_0_5), 2),
            "entry_zone_0.618": round(float(fib_0_618), 2),
            "take_profit_1.272": round(float(target_1_272), 2),
            "take_profit_1.618": round(float(target_1_618), 2)
        }
    }


@router.get("/fibonacci/{ticker}")
async def get_fibonacci_analysis(
    ticker: str,
    days: int = Query(default=365, ge=90, le=1825, description="Number of days of historical data (90-1825)"),
    lookback: int = Query(default=90, ge=30, le=365, description="Lookback period for swing points (30-365)")
):
    """
    Get Fibonacci retracement analysis for a given ticker.
    
    Args:
        ticker: Stock ticker symbol
        days: Number of days of historical data to fetch (default: 365, min: 90, max: 1825/5 years)
        lookback: Lookback period in days for finding swing points (default: 90, min: 30, max: 365)
    
    Returns:
        JSON with trend analysis, setup type, and Fibonacci levels
    """
    # Calculate date range
    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    # Fetch historical data
    df = await fetch_fmp_historical_data(ticker, from_date, to_date)
    
    if len(df) < 200:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient data for analysis. Need at least 200 days, got {len(df)} days."
        )
    
    # Get current price
    current_price = df.iloc[-1]['close']
    
    # Detect trend
    trend_analysis = detect_trend(df)
    
    # Calculate Fibonacci levels
    fib_result = calculate_fibonacci_levels(df, trend_analysis["status"], lookback)
    
    return {
        "ticker": ticker.upper(),
        "current_price": round(float(current_price), 2),
        "data_period": {
            "from": from_date,
            "to": to_date,
            "days": len(df)
        },
        "trend_analysis": trend_analysis,
        **fib_result
    }
