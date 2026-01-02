from fastapi import APIRouter, HTTPException
from redis_client import redis_client
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import pandas as pd
import os
from datetime import datetime, timedelta
from pandas_datareader import data as web
import yfinance as yf

router = APIRouter()

# Mapping for timeframe to date offset
period_map = {
    "daily": "30d",
    "weekly": "3mo",
    "monthly": "1y",
    "yearly": "5y",
    "max": "max"
}

# Mapping of Treasury yield FRED series IDs to Yahoo Finance ticker symbols
# Yahoo Finance provides real-time Treasury yield data
treasury_yield_ticker_map = {
    "DGS3MO": "^IRX",  # 3-Month Treasury Bill (13-week)
    "DGS2": "^FVX",    # 5-Year Treasury Note (closest to 2-year, using 5-year as proxy)
    "DGS5": "^FVX",    # 5-Year Treasury Note
    "DGS10": "^TNX",   # 10-Year Treasury Note
    "DGS30": "^TYX",   # 30-Year Treasury Bond
}

def fetch_fred_series(series_id: str, start_date: str):
    """Fetch a series from FRED and return list of {'date': str, 'value': float} sorted oldest to newest."""
    try:
        df = web.DataReader(series_id, 'fred', start=start_date, api_key=os.getenv('FRED_API_KEY'))
        df = df.dropna()
        df = df.reset_index()
        df.columns = ['date', 'value']
        df['date'] = df['date'].dt.strftime('%Y-%m-%d')
        df['value'] = df['value'].astype(float)
        return df.to_dict(orient='records')
    except Exception as e:
        print(f"Error fetching FRED series {series_id}: {e}")
        return []

def calculate_start_date(offset: str) -> str:
    """Convert offset string to start date."""
    today = datetime.today()
    if offset == "max":
        return "1900-01-01"
    elif offset.endswith('d'):
        days = int(offset.rstrip('d'))
        return (today - timedelta(days=days)).strftime('%Y-%m-%d')
    elif offset.endswith('mo'):
        months = int(offset.rstrip('mo'))
        return (today - timedelta(days=months*30)).strftime('%Y-%m-%d')
    elif offset.endswith('y'):
        years = int(offset.rstrip('y'))
        return (today - timedelta(days=years*365)).strftime('%Y-%m-%d')
    else:
        return (today - timedelta(days=365)).strftime('%Y-%m-%d')

def fetch_yfinance_series(ticker: str, start_date: str):
    """Fetch a series from Yahoo Finance and return list of {'date': str, 'value': float}."""
    try:
        stock = yf.Ticker(ticker)
        # Calculate period based on start_date
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        days_diff = (datetime.today() - start_dt).days
        
        if days_diff <= 30:
            period = "1mo"
            interval = "1d"
        elif days_diff <= 90:
            period = "3mo"
            interval = "1d"
        elif days_diff <= 365:
            period = "1y"
            interval = "1d"
        else:
            period = "5y"
            interval = "1wk"
        
        # Use start parameter with period, or use history with start/end dates
        hist = stock.history(start=start_date, interval=interval)
        
        if hist.empty:
            # Fallback: try with period instead
            hist = stock.history(period=period, interval=interval)
        
        if hist.empty:
            return []
        
        hist = hist.reset_index()
        # Handle both DatetimeIndex and Date column
        if 'Date' in hist.columns:
            hist['Date'] = pd.to_datetime(hist['Date']).dt.strftime('%Y-%m-%d')
        else:
            hist.index = pd.to_datetime(hist.index)
            hist = hist.reset_index()
            hist.columns = ['Date'] + list(hist.columns[1:])
            hist['Date'] = hist['Date'].dt.strftime('%Y-%m-%d')
        
        hist = hist[['Date', 'Close']]
        hist.columns = ['date', 'value']
        hist = hist.dropna()
        hist['value'] = hist['value'].astype(float)
        # Filter to only include dates >= start_date
        hist = hist[hist['date'] >= start_date]
        
        records = hist.to_dict(orient='records')
        
        # Merge Real-Time Data using fast_info
        try:
            # fast_info provides efficient access to latest price
            last_price = stock.fast_info.last_price
            # timezone = stock.fast_info.timezone # usually 'America/New_York'
            
            # Simple check: if valid price
            if last_price is not None and last_price > 0:
                # Get Today's date
                today_str = datetime.today().strftime('%Y-%m-%d')
                
                # Check if we need to append or update
                if records:
                    last_record_date = records[-1]['date']
                    if last_record_date != today_str:
                        # Append new record for today
                        records.append({
                            'date': today_str,
                            'value': float(last_price)
                        })
                    else:
                        # Update today's record (it might be partial/EOD)
                        records[-1]['value'] = float(last_price)
                else:
                    # No history, just add today
                    records.append({
                        'date': today_str,
                        'value': float(last_price)
                    })
                    
        except Exception as e:
            # print(f"Error fetching fast_info for {ticker}: {e}")
            pass
            
        return records
    except Exception as e:
        print(f"Error fetching yfinance series {ticker}: {e}")
        return []

class BondData(BaseModel):
    category: str
    title: str
    series_id: Optional[str] = None
    current_value: Optional[float] = None
    current_date: Optional[str] = None
    description: Optional[str] = None
    history: Optional[List[Dict[str, Any]]] = None
    chart_type: str = "line"

@router.get("/treasury-yields", response_model=List[BondData])
async def get_treasury_yields(timeframe: str = "monthly"):
    """
    Fetch Treasury Yields (3m, 2y, 5y, 10y, 30y) from Yahoo Finance (primary) or FRED (fallback).
    Yahoo Finance provides more up-to-date data than FRED.
    Caches results for 1 hour.
    """
    cache_key = f"bond:treasury:{timeframe}:v2"
    cached_data = redis_client.get_cache(cache_key)
    if cached_data:
        return cached_data

    start_offset = period_map.get(timeframe, "1y")
    start_date = calculate_start_date(start_offset)
    
    treasury_series = [
        {"title": "3-Month Treasury Yield", "series_id": "DGS3MO", "description": "3-Month Treasury Constant Maturity Rate (%)"},
        {"title": "2-Year Treasury Yield", "series_id": "DGS2", "description": "2-Year Treasury Constant Maturity Rate (%)"},
        {"title": "5-Year Treasury Yield", "series_id": "DGS5", "description": "5-Year Treasury Constant Maturity Rate (%)"},
        {"title": "10-Year Treasury Yield", "series_id": "DGS10", "description": "10-Year Treasury Constant Maturity Rate (%)"},
        {"title": "30-Year Treasury Yield", "series_id": "DGS30", "description": "30-Year Treasury Constant Maturity Rate (%)"},
    ]
    
    results = []
    for series in treasury_series:
        series_id = series["series_id"]
        history = None
        
        # Try Yahoo Finance first for more up-to-date data
        if series_id in treasury_yield_ticker_map:
            yahoo_ticker = treasury_yield_ticker_map[series_id]
            history = fetch_yfinance_series(yahoo_ticker, start_date)
            if history and len(history) > 0:
                print(f"Using Yahoo Finance data for {series_id} ({yahoo_ticker})")
            else:
                print(f"Yahoo Finance failed for {series_id}, trying FRED as fallback")
        
        # Fallback to FRED if Yahoo Finance fails or not available
        if not history or len(history) == 0:
            history = fetch_fred_series(series_id, start_date)
            if history and len(history) > 0:
                print(f"Using FRED data for {series_id}")
        
        if history and len(history) > 0:
            latest = history[-1]
            results.append({
                "category": "Treasury Yields",
                "title": series["title"],
                "series_id": series_id,
                "current_value": latest["value"],
                "current_date": latest["date"],
                "description": series["description"],
                "history": history,
                "chart_type": "line"
            })
    
    redis_client.set_cache(cache_key, results, ttl=3600)  # 1 hour cache
    return results

@router.get("/yield-curve", response_model=List[BondData])
async def get_yield_curve(timeframe: str = "monthly"):
    """
    Calculate Yield Curve Spreads (2s10s, 3m10s, 5s30s).
    Uses Yahoo Finance data (primary) or FRED (fallback) for underlying yields.
    Caches results for 1 hour.
    """
    cache_key = f"bond:yield_curve:{timeframe}:v2"
    cached_data = redis_client.get_cache(cache_key)
    if cached_data:
        return cached_data

    start_offset = period_map.get(timeframe, "1y")
    start_date = calculate_start_date(start_offset)
    
    # Helper function to fetch yield data with Yahoo Finance first, then FRED fallback
    def fetch_yield_data(series_id: str):
        history = None
        if series_id in treasury_yield_ticker_map:
            yahoo_ticker = treasury_yield_ticker_map[series_id]
            history = fetch_yfinance_series(yahoo_ticker, start_date)
            if not history:
                history = fetch_fred_series(series_id, start_date)
        elif not history or len(history) == 0: # Logic check: if yahoo failed or skipping yahoo
             history = fetch_fred_series(series_id, start_date)
        return history
    
    # Wait, the original helper function logic was:
    # if series_id in map: try yahoo. 
    # if not history (yahoo failed or not in map): try fred.
    # I should be careful not to break it.
    # Let's verify the original logic.
    # 188: if series_id in map: yahoo...
    # 191: if not history: fred...
    # That works.
    
    def fetch_yield_data_safe(series_id: str):
         history = None
         if series_id in treasury_yield_ticker_map:
             yahoo_ticker = treasury_yield_ticker_map[series_id]
             history = fetch_yfinance_series(yahoo_ticker, start_date)
         if not history or len(history) == 0:
             history = fetch_fred_series(series_id, start_date)
         return history

    # Fetch individual yields (trying Yahoo Finance first, then FRED)
    dgs2 = fetch_yield_data_safe("DGS2")
    dgs3mo = fetch_yield_data_safe("DGS3MO")
    dgs5 = fetch_yield_data_safe("DGS5")
    dgs10 = fetch_yield_data_safe("DGS10")
    dgs30 = fetch_yield_data_safe("DGS30")
    
    results = []
    
    # Calculate 2s10s spread
    if dgs2 and dgs10:
        spread_2s10s = []
        dgs2_dict = {item['date']: item['value'] for item in dgs2}
        dgs10_dict = {item['date']: item['value'] for item in dgs10}
        common_dates = sorted(set(dgs2_dict.keys()) & set(dgs10_dict.keys()))
        for date in common_dates:
            spread_2s10s.append({
                "date": date,
                "value": round(dgs10_dict[date] - dgs2_dict[date], 3)
            })
        if spread_2s10s:
            latest = spread_2s10s[-1]
            results.append({
                "category": "Yield Curve Spreads",
                "title": "2s10s Spread",
                "description": "10-Year minus 2-Year Treasury Yield Spread (bps)",
                "current_value": latest["value"],
                "current_date": latest["date"],
                "history": spread_2s10s,
                "chart_type": "line",
                "series_id": "SPREAD_2S10S"
            })
    
    # Calculate 3m10s spread
    if dgs3mo and dgs10:
        spread_3m10s = []
        dgs3mo_dict = {item['date']: item['value'] for item in dgs3mo}
        dgs10_dict = {item['date']: item['value'] for item in dgs10}
        common_dates = sorted(set(dgs3mo_dict.keys()) & set(dgs10_dict.keys()))
        for date in common_dates:
            spread_3m10s.append({
                "date": date,
                "value": round(dgs10_dict[date] - dgs3mo_dict[date], 3)
            })
        if spread_3m10s:
            latest = spread_3m10s[-1]
            results.append({
                "category": "Yield Curve Spreads",
                "title": "3m10s Spread",
                "description": "10-Year minus 3-Month Treasury Yield Spread (bps)",
                "current_value": latest["value"],
                "current_date": latest["date"],
                "history": spread_3m10s,
                "chart_type": "line",
                "series_id": "SPREAD_3M10S"
            })
    
    # Calculate 5s30s spread
    if dgs5 and dgs30:
        spread_5s30s = []
        dgs5_dict = {item['date']: item['value'] for item in dgs5}
        dgs30_dict = {item['date']: item['value'] for item in dgs30}
        common_dates = sorted(set(dgs5_dict.keys()) & set(dgs30_dict.keys()))
        for date in common_dates:
            spread_5s30s.append({
                "date": date,
                "value": round(dgs30_dict[date] - dgs5_dict[date], 3)
            })
        if spread_5s30s:
            latest = spread_5s30s[-1]
            results.append({
                "category": "Yield Curve Spreads",
                "title": "5s30s Spread",
                "description": "30-Year minus 5-Year Treasury Yield Spread (bps)",
                "current_value": latest["value"],
                "current_date": latest["date"],
                "history": spread_5s30s,
                "chart_type": "line",
                "series_id": "SPREAD_5S30S"
            })
    
    redis_client.set_cache(cache_key, results, ttl=3600)  # 1 hour cache
    return results

@router.get("/series/{series_id}", response_model=BondData)
async def get_bond_series(series_id: str, timeframe: str = "monthly"):
    """
    Fetch a single bond market data series.
    Handles both raw FRED IDs and calculated spread IDs.
    """
    start_offset = period_map.get(timeframe, "1y")
    start_date = calculate_start_date(start_offset)

    # Handle calculated spreads
    if series_id.startswith("SPREAD_"):
        # We need to fetch components and calculate
        if series_id == "SPREAD_2S10S":
            s1, s2 = "DGS2", "DGS10"
            title, desc = "2s10s Spread", "10-Year minus 2-Year Treasury Yield Spread (bps)"
        elif series_id == "SPREAD_3M10S":
            s1, s2 = "DGS3MO", "DGS10"
            title, desc = "3m10s Spread", "10-Year minus 3-Month Treasury Yield Spread (bps)"
        elif series_id == "SPREAD_5S30S":
            s1, s2 = "DGS5", "DGS30"
            title, desc = "5s30s Spread", "30-Year minus 5-Year Treasury Yield Spread (bps)"
        else:
            raise HTTPException(status_code=404, detail="Spread not found")

        # Helper function to fetch yield data with Yahoo Finance first, then FRED fallback
        def fetch_yield_data(series_id: str):
            history = None
            if series_id in treasury_yield_ticker_map:
                yahoo_ticker = treasury_yield_ticker_map[series_id]
                history = fetch_yfinance_series(yahoo_ticker, start_date)
            if not history or len(history) == 0:
                history = fetch_fred_series(series_id, start_date)
            return history
        
        h1 = fetch_yield_data(s1)
        h2 = fetch_yield_data(s2)
        
        spread_history = []
        if h1 and h2:
            d1 = {item['date']: item['value'] for item in h1}
            d2 = {item['date']: item['value'] for item in h2}
            common = sorted(set(d1.keys()) & set(d2.keys()))
            for date in common:
                spread_history.append({
                    "date": date,
                    "value": round(d2[date] - d1[date], 3)
                })
        
        latest = spread_history[-1] if spread_history else {"value": None, "date": None}
        
        return {
            "category": "Yield Curve Spreads",
            "title": title,
            "series_id": series_id,
            "current_value": latest.get("value"),
            "current_date": latest.get("date"),
            "description": desc,
            "history": spread_history,
            "chart_type": "line"
        }

    # Handle LIBOR-OIS Spread special case
    if series_id == "SPREAD_LIBOR_OIS":
        h1 = fetch_fred_series("USD3MTD156N", start_date)
        h2 = fetch_fred_series("SOFR", start_date) or fetch_fred_series("FEDFUNDS", start_date)
        
        spread_history = []
        if h1 and h2:
            d1 = {item['date']: item['value'] for item in h1}
            d2 = {item['date']: item['value'] for item in h2}
            common = sorted(set(d1.keys()) & set(d2.keys()))
            for date in common:
                val = (d1[date] - d2[date]) * 100
                spread_history.append({
                    "date": date,
                    "value": round(val, 2)
                })
        
        latest = spread_history[-1] if spread_history else {"value": None, "date": None}
        return {
            "category": "Funding Stress Metrics",
            "title": "LIBOR-OIS Spread",
            "series_id": "SPREAD_LIBOR_OIS",
            "current_value": latest.get("value"),
            "current_date": latest.get("date"),
            "description": "3-Month LIBOR minus OIS (SOFR/Fed Funds) Spread (bps)",
            "history": spread_history,
            "chart_type": "line"
        }

    # Handle raw FRED series
    # We don't have a global map of all series to titles here easily without duplicating lists.
    # But we can just fetch the data and return it with a generic title if we can't find it, 
    # OR we can iterate through all our lists to find the metadata.
    
    # Helper to find metadata
    def find_meta(sid):
        # Treasury
        ts = [
            {"title": "3-Month Treasury Yield", "series_id": "DGS3MO", "description": "3-Month Treasury Constant Maturity Rate (%)"},
            {"title": "2-Year Treasury Yield", "series_id": "DGS2", "description": "2-Year Treasury Constant Maturity Rate (%)"},
            {"title": "5-Year Treasury Yield", "series_id": "DGS5", "description": "5-Year Treasury Constant Maturity Rate (%)"},
            {"title": "10-Year Treasury Yield", "series_id": "DGS10", "description": "10-Year Treasury Constant Maturity Rate (%)"},
            {"title": "30-Year Treasury Yield", "series_id": "DGS30", "description": "30-Year Treasury Constant Maturity Rate (%)"},
        ]
        # TIPS
        tips = [
            {"title": "10-Year TIPS Yield", "series_id": "DFII10", "description": "10-Year Treasury Inflation-Indexed Security, Constant Maturity (%)"},
            {"title": "10-Year Breakeven Inflation Rate", "series_id": "T10YIE", "description": "10-Year Breakeven Inflation Rate (%)"},
            {"title": "5-Year Breakeven Inflation Rate", "series_id": "T5YIFR", "description": "5-Year Forward Inflation Expectation Rate (%)"},
        ]
        # Rates
        rates = [
            {"title": "Fed Funds Rate", "series_id": "FEDFUNDS", "description": "Effective Federal Funds Rate (%)"},
            {"title": "SOFR Rate", "series_id": "SOFR", "description": "Secured Overnight Financing Rate (%)"},
            {"title": "3-Month Commercial Paper Rate", "series_id": "CPN3M", "description": "3-Month Commercial Paper Rate (%)"},
        ]
        # Credit
        credit = [
            {"title": "Investment Grade Corporate Bond OAS", "series_id": "BAMLC0A0CM", "description": "ICE BofA US Corporate Index Option-Adjusted Spread (bps)"},
            {"title": "High Yield Corporate Bond OAS", "series_id": "BAMLH0A0HYM2", "description": "ICE BofA US High Yield Index Option-Adjusted Spread (bps)"},
        ]
        # Stress
        stress = [
            {"title": "3-Month LIBOR", "series_id": "USD3MTD156N", "description": "3-Month London Interbank Offered Rate (LIBOR) based on USD (%)"},
            {"title": "TED Spread", "series_id": "TEDRATE", "description": "TED Spread (3-Month LIBOR minus 3-Month Treasury Bill) (bps)"},
            {"title": "3-Month Treasury Bill Secondary Market Rate", "series_id": "TB3MS", "description": "3-Month Treasury Bill: Secondary Market Rate (%)"},
            {"title": "10-Year Treasury Constant Maturity Minus 2-Year", "series_id": "T10Y2Y", "description": "10-Year Treasury Constant Maturity Minus 2-Year Treasury Constant Maturity (bps) - Indicator of market stress"},
        ]
        
        all_meta = ts + tips + rates + credit + stress
        return next((item for item in all_meta if item["series_id"] == sid), None)

    # Handle MOVE index special case
    if series_id == "^MOVE":
         history = fetch_yfinance_series("^MOVE", start_date)
         latest = history[-1] if history else {"value": None, "date": None}
         return {
            "category": "Funding Stress Metrics",
            "title": "MOVE Index (Bond Volatility)",
            "series_id": "^MOVE",
            "current_value": latest.get("value"),
            "current_date": latest.get("date"),
            "description": "ICE BofA MOVE Index - Measures bond market volatility",
            "history": history,
            "chart_type": "line"
        }

    meta = find_meta(series_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Series not found")
    
    # Try Yahoo Finance first for Treasury yields, then fallback to FRED
    history = None
    if series_id in treasury_yield_ticker_map:
        yahoo_ticker = treasury_yield_ticker_map[series_id]
        history = fetch_yfinance_series(yahoo_ticker, start_date)
        if not history or len(history) == 0:
            history = fetch_fred_series(series_id, start_date)
    else:
        history = fetch_fred_series(series_id, start_date)
    
    latest = history[-1] if history else {"value": None, "date": None}
    
    return {
        "category": "Bond Data", # Generic category
        "title": meta["title"],
        "series_id": series_id,
        "current_value": latest.get("value"),
        "current_date": latest.get("date"),
        "description": meta["description"],
        "history": history,
        "chart_type": "line"
    }

@router.get("/tips-breakeven", response_model=List[BondData])
async def get_tips_breakeven(timeframe: str = "monthly"):
    """
    Fetch TIPS (Treasury Inflation-Protected Securities) and Breakeven Rates.
    Caches results for 1 hour.
    """
    cache_key = f"bond:tips:{timeframe}:v2"
    cached_data = redis_client.get_cache(cache_key)
    if cached_data:
        return cached_data
    start_offset = period_map.get(timeframe, "1y")
    start_date = calculate_start_date(start_offset)
    
    tips_series = [
        {"title": "10-Year TIPS Yield", "series_id": "DFII10", "description": "10-Year Treasury Inflation-Indexed Security, Constant Maturity (%)"},
        {"title": "10-Year Breakeven Inflation Rate", "series_id": "T10YIE", "description": "10-Year Breakeven Inflation Rate (%)"},
        {"title": "5-Year Breakeven Inflation Rate", "series_id": "T5YIFR", "description": "5-Year Forward Inflation Expectation Rate (%)"},
    ]
    
    results = []
    for series in tips_series:
        history = fetch_fred_series(series["series_id"], start_date)
        if history:
            latest = history[-1]
            results.append({
                "category": "TIPS & Breakeven Rates",
                "title": series["title"],
                "series_id": series["series_id"],
                "current_value": latest["value"],
                "current_date": latest["date"],
                "description": series["description"],
                "history": history,
                "chart_type": "line"
            })
    
    redis_client.set_cache(cache_key, results, ttl=3600)  # 1 hour cache
    return results

@router.get("/central-bank-rates", response_model=List[BondData])
async def get_central_bank_rates(timeframe: str = "monthly"):
    """
    Fetch Central Bank & Money Market Rates (Fed Funds, SOFR, etc.).
    Caches results for 1 hour.
    """
    cache_key = f"bond:rates:{timeframe}:v2"
    cached_data = redis_client.get_cache(cache_key)
    if cached_data:
        return cached_data
    start_offset = period_map.get(timeframe, "1y")
    start_date = calculate_start_date(start_offset)
    
    rates_series = [
        {"title": "Fed Funds Rate", "series_id": "FEDFUNDS", "description": "Effective Federal Funds Rate (%)"},
        {"title": "SOFR Rate", "series_id": "SOFR", "description": "Secured Overnight Financing Rate (%)"},
        {"title": "3-Month Commercial Paper Rate", "series_id": "CPN3M", "description": "3-Month Commercial Paper Rate (%)"},
    ]
    
    results = []
    for series in rates_series:
        history = fetch_fred_series(series["series_id"], start_date)
        if history:
            latest = history[-1]
            results.append({
                "category": "Central Bank & Money Market Rates",
                "title": series["title"],
                "series_id": series["series_id"],
                "current_value": latest["value"],
                "current_date": latest["date"],
                "description": series["description"],
                "history": history,
                "chart_type": "line"
            })
    
    redis_client.set_cache(cache_key, results, ttl=3600)  # 1 hour cache
    return results

@router.get("/credit-spreads", response_model=List[BondData])
async def get_credit_spreads(timeframe: str = "monthly"):
    """
    Fetch Corporate Bond Spreads (Investment Grade & High Yield).
    Caches results for 1 hour.
    """
    cache_key = f"bond:credit:{timeframe}:v2"
    cached_data = redis_client.get_cache(cache_key)
    if cached_data:
        return cached_data
    start_offset = period_map.get(timeframe, "1y")
    start_date = calculate_start_date(start_offset)
    
    spread_series = [
        {"title": "Investment Grade Corporate Bond OAS", "series_id": "BAMLC0A0CM", "description": "ICE BofA US Corporate Index Option-Adjusted Spread (bps)"},
        {"title": "High Yield Corporate Bond OAS", "series_id": "BAMLH0A0HYM2", "description": "ICE BofA US High Yield Index Option-Adjusted Spread (bps)"},
    ]
    
    results = []
    for series in spread_series:
        history = fetch_fred_series(series["series_id"], start_date)
        if history:
            latest = history[-1]
            results.append({
                "category": "Credit Market Data",
                "title": series["title"],
                "series_id": series["series_id"],
                "current_value": latest["value"],
                "current_date": latest["date"],
                "description": series["description"],
                "history": history,
                "chart_type": "line"
            })
    
    redis_client.set_cache(cache_key, results, ttl=3600)  # 1 hour cache
    return results

@router.get("/funding-stress", response_model=List[BondData])
async def get_funding_stress(timeframe: str = "monthly"):
    """
    Fetch Funding Stress Metrics including:
    - MOVE Index (Bond Volatility)
    - LIBOR-OIS spread
    - Treasury liquidity indicators
    - Inter-bank spreads
    Caches results for 1 hour.
    """
    cache_key = f"bond:stress:{timeframe}:v2"
    cached_data = redis_client.get_cache(cache_key)
    if cached_data:
        return cached_data
    start_offset = period_map.get(timeframe, "1y")
    start_date = calculate_start_date(start_offset)
    
    results = []
    
    # 1. MOVE Index (Bond Volatility) from Yahoo Finance
    try:
        move_history = fetch_yfinance_series("^MOVE", start_date)
        if move_history:
            latest = move_history[-1]
            results.append({
                "category": "Funding Stress Metrics",
                "title": "MOVE Index (Bond Volatility)",
                "series_id": "^MOVE",
                "current_value": latest["value"],
                "current_date": latest["date"],
                "description": "ICE BofA MOVE Index - Measures bond market volatility",
                "history": move_history,
                "chart_type": "line"
            })
    except Exception as e:
        print(f"Error fetching MOVE Index: {e}")
    
    # 2. FRED series for funding stress
    stress_series = [
        {"title": "3-Month LIBOR", "series_id": "USD3MTD156N", "description": "3-Month London Interbank Offered Rate (LIBOR) based on USD (%)"},
        {"title": "TED Spread", "series_id": "TEDRATE", "description": "TED Spread (3-Month LIBOR minus 3-Month Treasury Bill) (bps)"},
        {"title": "3-Month Treasury Bill Secondary Market Rate", "series_id": "TB3MS", "description": "3-Month Treasury Bill: Secondary Market Rate (%)"},
    ]
    
    for series in stress_series:
        try:
            history = fetch_fred_series(series["series_id"], start_date)
            if history:
                latest = history[-1]
                results.append({
                    "category": "Funding Stress Metrics",
                    "title": series["title"],
                    "series_id": series["series_id"],
                    "current_value": latest["value"],
                    "current_date": latest["date"],
                    "description": series["description"],
                    "history": history,
                    "chart_type": "line"
                })
        except Exception as e:
            print(f"Error fetching {series['series_id']}: {e}")
    
    # 3. Calculate LIBOR-OIS spread if we have both series
    try:
        libor_history = fetch_fred_series("USD3MTD156N", start_date)
        # Try to get OIS equivalent - using SOFR as proxy or Fed Funds
        ois_history = fetch_fred_series("SOFR", start_date) or fetch_fred_series("FEDFUNDS", start_date)
        
        if libor_history and ois_history:
            spread_history = []
            libor_dict = {item['date']: item['value'] for item in libor_history}
            ois_dict = {item['date']: item['value'] for item in ois_history}
            common_dates = sorted(set(libor_dict.keys()) & set(ois_dict.keys()))
            
            for date in common_dates:
                spread_value = (libor_dict[date] - ois_dict[date]) * 100  # Convert to bps
                spread_history.append({
                    "date": date,
                    "value": round(spread_value, 2)
                })
            
            if spread_history:
                latest = spread_history[-1]
                results.append({
                    "category": "Funding Stress Metrics",
                    "title": "LIBOR-OIS Spread",
                    "description": "3-Month LIBOR minus OIS (SOFR/Fed Funds) Spread (bps)",
                    "current_value": latest["value"],
                    "current_date": latest["date"],
                    "history": spread_history,
                    "chart_type": "line",
                    "series_id": "SPREAD_LIBOR_OIS"
                })
    except Exception as e:
        print(f"Error calculating LIBOR-OIS spread: {e}")
    
    # 4. Treasury liquidity indicators from FRED
    # Note: NY Fed liquidity index may not be directly available via FRED
    # Using related series that indicate market stress/liquidity
    liquidity_series = [
        {"title": "10-Year Treasury Constant Maturity Minus 2-Year", "series_id": "T10Y2Y", "description": "10-Year Treasury Constant Maturity Minus 2-Year Treasury Constant Maturity (bps) - Indicator of market stress"},
    ]
    
    for series in liquidity_series:
        history = fetch_fred_series(series["series_id"], start_date)
        if history:
            latest = history[-1]
            results.append({
                "category": "Funding Stress Metrics",
                "title": series["title"],
                "series_id": series["series_id"],
                "current_value": latest["value"],
                "current_date": latest["date"],
                "description": series["description"],
                "history": history,
                "chart_type": "line"
            })
    
    redis_client.set_cache(cache_key, results, ttl=3600)  # 1 hour cache
    return results

@router.get("/all", response_model=Dict[str, List[BondData]])
async def get_all_bond_data(timeframe: str = "monthly"):
    """
    Fetch all bond market data categories.
    """
    try:
        treasury_yields = await get_treasury_yields(timeframe)
        yield_curve = await get_yield_curve(timeframe)
        tips = await get_tips_breakeven(timeframe)
        central_bank = await get_central_bank_rates(timeframe)
        credit = await get_credit_spreads(timeframe)
        funding_stress = await get_funding_stress(timeframe)
        
        return {
            "treasury_yields": treasury_yields,
            "yield_curve": yield_curve,
            "tips_breakeven": tips,
            "central_bank_rates": central_bank,
            "credit_spreads": credit,
            "funding_stress": funding_stress
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching bond data: {str(e)}")

