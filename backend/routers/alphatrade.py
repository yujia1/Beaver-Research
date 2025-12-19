from fastapi import APIRouter, HTTPException
from typing import Dict, List
import yfinance as yf
from datetime import datetime

router = APIRouter()

@router.get("/stock-price/{ticker}")
async def get_stock_price(ticker: str) -> Dict:
    """
    Get current stock price and company info for a ticker using yfinance.
    """
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info
        
        # Get current price
        current_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose', 0)
        
        # Get company info
        company_name = info.get('longName') or info.get('shortName') or ticker.upper()
        sector = info.get('sector') or 'UNKNOWN'
        
        return {
            "ticker": ticker.upper(),
            "currentPrice": float(current_price) if current_price else 0.0,
            "companyName": company_name,
            "sector": sector.upper(),
            "lastUpdated": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error fetching stock price for {ticker}: {e}")
        raise HTTPException(status_code=404, detail=f"Could not fetch data for ticker {ticker}")

@router.post("/stock-prices")
async def get_multiple_stock_prices(tickers: List[str]) -> Dict[str, Dict]:
    """
    Get current stock prices for multiple tickers.
    Returns a dictionary with ticker as key and price data as value.
    """
    results = {}
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker.upper())
            info = stock.info
            
            current_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose', 0)
            company_name = info.get('longName') or info.get('shortName') or ticker.upper()
            sector = info.get('sector') or 'UNKNOWN'
            
            results[ticker.upper()] = {
                "ticker": ticker.upper(),
                "currentPrice": float(current_price) if current_price else 0.0,
                "companyName": company_name,
                "sector": sector.upper(),
                "lastUpdated": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error fetching stock price for {ticker}: {e}")
            results[ticker.upper()] = {
                "ticker": ticker.upper(),
                "currentPrice": 0.0,
                "companyName": ticker.upper(),
                "sector": "UNKNOWN",
                "error": str(e)
            }
    
    return results
