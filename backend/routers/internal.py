from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import yfinance as yf
import pandas as pd
import datetime
import random
import os
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from pandas_datareader import data as web
from requests.exceptions import ReadTimeout, Timeout, RequestException

router = APIRouter()

# Mapping for timeframe to FRED offset
period_map = {
    "daily": "30d",
    "weekly": "3mo",
    "monthly": "1y",
    "quarterly": "1y",  # Use 1y for quarterly as FRED doesn't have quarterly-specific period
    "yearly": "5y",
    "5y": "5y",
    "max": "max"
}

# FRED indicator configurations
fred_indicators = [
    {
        "indicator": "Consumer Price Index (CPI)",
        "series_id": "CPIAUCSL",
        "description": "Consumer Price Index (YoY %)",
        "category": "Macro",
        "chart_type": "line"
    },
    {
        "indicator": "Unemployment Rate",
        "series_id": "UNRATE",
        "description": "Unemployment Rate (%)",
        "category": "Labor",
        "chart_type": "line"
    },
    {
        "indicator": "10Y Treasury Yield",
        "series_id": "DGS10",
        "description": "10-Year Treasury Yield (%)",
        "category": "Rates",
        "chart_type": "line"
    },
    {
        "indicator": "Consumer Spending (PCE)",
        "series_id": "PCE",
        "description": "Personal Consumption Expenditures ($B)",
        "category": "Macro",
        "chart_type": "line"
    },
    {
        "indicator": "Manufacturing Output",
        "series_id": "IPMAN",
        "description": "Industrial Production: Manufacturing (Index)",
        "category": "Business",
        "chart_type": "line"
    },
    {
        "indicator": "Bank Lending",
        "series_id": "TOTLL",
        "description": "Total Loans and Leases ($B)",
        "category": "Financial",
        "chart_type": "line"
    },
    {
        "indicator": "Financial Stress Index",
        "series_id": "STLFSI4",
        "description": "St. Louis Fed Financial Stress Index",
        "category": "Financial",
        "chart_type": "line"
    },

    {
        "indicator": "Housing Permits",
        "series_id": "PERMIT",
        "description": "New Privately-Owned Housing Units Authorized (Thousands)",
        "category": "Housing",
        "chart_type": "line"
    },
    {
        "indicator": "U.S. / Euro Foreign Exchange Rate",
        "series_id": "DEXUSEU",
        "description": "U.S. Dollars to One Euro",
        "category": "Currency",
        "chart_type": "line"
    },
    {
        "indicator": "Japanese Yen to U.S. Dollar Spot Exchange Rate",
        "series_id": "DEXJPUS",
        "description": "Japanese Yen to One U.S. Dollar",
        "category": "Currency",
        "chart_type": "line"
    },
    {
        "indicator": "China / U.S. Foreign Exchange Rate",
        "series_id": "DEXCHUS",
        "description": "Chinese Yuan to One U.S. Dollar",
        "category": "Currency",
        "chart_type": "line"
    },
    # Metals
    {
        "indicator": "Gold Fixing Price",
        "series_id": "GOLDAMGBD228NLBM",
        "description": "Gold Fixing Price (USD per Troy Ounce)",
        "category": "Commodity",
        "chart_type": "line"
    },
    {
        "indicator": "Platinum Price",
        "series_id": "PLATINUM",
        "description": "Platinum Price (USD per Troy Ounce)",
        "category": "Commodity",
        "chart_type": "line"
    },
    {
        "indicator": "Silver Price",
        "series_id": "SILVER",
        "description": "Silver Price (USD per Troy Ounce)",
        "category": "Commodity",
        "chart_type": "line"
    },
    {
        "indicator": "Copper Price",
        "series_id": "PCOPPUSDM",
        "description": "Copper Price (USD per Metric Ton)",
        "category": "Commodity",
        "chart_type": "line"
    },
    {
        "indicator": "Iron Ore Price",
        "series_id": "PIORECRUSDM",
        "description": "Iron Ore Price (USD per Metric Ton)",
        "category": "Commodity",
        "chart_type": "line"
    },
    {
        "indicator": "Silicon Price",
        "series_id": "PSILICON",
        "description": "Silicon Price (USD per Metric Ton)",
        "category": "Commodity",
        "chart_type": "line"
    },
    # Agricultural
    {
        "indicator": "Wheat Price",
        "series_id": "PWHEAMTUSDM",
        "description": "Wheat Price (USD per Metric Ton)",
        "category": "Commodity",
        "chart_type": "line"
    },
    {
        "indicator": "Corn Price",
        "series_id": "PCORNUSDM",
        "description": "Corn Price (USD per Metric Ton)",
        "category": "Commodity",
        "chart_type": "line"
    },
    {
        "indicator": "Soybeans Price",
        "series_id": "PSOYBUSDM",
        "description": "Soybeans Price (USD per Metric Ton)",
        "category": "Commodity",
        "chart_type": "line"
    },
    {
        "indicator": "Coffee Price",
        "series_id": "PCOFFUSDM",
        "description": "Coffee Price (USD per Metric Ton)",
        "category": "Commodity",
        "chart_type": "line"
    },
    {
        "indicator": "Sugar Price",
        "series_id": "PSUGAR",
        "description": "Sugar Price (USD per pound)",
        "category": "Commodity",
        "chart_type": "line"
    },
    # Industrial
    {
        "indicator": "Natural Gas Price Index",
        "series_id": "PNRGINDEXM",
        "description": "Natural Gas Price Index",
        "category": "Commodity",
        "chart_type": "line"
    },
    {
        "indicator": "Crude Oil Price",
        "series_id": "POILBREUSDM",
        "description": "Crude Oil Price (USD per Barrel)",
        "category": "Commodity",
        "chart_type": "line"
    },
    {
        "indicator": "Aluminum Price",
        "series_id": "PALUMINUM",
        "description": "Aluminum Price (USD per Metric Ton)",
        "category": "Commodity",
        "chart_type": "line"
    },
    {
        "indicator": "Zinc Price",
        "series_id": "PZINC",
        "description": "Zinc Price (USD per Metric Ton)",
        "category": "Commodity",
        "chart_type": "line"
    }
]

def fetch_fred_series(series_id: str, start_date: str, max_retries: int = 2, timeout: int = 15):
    """Fetch a series from FRED and return list of {'date': str, 'value': float} sorted oldest to newest.
    
    Args:
        series_id: FRED series ID
        start_date: Start date in YYYY-MM-DD format
        max_retries: Maximum number of retry attempts (default: 2)
        timeout: Request timeout in seconds (default: 15, reduced from default 30)
    """
    fred_api_key = os.getenv('FRED_API_KEY')
    if not fred_api_key:
        print(f"Warning: FRED_API_KEY not set. Cannot fetch {series_id}")
        return []
    
    # Retry logic with exponential backoff
    for attempt in range(max_retries + 1):
        try:
            # Use a shorter timeout to fail faster and retry
            # Note: pandas_datareader doesn't directly support timeout, but we can catch timeout exceptions
            df = web.DataReader(series_id, 'fred', start=start_date, api_key=fred_api_key)
            
            if df.empty:
                print(f"Warning: FRED returned empty data for {series_id}")
                return []
            
            df = df.dropna()
            if df.empty:
                print(f"Warning: FRED data for {series_id} is all NaN after dropna")
                return []
            
            # Reset index to convert DatetimeIndex to a column
            df = df.reset_index()
            
            # Handle column names - FRED returns data with the series_id as column name
            # After reset_index, we have 'DATE' (or 'date') and the series_id column
            if len(df.columns) == 2:
                # Standard case: DATE column and value column
                date_col = df.columns[0]
                value_col = df.columns[1]
            elif len(df.columns) == 1:
                # Only value column, date is in index (shouldn't happen after reset_index, but handle it)
                print(f"Warning: Unexpected DataFrame structure for {series_id}: {df.columns}")
                return []
            else:
                # Multiple columns - use first as date, second as value
                date_col = df.columns[0]
                value_col = df.columns[1]
            
            # Rename columns for consistency
            df = df.rename(columns={date_col: 'date', value_col: 'value'})
            
            # Ensure date is datetime and format it
            if not pd.api.types.is_datetime64_any_dtype(df['date']):
                df['date'] = pd.to_datetime(df['date'])
            df['date'] = df['date'].dt.strftime('%Y-%m-%d')
            
            # Ensure value is float
            df['value'] = df['value'].astype(float)
            
            return df.to_dict(orient='records')
            
        except (ReadTimeout, Timeout) as e:
            if attempt < max_retries:
                wait_time = (2 ** attempt) * 1  # Exponential backoff: 1s, 2s, 4s
                print(f"Timeout fetching FRED series {series_id} (attempt {attempt + 1}/{max_retries + 1}). Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                print(f"Error: FRED series {series_id} timed out after {max_retries + 1} attempts")
                return []
        except RequestException as e:
            if attempt < max_retries:
                wait_time = (2 ** attempt) * 1
                print(f"Request error fetching FRED series {series_id} (attempt {attempt + 1}/{max_retries + 1}): {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                print(f"Error: FRED series {series_id} failed after {max_retries + 1} attempts: {e}")
                return []
        except Exception as e:
            # For other exceptions, don't retry - just log and return empty
            print(f"Error fetching FRED series {series_id}: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    return []

# Mapping of commodity series IDs to Yahoo Finance ticker symbols
commodity_ticker_map = {
    "GOLDAMGBD228NLBM": "GC=F",  # Gold Futures
    "PLATINUM": "PL=F",  # Platinum Futures
    "SILVER": "SI=F",  # Silver Futures
    "PCOPPUSDM": "HG=F",  # Copper Futures
    "PIORECRUSDM": "IO=F",  # Iron Ore Futures (or use VALE, BHP as proxy)
    "PSILICON": "SI=F",  # Silicon - using Silver as proxy (may need adjustment)
    "PTITANIUM": "TI=F",  # Titanium - may need alternative source
    "PWHEAMTUSDM": "ZW=F",  # Wheat Futures
    "PCORNUSDM": "ZC=F",  # Corn Futures
    "PSOYBUSDM": "ZS=F",  # Soybeans Futures
    "PCOFFUSDM": "KC=F",  # Coffee Futures
    "PLUMBER": "LB=F",  # Lumber Futures
    "PMILK": "DA=F",  # Class III Milk Futures
    "PSUGAR": "SB=F",  # Sugar #11 Futures
    "PNRGINDEXM": "NG=F",  # Natural Gas Futures
    "POILBREUSDM": "CL=F",  # Crude Oil Futures
    "PALUMINUM": "ALI=F",  # Aluminum Futures
    "PNICKEL": "NI=F",  # Nickel Futures
    "PZINC": "ZN=F",  # Zinc Futures
}

def fetch_commodity_from_yahoo(series_id: str, timeframe: str):
    """Fetch commodity data from Yahoo Finance and return list of {'date': str, 'value': float}."""
    try:
        ticker_symbol = commodity_ticker_map.get(series_id)
        if not ticker_symbol:
            print(f"No Yahoo Finance ticker mapping found for {series_id}")
            return []
        
        # Map timeframe to yfinance period
        period_map_yahoo = {
            "monthly": "1y",
            "quarterly": "1y",
            "yearly": "5y",
            "5y": "5y",
            "max": "max"
        }
        period = period_map_yahoo.get(timeframe, "1y")
        
        # Map timeframe to interval
        interval_map = {
            "monthly": "1d",
            "quarterly": "1d",
            "yearly": "1wk",
            "5y": "1mo",
            "max": "1mo"
        }
        interval = interval_map.get(timeframe, "1d")
        
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:
            print(f"No data found for {ticker_symbol}")
            return []
        
        # Convert to list of {date, value} objects
        history = []
        for date, row in hist.iterrows():
            history.append({
                "date": date.strftime("%Y-%m-%d"),
                "value": float(row['Close'])
            })
        
        return history
    except Exception as e:
        print(f"Error fetching commodity {series_id} from Yahoo Finance: {e}")
        import traceback
        traceback.print_exc()
        return []
class HistoricalData(BaseModel):
    date: str
    value: float

class MacroData(BaseModel):
    indicator: str
    value: Optional[float] = None
    date: Optional[str] = None
    description: str
    category: str
    series_id: Optional[str] = None
    history: Optional[List[Dict[str, Any]]] = None
    chart_type: str = "line" # line, bar

class MicroData(BaseModel):
    ticker: str
    company_name: Optional[str] = None
    price: float
    volume: int
    market_cap: Optional[int] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    # New Fields
    financials: Optional[Dict[str, Any]] = None
    balance_sheet: Optional[Dict[str, Any]] = None
    cashflow: Optional[Dict[str, Any]] = None
    ratios: Optional[Dict[str, Any]] = None
    holders: Optional[Dict[str, Any]] = None
    trading: Optional[Dict[str, Any]] = None
    filings: Optional[List[Dict[str, Any]]] = None

@router.get("/macro", response_model=List[MacroData])
async def get_macro_data(timeframe: str = "monthly"):
    """
    Fetch macro economic data.
    Includes 8 key indicators with historical data (Mocked for now).
    Timeframe options: daily, weekly, monthly, yearly
    """
    try:
        start_offset = period_map.get(timeframe, "1y")
        # Convert offset to a date string (approximate)
        from datetime import datetime, timedelta
        
        if start_offset == "max":
            start_date = "1900-01-01" # Fetch all available history
        elif start_offset.endswith('d'):
            days = int(start_offset.rstrip('d'))
            start_date = (datetime.today() - timedelta(days=days)).strftime('%Y-%m-%d')
        elif start_offset.endswith('mo'):
            months = int(start_offset.rstrip('mo'))
            start_date = (datetime.today() - timedelta(days=months*30)).strftime('%Y-%m-%d')
        elif start_offset.endswith('y'):
            years = int(start_offset.rstrip('y'))
            start_date = (datetime.today() - timedelta(days=years*365)).strftime('%Y-%m-%d')
        else:
            start_date = (datetime.today() - timedelta(days=365)).strftime('%Y-%m-%d')

        # Filter to only Economic indicators (exclude Currency and Commodity)
        # Only include: Consumer Price Index (CPI), Unemployment Rate, Consumer Spending (PCE),
        # Manufacturing Output, Bank Lending, Housing Permits
        allowed_economic_series = ['CPIAUCSL', 'UNRATE', 'PCE', 'IPMAN', 'TOTLL', 'PERMIT']
        economic_indicators = [
            cfg for cfg in fred_indicators 
            if cfg["series_id"] in allowed_economic_series
        ]
        
        # Build results list using real data - fetch in parallel with timeout protection
        results = []
        
        def fetch_single_indicator(cfg):
            """Fetch a single indicator with error handling"""
            try:
                history = fetch_fred_series(cfg["series_id"], start_date)
                
                # Always append the indicator, even if history is empty (frontend handles empty history)
                if history and len(history) > 0:
                    latest_val = float(history[-1]["value"])
                    latest_date = str(history[-1]["date"])
                else:
                    latest_val = 0.0
                    latest_date = datetime.today().strftime('%Y-%m-%d')
                
                return {
                    "indicator": cfg["indicator"],
                    "value": latest_val,
                    "date": latest_date,
                    "description": cfg["description"],
                    "category": cfg["category"],
                    "history": history if history else [], # Can be empty list
                    "chart_type": cfg["chart_type"],
                    "series_id": cfg["series_id"] # Ensure series_id is passed to frontend
                }
            except Exception as e:
                print(f"Error fetching {cfg['series_id']}: {e}")
                import traceback
                traceback.print_exc()
                # Add indicator with default data if fetch fails
                return {
                    "indicator": cfg["indicator"],
                    "value": 0.0,
                    "date": datetime.today().strftime('%Y-%m-%d'),
                    "description": cfg["description"],
                    "category": cfg["category"],
                    "history": [],
                    "chart_type": cfg["chart_type"],
                    "series_id": cfg["series_id"]
                }
        
        # Fetch all indicators in parallel with individual timeouts (20 seconds each)
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(fetch_single_indicator, cfg): cfg for cfg in economic_indicators}
            for future in futures:
                try:
                    result = future.result(timeout=20)  # 20 second timeout per indicator
                    results.append(result)
                except FutureTimeoutError:
                    cfg = futures[future]
                    print(f"Timeout: {cfg['series_id']} exceeded 20 second timeout")
                    results.append({
                        "indicator": cfg["indicator"],
                        "value": 0.0,
                        "date": datetime.today().strftime('%Y-%m-%d'),
                        "description": cfg["description"],
                        "category": cfg["category"],
                        "history": [],
                        "chart_type": cfg["chart_type"],
                        "series_id": cfg["series_id"]
                    })
                except Exception as e:
                    cfg = futures[future]
                    print(f"Unexpected error for {cfg['series_id']}: {e}")
                    results.append({
                        "indicator": cfg["indicator"],
                        "value": 0.0,
                        "date": datetime.today().strftime('%Y-%m-%d'),
                        "description": cfg["description"],
                        "category": cfg["category"],
                        "history": [],
                        "chart_type": cfg["chart_type"],
                        "series_id": cfg["series_id"]
                    })

        # Add FedWatch Tool as it's not from FRED and has a different history format
        today = datetime.today().date()
        
        # Calculate next FOMC meeting date
        def get_next_fomc_meeting_date():
            """Calculate the next FOMC meeting date based on typical schedule"""
            from datetime import date
            today = date.today()
            
            # FOMC meetings typically occur 8 times per year
            # Common months: Jan/Feb, Mar, May, Jun, Jul, Sep, Nov, Dec
            # For 2025, known dates include: Dec 9-10, 2025
            # This is a simplified calculation - in production, you'd want to fetch from FOMC calendar
            
            # Known upcoming FOMC meeting dates (2025-2026)
            fomc_dates = [
                date(2025, 12, 9),   # December 9-10, 2025
                date(2026, 1, 28),   # January 28-29, 2026 (typical)
                date(2026, 3, 18),   # March 18-19, 2026 (typical)
                date(2026, 5, 6),    # May 6-7, 2026 (typical)
                date(2026, 6, 17),   # June 17-18, 2026 (typical)
                date(2026, 7, 29),   # July 29-30, 2026 (typical)
                date(2026, 9, 16),   # September 16-17, 2026 (typical)
                date(2026, 11, 6),   # November 6-7, 2026 (typical)
                date(2026, 12, 15),  # December 15-16, 2026 (typical)
            ]
            
            # Find next meeting date
            for meeting_date in fomc_dates:
                if meeting_date >= today:
                    return meeting_date.strftime('%B %d, %Y')
            
            # Fallback if no future date found
            return "TBD"
        
        next_meeting_date = get_next_fomc_meeting_date()
        
        results.append({
            "indicator": "FedWatch Tool",
            "value": 5.25, # Current Fed Funds Rate (Upper)
            "date": str(today),
            "description": f"Target Rate Probabilities (next meeting date: {next_meeting_date})",
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
        
        return results
    except Exception as e:
        print(f"Error in get_macro_data: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching macro data: {str(e)}")

@router.get("/macro/series/{series_id}", response_model=MacroData)
async def get_macro_series(series_id: str, timeframe: str = "monthly"):
    """
    Fetch a single macro economic data series.
    """
    start_offset = period_map.get(timeframe, "1y")
    from datetime import datetime, timedelta
    
    # Calculate start date (duplicate logic, could be refactored)
    if start_offset == "max":
        # For max, use a very old date to get all available data (FRED typically goes back to 1970s)
        start_date = "1970-01-01"
    elif start_offset.endswith('d'):
        days = int(start_offset.rstrip('d'))
        start_date = (datetime.today() - timedelta(days=days)).strftime('%Y-%m-%d')
    elif start_offset.endswith('mo'):
        months = int(start_offset.rstrip('mo'))
        start_date = (datetime.today() - timedelta(days=months*30)).strftime('%Y-%m-%d')
    elif start_offset.endswith('y'):
        years = int(start_offset.rstrip('y'))
        start_date = (datetime.today() - timedelta(days=years*365)).strftime('%Y-%m-%d')
    else:
        start_date = (datetime.today() - timedelta(days=365)).strftime('%Y-%m-%d')

    # Handle FedWatch special case
    if series_id == "FEDWATCH":
        today = datetime.today().date()
        
        # Calculate next FOMC meeting date
        def get_next_fomc_meeting_date():
            """Calculate the next FOMC meeting date based on typical schedule"""
            from datetime import date
            today = date.today()
            
            # Known upcoming FOMC meeting dates (2025-2026)
            fomc_dates = [
                date(2025, 12, 9),   # December 9-10, 2025
                date(2026, 1, 28),   # January 28-29, 2026 (typical)
                date(2026, 3, 18),   # March 18-19, 2026 (typical)
                date(2026, 5, 6),    # May 6-7, 2026 (typical)
                date(2026, 6, 17),   # June 17-18, 2026 (typical)
                date(2026, 7, 29),   # July 29-30, 2026 (typical)
                date(2026, 9, 16),   # September 16-17, 2026 (typical)
                date(2026, 11, 6),   # November 6-7, 2026 (typical)
                date(2026, 12, 15),  # December 15-16, 2026 (typical)
            ]
            
            # Find next meeting date
            for meeting_date in fomc_dates:
                if meeting_date >= today:
                    return meeting_date.strftime('%B %d, %Y')
            
            # Fallback if no future date found
            return "TBD"
        
        next_meeting_date = get_next_fomc_meeting_date()
        
        return {
            "indicator": "FedWatch Tool",
            "value": 5.25,
            "date": str(today),
            "description": f"Target Rate Probabilities (next meeting date: {next_meeting_date})",
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

    # Find config
    cfg = next((item for item in fred_indicators if item["series_id"] == series_id), None)
    if not cfg:
        raise HTTPException(status_code=404, detail="Series not found")

    # Check if this is a commodity and use Yahoo Finance
    if cfg["category"] == "Commodity" and series_id in commodity_ticker_map:
        history = fetch_commodity_from_yahoo(series_id, timeframe)
        # If Yahoo Finance fails, try FRED as fallback
        if not history or len(history) == 0:
            print(f"Yahoo Finance failed for {series_id}, trying FRED as fallback")
            history = fetch_fred_series(series_id, start_date)
    else:
        history = fetch_fred_series(series_id, start_date)
    
    # Ensure we have valid values even if history is empty
    if history and len(history) > 0:
        latest_val = float(history[-1]["value"])
        latest_date = str(history[-1]["date"])
    else:
        # Return default values if no data available
        latest_val = 0.0
        latest_date = datetime.today().strftime('%Y-%m-%d')

    return {
        "indicator": cfg["indicator"],
        "value": latest_val,
        "date": latest_date,
        "description": cfg["description"],
        "category": cfg["category"],
        "history": history if history else [],
        "chart_type": cfg["chart_type"],
        "series_id": cfg["series_id"]
    }

@router.get("/stock/{ticker}/history")
async def get_stock_history(ticker: str, period: str = "2y"):
    """
    Fetch historical stock price data from Yahoo Finance.
    Period options: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    """
    try:
        stock = yf.Ticker(ticker)
        
        # Map period to interval
        interval_map = {
            "1d": "1m",
            "5d": "5m",
            "1mo": "1d",
            "3mo": "1d",
            "6mo": "1d",
            "1y": "1d",
            "2y": "1d",
            "5y": "1wk",
            "10y": "1mo",
            "ytd": "1d",
            "max": "1mo"
        }
        
        interval = interval_map.get(period, "1d")
        
        hist = stock.history(period=period, interval=interval)
        
        if hist.empty:
            raise HTTPException(status_code=404, detail="No data found for ticker")
        
        # Convert to list of {date, price} objects
        history = []
        for date, row in hist.iterrows():
            history.append({
                "date": date.strftime("%Y-%m-%d"),
                "price": float(row['Close'])
            })
        
        # Get current price info
        info = stock.info
        current_price = float(hist['Close'].iloc[-1])
        
        # Calculate price change from first date in history
        first_price = float(hist['Close'].iloc[0])
        price_change = current_price - first_price
        price_change_percent = (price_change / first_price) * 100 if first_price > 0 else 0
        
        # Calculate today's percentage change (current vs previous close)
        today_change_percent = 0
        if len(hist) >= 2:
            previous_close = float(hist['Close'].iloc[-2])
            today_change = current_price - previous_close
            today_change_percent = (today_change / previous_close) * 100 if previous_close > 0 else 0
        elif 'regularMarketChangePercent' in info:
            # Use yfinance info if available
            today_change_percent = info.get('regularMarketChangePercent', 0)
        
        return {
            "ticker": ticker,
            "company_name": info.get("longName", ticker),
            "history": history,
            "current_price": current_price,
            "price_change": price_change,
            "price_change_percent": price_change_percent,
            "today_change_percent": round(today_change_percent, 2),
            "reference_date": hist.index[0].strftime("%b %Y")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stock data: {str(e)}")

@router.get("/micro/{ticker}", response_model=MicroData)
async def get_micro_data(ticker: str):
    """
    Fetch comprehensive micro economic data (company specific) using yfinance.
    Includes Financials (Annual + LTM), Ratios, Holders, and Trading data.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        history = stock.history(period="1d")
        
        if history.empty:
             raise HTTPException(status_code=404, detail="Ticker not found")

        current_price = history['Close'].iloc[-1]
        volume = history['Volume'].iloc[-1]
        
        # Helper to safely get dataframe as dict
        def df_to_dict(df):
            if df is None or df.empty:
                return {}
            # yfinance returns: rows=metrics, columns=dates
            # We need: {metric_name: {date: value, date: value}}
            result = {}
            for metric in df.index:
                result[metric] = {}
                for date_col in df.columns:
                    # Convert timestamp to string
                    date_str = str(date_col)
                    value = df.loc[metric, date_col]
                    # Handle NaN values and convert numpy types to Python types
                    if pd.isna(value):
                        result[metric][date_str] = None
                    else:
                        # Convert numpy types to Python native types for JSON serialization
                        if hasattr(value, 'item'):  # numpy scalar
                            result[metric][date_str] = value.item()
                        elif isinstance(value, (int, float)):
                            result[metric][date_str] = float(value)
                        else:
                            result[metric][date_str] = value
            return result
        
        # Helper to calculate LTM from quarterly data
        def calculate_ltm(quarterly_df):
            if quarterly_df is None:
                return {}
            # Check if it's a DataFrame
            if not hasattr(quarterly_df, 'empty'):
                return {}
            if quarterly_df.empty or len(quarterly_df.columns) < 4:
                return {}
            # Sum last 4 quarters for each line item
            ltm = {}
            for index in quarterly_df.index:
                try:
                    ltm[index] = quarterly_df.loc[index].iloc[:4].sum()
                except:
                    ltm[index] = None
            return ltm

        # Fetch Annual Financials
        financials_annual = df_to_dict(stock.financials)
        balance_sheet_annual = df_to_dict(stock.balance_sheet)
        cashflow_annual = df_to_dict(stock.cashflow)
        
        # Fetch Quarterly Financials for LTM and quarterly view
        financials_quarterly = stock.quarterly_financials
        balance_sheet_quarterly = stock.quarterly_balance_sheet
        cashflow_quarterly = stock.quarterly_cashflow
        
        # Convert quarterly dataframes to dict
        financials_quarterly_dict = df_to_dict(financials_quarterly)
        balance_sheet_quarterly_dict = df_to_dict(balance_sheet_quarterly)
        cashflow_quarterly_dict = df_to_dict(cashflow_quarterly)
        
        # Calculate LTM
        financials_ltm = calculate_ltm(financials_quarterly)
        balance_sheet_ltm = calculate_ltm(balance_sheet_quarterly)
        cashflow_ltm = calculate_ltm(cashflow_quarterly)
        
        # Combine annual + quarterly + LTM
        financials = {
            "annual": financials_annual,
            "quarterly": financials_quarterly_dict,
            "ltm": financials_ltm
        }
        balance_sheet = {
            "annual": balance_sheet_annual,
            "quarterly": balance_sheet_quarterly_dict,
            "ltm": balance_sheet_ltm
        }
        cashflow = {
            "annual": cashflow_annual,
            "quarterly": cashflow_quarterly_dict,
            "ltm": cashflow_ltm
        }
        
        # Calculate Comprehensive Ratios
        market_cap = info.get("marketCap", 0)
        
        # Get key values for calculations
        try:
            # From financials
            total_revenue = financials_ltm.get("Total Revenue", 0) or 0
            gross_profit = financials_ltm.get("Gross Profit", 0) or 0
            operating_income = financials_ltm.get("Operating Income", 0) or 0
            ebitda = financials_ltm.get("EBITDA", 0) or info.get("ebitda", 0) or 0
            net_income = financials_ltm.get("Net Income", 0) or 0
            interest_expense = abs(financials_ltm.get("Interest Expense", 0) or 0)
            
            # From balance sheet (use most recent quarter)
            total_assets = info.get("totalAssets", 0) or 0
            total_equity = info.get("totalStockholderEquity", 0) or 0
            total_debt = info.get("totalDebt", 0) or 0
            current_assets = balance_sheet_ltm.get("Current Assets", 0) or 0
            current_liabilities = balance_sheet_ltm.get("Current Liabilities", 0) or 0
            inventory = balance_sheet_ltm.get("Inventory", 0) or 0
            accounts_receivable = balance_sheet_ltm.get("Accounts Receivable", 0) or 0
            accounts_payable = balance_sheet_ltm.get("Accounts Payable", 0) or 0
            
            # From cash flow
            operating_cf = cashflow_ltm.get("Operating Cash Flow", 0) or 0
            capex = abs(cashflow_ltm.get("Capital Expenditure", 0) or 0)
            free_cash_flow = operating_cf - capex
            
            # Calculate COGS
            cogs = total_revenue - gross_profit if total_revenue and gross_profit else 0
            
        except Exception as e:
            print(f"Error extracting financial values: {e}")
            total_revenue = ebitda = net_income = total_assets = total_equity = 0
            free_cash_flow = operating_cf = capex = 0
            cogs = inventory = accounts_receivable = accounts_payable = 0
            interest_expense = total_debt = 0
        
        # Profitability Ratios
        profitability = {
            "grossMargins": info.get("grossMargins"),
            "operatingMargins": info.get("operatingMargins"),
            "ebitdaMargins": info.get("ebitdaMargins"),
            "netMargin": (net_income / total_revenue * 100) if total_revenue else None,
            "returnOnAssets": (net_income / total_assets * 100) if total_assets else info.get("returnOnAssets"),
            "returnOnEquity": (net_income / total_equity * 100) if total_equity else info.get("returnOnEquity"),
            "returnOnInvestedCapital": (operating_income / (total_debt + total_equity) * 100) if (total_debt + total_equity) else None,
            "fcfYield": (free_cash_flow / market_cap * 100) if market_cap else None
        }
        
        # Liquidity & Solvency
        liquidity = {
            "currentRatio": info.get("currentRatio"),
            "quickRatio": info.get("quickRatio"),
            "debtToEquity": info.get("debtToEquity"),
            "debtToEbitda": (total_debt / ebitda) if ebitda else None,
            "interestCoverage": (ebitda / interest_expense) if interest_expense else None
        }
        
        # Efficiency Ratios
        efficiency = {
            "inventoryTurnover": (cogs / inventory) if inventory else None,
            "daysSalesOutstanding": (accounts_receivable / total_revenue * 365) if total_revenue else None,
            "daysPayableOutstanding": (accounts_payable / cogs * 365) if cogs else None,
            "assetTurnover": (total_revenue / total_assets) if total_assets else None,
            "workingCapital": current_assets - current_liabilities
        }
        
        # Valuation
        valuation = {
            "trailingPE": info.get("trailingPE"),
            "forwardPE": info.get("forwardPE"),
            "priceToBook": info.get("priceToBook"),
            "enterpriseToEbitda": info.get("enterpriseToEbitda"),
            "priceToSales": info.get("priceToSalesTrailing12Months"),
            "evToRevenue": info.get("enterpriseToRevenue")
        }
        
        ratios = {
            "profitability": profitability,
            "liquidity": liquidity,
            "efficiency": efficiency,
            "valuation": valuation
        }
        
        # Holders (Institutional & Insider)
        holders = {
            "major": df_to_dict(stock.major_holders),
            "institutional": df_to_dict(stock.institutional_holders),
            "insider": df_to_dict(stock.insider_transactions)
        }
        
        # Trading Data
        trading = {
            "shortRatio": info.get("shortRatio"),
            "shortPercentOfFloat": info.get("shortPercentOfFloat"),
            "sharesShort": info.get("sharesShort"),
            "averageVolume": info.get("averageVolume"),
            "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
            "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
            "beta": info.get("beta"),
            "impliedSharesOutstanding": info.get("impliedSharesOutstanding"),
            "options": [],
            "availableOptionsDates": []
        }

        # Try to fetch options data for all available expiry dates
        try:
            options_dates = stock.options
            if options_dates:
                trading["availableOptionsDates"] = list(options_dates)
                
                # Fetch data for all expiry dates (limit to first 20 to avoid timeout)
                options_list = []
                for date in options_dates[:20]:  # Limit to first 20 dates
                    try:
                        chain = stock.option_chain(date)
                        
                        # Calculate totals for this expiration
                        calls_vol = chain.calls['volume'].sum() if not chain.calls.empty else 0
                        puts_vol = chain.puts['volume'].sum() if not chain.puts.empty else 0
                        calls_oi = chain.calls['openInterest'].sum() if not chain.calls.empty else 0
                        puts_oi = chain.puts['openInterest'].sum() if not chain.puts.empty else 0
                        
                        options_list.append({
                            "expirationDate": date,
                            "callsVolume": int(calls_vol),
                            "putsVolume": int(puts_vol),
                            "callsOpenInterest": int(calls_oi),
                            "putsOpenInterest": int(puts_oi),
                            "totalVolume": int(calls_vol + puts_vol),
                            "totalOpenInterest": int(calls_oi + puts_oi)
                        })
                    except Exception as e:
                        print(f"Error fetching chain for {date}: {e}")
                        continue
                
                trading["options"] = options_list
        except Exception as e:
            print(f"Error fetching options data: {e}")

        
        # SEC Filings - Use SEC EDGAR API directly
        filings = []
        try:
            import requests
            # Get CIK from ticker - try multiple methods
            cik = info.get("cik") or info.get("companyOfficers", [{}])[0].get("cik") if info.get("companyOfficers") else None
            
            # If no CIK in info, try to look it up by ticker
            if not cik:
                # Try SEC company tickers JSON
                try:
                    tickers_url = "https://www.sec.gov/files/company_tickers.json"
                    headers = {'User-Agent': 'Financial Dashboard contact@example.com'}
                    resp = requests.get(tickers_url, headers=headers, timeout=10)
                    if resp.status_code == 200:
                        tickers_data = resp.json()
                        # Search for ticker
                        for entry in tickers_data.values():
                            if entry.get("ticker") == ticker.upper():
                                cik = entry.get("cik_str")
                                break
                except:
                    pass
            
            if cik:
                # Pad CIK to 10 digits
                cik_padded = str(cik).zfill(10)
                
                # Fetch filings from SEC EDGAR API
                headers = {'User-Agent': 'Financial Dashboard contact@example.com'}
                url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    sec_data = response.json()
                    recent_filings = sec_data.get("filings", {}).get("recent", {})
                    
                    if recent_filings:
                        # Get arrays of filing data
                        forms = recent_filings.get("form", [])
                        dates = recent_filings.get("filingDate", [])
                        accession_numbers = recent_filings.get("accessionNumber", [])
                        primary_documents = recent_filings.get("primaryDocument", [])
                        
                        # Build filings list (limit to 50 most recent)
                        for i in range(min(50, len(forms))):
                            accession = accession_numbers[i].replace("-", "")
                            primary_doc = primary_documents[i] if i < len(primary_documents) else ""
                            
                            # Direct link to the filing document
                            if primary_doc:
                                filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{primary_doc}"
                            else:
                                # Fallback to filing detail page
                                filing_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik_padded}&type={forms[i]}&dateb=&owner=exclude&count=100"
                            
                            filings.append({
                                "type": forms[i],
                                "date": dates[i],
                                "link": filing_url
                            })
                else:
                    print(f"SEC API returned status {response.status_code} for CIK {cik_padded}")
            else:
                print(f"No CIK found for ticker {ticker}")
        except Exception as e:
            print(f"Error fetching SEC filings: {e}")
            import traceback
            traceback.print_exc()
            # If filings fail, just return empty list

        return {
            "ticker": ticker.upper(),
            "company_name": info.get("longName"),
            "price": round(current_price, 2),
            "volume": int(volume),
            "market_cap": info.get("marketCap"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "financials": financials,
            "balance_sheet": balance_sheet,
            "cashflow": cashflow,
            "ratios": ratios,
            "holders": holders,
            "trading": trading,
            "filings": filings
        }
    except Exception as e:
        print(f"Error fetching micro data for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class OptionsRequest(BaseModel):
    ticker: str
    expirationDates: List[str]

@router.post("/micro/options")
async def get_options_aggregation(request: OptionsRequest):
    """
    Fetch aggregated options data for specified expiration dates.
    """
    try:
        stock = yf.Ticker(request.ticker)
        
        total_calls_vol = 0
        total_puts_vol = 0
        total_calls_oi = 0
        total_puts_oi = 0
        
        for date in request.expirationDates:
            try:
                chain = stock.option_chain(date)
                if not chain.calls.empty:
                    total_calls_vol += chain.calls['volume'].sum()
                    total_calls_oi += chain.calls['openInterest'].sum()
                if not chain.puts.empty:
                    total_puts_vol += chain.puts['volume'].sum()
                    total_puts_oi += chain.puts['openInterest'].sum()
            except Exception as e:
                print(f"Error fetching chain for {date}: {e}")
                continue
        
        return {
            "totalVolume": int(total_calls_vol + total_puts_vol),
            "totalOpenInterest": int(total_calls_oi + total_puts_oi),
            "callsVolume": int(total_calls_vol),
            "putsVolume": int(total_puts_vol),
            "callsOpenInterest": int(total_calls_oi),
            "putsOpenInterest": int(total_puts_oi),
            "selectedDates": request.expirationDates
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class MarketMover(BaseModel):
    ticker: str
    price: float
    change: float
    change_percent: float
    volume: str

class MarketMoversResponse(BaseModel):
    gainers: List[MarketMover]
    losers: List[MarketMover]
    volatile: List[MarketMover]
    active: List[MarketMover]

@router.get("/indices")
async def get_indices():
    """
    Fetch real-time data for major market indices: Dow Jones, NASDAQ, S&P 500, Russell 2000.
    Returns current value, change percentage, and 30-day history for each index.
    """
    indices_config = [
        {"name": "Dow Jones", "ticker": "^DJI"},
        {"name": "NASDAQ", "ticker": "^IXIC"},
        {"name": "S&P 500", "ticker": "^GSPC"},
        {"name": "Russell 2000", "ticker": "^RUT"}
    ]
    
    results = []
    try:
        for idx in indices_config:
            try:
                ticker = yf.Ticker(idx["ticker"])
                # Get last 30 days of data
                history = ticker.history(period="1mo")
                
                if history.empty:
                    # Fallback to default values if data unavailable
                    results.append({
                        "name": idx["name"],
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
                    "value": round(current_price, 2),
                    "change": round(change_percent, 2),
                    "history": history_list
                })
            except Exception as e:
                print(f"Error fetching {idx['name']}: {e}")
                # Fallback to default values
                results.append({
                    "name": idx["name"],
                    "value": 0.0,
                    "change": 0.0,
                    "history": []
                })
                continue
        
        return results
    except Exception as e:
        print(f"Error fetching indices: {e}")
        # Return empty results on critical failure
        return [{"name": idx["name"], "value": 0.0, "change": 0.0, "history": []} for idx in indices_config]

@router.get("/market-movers", response_model=MarketMoversResponse)
async def get_market_movers():
    """
    Fetch market movers (Gainers, Losers, Volatile, Active) using Real Data.
    Scans a curated list of popular stocks to find top performers.
    """
    # Curated list of active/popular stocks to scan (Expanded for more results)
    tickers = [
        "NVDA", "TSLA", "AAPL", "AMD", "MSFT", "GOOGL", "AMZN", "META", "NFLX", 
        "INTC", "COIN", "GME", "AMC", "PLTR", "SPY", "QQQ", "IWM", "BA", "WMT", 
        "JPM", "V", "PG", "JNJ", "XOM", "CVX", "BAC", "WFC", "C", "GS", "DIS",
        "UBER", "ABNB", "PYPL", "SQ", "ROKU", "SHOP", "SNOW", "CRM", "ADBE", "ORCL",
        "CSCO", "PEP", "KO", "MCD", "NKE", "IBM", "CAT", "MMM", "GE", "F", "GM",
        "T", "VZ", "TMUS", "CMCSA", "PFE", "MRK", "ABBV", "LLY", "UNH", "COST",
        "HD", "LOW", "SBUX", "TGT", "TJX", "LULU", "NIO", "BABA", "JD", "BIDU",
        "ZM", "DOCU", "TWLO", "NET", "CRWD", "PANW", "FTNT", "ZS", "DDOG", "MDB",
        "OKTA", "TEAM", "WDAY", "NOW", "SNPS", "CDNS", "ADSK", "ANSS", "KLAC", "LRCX"
    ]
    
    try:
        # Batch fetch data for efficiency
        # We need 'price' (regularMarketPrice) and 'previousClose' to calculate change
        # yf.Tickers is good for getting info, but download is faster for price history.
        # However, for "current" snapshot, Tickers().tickers[].info is often used but can be slow sequentially.
        # Let's use yf.download for last 2 days to calculate change if market is open/closed.
        # Actually, yf.download returns a DataFrame.
        
        data = yf.download(tickers, period="5d", interval="1d", progress=False)
        
        # Extract latest data
        # data['Close'] is a DataFrame with columns as Tickers
        
        if data.empty:
             raise HTTPException(status_code=500, detail="No data fetched")

        movers = []
        
        # We need the last two rows to calculate change if we want "daily" change
        # If market is open, the last row is current.
        
        try:
            closes = data['Close']
            volumes = data['Volume']
        except KeyError as e:
            # yfinance structure might vary if multi-level columns
            # If only one ticker, it's Series. If multiple, it's DataFrame.
            # But we passed a list, so it should be MultiIndex or DataFrame.
            # Let's check columns again.
            return {"gainers": [], "losers": [], "volatile": [], "active": []}
        
        # Iterate through tickers
        for ticker in tickers:
            try:
                # Get series for this ticker
                # If MultiIndex, accessing by ticker might need level
                if isinstance(closes.columns, pd.MultiIndex):
                     # This shouldn't happen with 'Close' selected unless structure is different
                     pass
                
                if ticker not in closes.columns:
                    continue

                ticker_closes = closes[ticker].dropna()
                if len(ticker_closes) < 2:
                    continue
                
                current_price = float(ticker_closes.iloc[-1])
                prev_close = float(ticker_closes.iloc[-2])
                
                change = current_price - prev_close
                change_percent = (change / prev_close) * 100
                
                # Get volume (last available)
                ticker_vol = volumes[ticker].dropna()
                volume_num = float(ticker_vol.iloc[-1]) if not ticker_vol.empty else 0
                
                # Format volume
                if volume_num >= 1_000_000:
                    volume_str = f"{round(volume_num / 1_000_000, 1)}M"
                elif volume_num >= 1_000:
                    volume_str = f"{round(volume_num / 1_000, 1)}K"
                else:
                    volume_str = str(int(volume_num))

                movers.append({
                    "ticker": ticker,
                    "price": round(current_price, 2),
                    "change": round(change, 2),
                    "change_percent": round(change_percent, 2),
                    "volume": volume_str,
                    "raw_vol": volume_num,
                    "abs_change": abs(change_percent)
                })
            except Exception:
                continue

        # Sort lists
        # Gainers: Top 15 by change_percent desc
        gainers = sorted([m for m in movers if m['change_percent'] > 0], key=lambda x: x['change_percent'], reverse=True)[:15]
        
        # Losers: Top 15 by change_percent asc
        losers = sorted([m for m in movers if m['change_percent'] < 0], key=lambda x: x['change_percent'])[:15]
        
        # Volatile: Top 15 by abs_change desc
        volatile = sorted(movers, key=lambda x: x['abs_change'], reverse=True)[:15]
        
        # Active: Top 15 by raw_vol desc
        active = sorted(movers, key=lambda x: x['raw_vol'], reverse=True)[:15]
        
        # Fallback if empty (e.g. flat market or data issue)
        if not gainers and movers: gainers = movers[:15]
        if not losers and movers: losers = movers[-15:]

        print(f"DEBUG: Movers count: {len(movers)}")
        print(f"DEBUG: Gainers count: {len(gainers)}")
        print(f"DEBUG: Losers count: {len(losers)}")

        return {
            "gainers": gainers,
            "losers": losers,
            "volatile": volatile,
            "active": active
        }

    except Exception as e:
        print(f"Error fetching market movers: {e}")
        # Fallback to empty or mock if critical failure, but let's return empty lists for now to see error
        return {"gainers": [], "losers": [], "volatile": [], "active": []}

class CryptoData(BaseModel):
    ticker: str
    name: str
    price: float
    date: str
    description: str
    series_id: str
    history: List[Dict[str, Any]]
    selectedTimeframe: str
    loading: bool
    chart_type: str

@router.get("/crypto/all")
async def get_all_crypto_data(timeframe: str = "daily"):
    """
    Fetch data for all major cryptocurrencies WITH history (like Bond/Economic tabs).
    Returns data for BTC-USD, ETH-USD, USDT-USD, BNB-USD, SOL-USD
    Includes history data for the specified timeframe.
    """
    try:
        crypto_pairs = [
            {"ticker": "BTC-USD", "name": "Bitcoin (BTC)", "description": "Bitcoin Price"},
            {"ticker": "ETH-USD", "name": "Ethereum (ETH)", "description": "Ethereum Price"},
            {"ticker": "USDT-USD", "name": "Tether USDt (USDT)", "description": "Tether USDt Price"},
            {"ticker": "BNB-USD", "name": "BNB (BNB)", "description": "BNB Price"},
            {"ticker": "SOL-USD", "name": "Solana (SOL)", "description": "Solana Price"}
        ]
        
        # Map frontend timeframes to yfinance periods
        period_map = {
            "daily": "1mo",
            "weekly": "3mo",
            "monthly": "1y",
            "yearly": "5y"
        }
        
        yf_period = period_map.get(timeframe, "1mo")
        
        results = []
        for pair in crypto_pairs:
            try:
                crypto = yf.Ticker(pair["ticker"])
                # Fetch history with the specified timeframe
                history = crypto.history(period=yf_period)
                
                if history.empty:
                    print(f"[WARNING] {pair['ticker']}: History DataFrame is empty")
                    results.append({
                        "indicator": pair["name"],
                        "value": 0,
                        "volume": 0,
                        "date": datetime.datetime.now().strftime('%Y-%m-%d'),
                        "description": pair["description"],
                        "series_id": pair["ticker"],
                        "history": [],
                        "selectedTimeframe": timeframe,
                        "loading": False,
                        "chart_type": "line"
                    })
                    continue
                
                # Convert history to list with volume
                history_list = []
                has_volume_column = 'Volume' in history.columns
                
                if not has_volume_column:
                    print(f"[DEBUG] {pair['ticker']}: No 'Volume' column in history DataFrame. Available columns: {list(history.columns)}")
                
                volume_count = 0
                for date, row in history.iterrows():
                    try:
                        volume_value = 0
                        if has_volume_column:
                            try:
                                vol = row['Volume']
                                if pd.notna(vol) and vol != 0:
                                    volume_value = float(vol)
                                    volume_count += 1
                            except (KeyError, ValueError, TypeError):
                                volume_value = 0
                        
                        close_value = row['Close']
                        if pd.isna(close_value):
                            print(f"[WARNING] {pair['ticker']}: Skipping row with NaN Close value on {date}")
                            continue
                        
                        history_list.append({
                            "date": date.strftime('%Y-%m-%d'),
                            "value": float(close_value),
                            "volume": volume_value
                        })
                    except Exception as e:
                        print(f"[WARNING] {pair['ticker']}: Error processing row for date {date}: {e}")
                        continue
                
                # Get current price and volume from latest data
                current_price = float(history['Close'].iloc[-1])
                current_volume = 0
                if has_volume_column:
                    try:
                        vol = history['Volume'].iloc[-1]
                        if pd.notna(vol) and vol != 0:
                            current_volume = float(vol)
                    except (KeyError, ValueError, TypeError):
                        current_volume = 0
                current_date = history.index[-1].strftime('%Y-%m-%d')
                
                if has_volume_column:
                    print(f"[DEBUG] {pair['ticker']}: Found {volume_count} non-zero volume entries out of {len(history_list)} total entries")
                
                results.append({
                    "indicator": pair["name"],
                    "value": round(current_price, 2),
                    "volume": round(current_volume, 0),
                    "date": current_date,
                    "description": pair["description"],
                    "series_id": pair["ticker"],
                    "history": history_list,  # Include history in initial response
                    "selectedTimeframe": timeframe,
                    "loading": False,
                    "chart_type": "line"
                })
            except Exception as e:
                print(f"Error fetching {pair['ticker']}: {e}")
                # Add empty entry with error state
                results.append({
                    "indicator": pair["name"],
                    "value": 0,
                    "volume": 0,
                    "date": datetime.datetime.now().strftime('%Y-%m-%d'),
                    "description": pair["description"],
                    "series_id": pair["ticker"],
                    "history": [],
                    "selectedTimeframe": timeframe,
                    "loading": False,
                    "chart_type": "line"
                })
                continue
        
        return results
    except Exception as e:
        print(f"Error fetching all crypto data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/crypto/{ticker}")
async def get_crypto_data(ticker: str):
    """
    Fetch crypto data using yfinance.
    Returns current price and basic info for a cryptocurrency.
    """
    try:
        crypto = yf.Ticker(ticker)
        info = crypto.info
        history = crypto.history(period="1d")
        
        if history.empty:
            raise HTTPException(status_code=404, detail=f"Crypto ticker {ticker} not found")
        
        current_price = float(history['Close'].iloc[-1])
        current_date = history.index[-1].strftime('%Y-%m-%d')
        
        # Get crypto name from info or use ticker
        crypto_name = info.get("longName") or info.get("shortName") or ticker.replace("-USD", "")
        description = f"{crypto_name} Price"
        
        return {
            "ticker": ticker.upper(),
            "name": crypto_name,
            "price": round(current_price, 2),
            "date": current_date,
            "description": description,
            "series_id": ticker.upper(),
            "history": [],
            "selectedTimeframe": "daily",
            "loading": False,
            "chart_type": "line"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching crypto data for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/crypto/{ticker}/history")
async def get_crypto_history(ticker: str, period: str = "1mo"):
    """
    Fetch crypto price history using yfinance.
    
    Args:
        ticker: Crypto ticker (e.g., BTC-USD, ETH-USD)
        period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
    """
    try:
        crypto = yf.Ticker(ticker)
        
        # Map frontend timeframes to yfinance periods
        period_map = {
            "daily": "1mo",
            "weekly": "3mo",
            "monthly": "1y",
            "yearly": "5y"
        }
        
        # Use mapped period if provided, otherwise use the period parameter
        yf_period = period_map.get(period, period)
        
        history = crypto.history(period=yf_period)
        
        if history.empty:
            raise HTTPException(status_code=404, detail=f"No history data for {ticker}")
        
        # Convert to list of {date, value, volume} objects
        history_list = []
        has_volume_column = 'Volume' in history.columns
        
        if not has_volume_column:
            print(f"[DEBUG] {ticker}: No 'Volume' column in history DataFrame. Available columns: {list(history.columns)}")
        
        volume_count = 0
        for date, row in history.iterrows():
            volume_value = 0
            if has_volume_column:
                try:
                    vol = row['Volume']
                    # Check if volume is not NaN and is a valid number
                    if pd.notna(vol) and vol != 0:
                        volume_value = float(vol)
                        volume_count += 1
                except (KeyError, ValueError, TypeError) as e:
                    volume_value = 0
            
            history_list.append({
                "date": date.strftime('%Y-%m-%d'),
                "value": float(row['Close']),
                "volume": volume_value
            })
        
        if has_volume_column:
            print(f"[DEBUG] {ticker}: Found {volume_count} non-zero volume entries out of {len(history_list)} total entries")
        
        # Get current price and volume from latest data
        current_price = float(history['Close'].iloc[-1])
        current_volume = 0
        if has_volume_column:
            try:
                vol = history['Volume'].iloc[-1]
                if pd.notna(vol) and vol != 0:
                    current_volume = float(vol)
            except (KeyError, ValueError, TypeError):
                current_volume = 0
        current_date = history.index[-1].strftime('%Y-%m-%d')
        
        return {
            "history": history_list,
            "value": round(current_price, 2),
            "volume": round(current_volume, 0),
            "date": current_date
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching crypto history for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
