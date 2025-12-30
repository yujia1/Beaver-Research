import yfinance as yf
from typing import List, Dict, Any

# Mapping of currency series IDs to Yahoo Finance ticker symbols
currency_ticker_map = {
    "DEXUSEU": "EURUSD=X",  # U.S. / Euro Foreign Exchange Rate (USD per EUR)
    "DEXJPUS": "JPY=X",     # Japanese Yen to U.S. Dollar Spot Exchange Rate (JPY per USD)
    "DEXCHUS": "CNY=X",     # China / U.S. Foreign Exchange Rate (CNY per USD)
}

def fetch_currency_from_yahoo(series_id: str, timeframe: str) -> List[Dict[str, Any]]:
    """Fetch currency exchange rate data from Yahoo Finance and return list of {'date': str, 'value': float}."""
    try:
        ticker_symbol = currency_ticker_map.get(series_id)
        if not ticker_symbol:
            print(f"No Yahoo Finance ticker mapping found for {series_id}")
            return []
        
        # Map timeframe to yfinance period
        period_map_yahoo = {
            "daily": "1mo",
            "weekly": "3mo",
            "monthly": "1y",
            "quarterly": "1y",
            "yearly": "5y",
            "5y": "5y",
            "max": "max"
        }
        period = period_map_yahoo.get(timeframe, "1y")
        
        # Map timeframe to interval
        interval_map = {
            "daily": "1d",
            "weekly": "1d",
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
        
        print(f"[CURRENCY] Fetched {len(history)} data points from Yahoo Finance for {series_id} ({ticker_symbol})")
        return history
    except Exception as e:
        print(f"Error fetching currency {series_id} from Yahoo Finance: {e}")
        return []
