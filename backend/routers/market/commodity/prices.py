import yfinance as yf
from typing import List, Dict, Any

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

def fetch_commodity_from_yahoo(series_id: str, timeframe: str) -> List[Dict[str, Any]]:
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
        return []
