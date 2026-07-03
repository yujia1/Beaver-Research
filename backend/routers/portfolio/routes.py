
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta
import asyncio
import yfinance as yf
import os
import httpx
import xml.etree.ElementTree as ET
import re
from redis_client import redis_client

from routers.admin.auth import get_current_user, create_resource_dependency

# Create resource-specific access dependency
require_portfolio_access = create_resource_dependency('/portfolio')

router = APIRouter()

# --- Pydantic Models ---
class LotCreate(BaseModel):
    purchaseDate: str
    quantity: int
    costPerShare: float
    side: str = "LONG"
    link: Optional[str] = None
    note: Optional[str] = None

class LotUpdate(BaseModel):
    purchaseDate: str
    quantity: int
    costPerShare: float
    side: str
    link: Optional[str] = None
    note: Optional[str] = None

class LotResponse(BaseModel):
    id: int
    purchaseDate: str
    quantity: int
    costPerShare: float
    side: str
    link: Optional[str] = None
    note: Optional[str] = None
    updatedBy: Optional[str] = None

class PositionCreate(BaseModel):
    ticker: str
    sector: Optional[str] = None

class PositionResponse(BaseModel):
    ticker: str
    sector: Optional[str]
    currentPrice: float
    lots: List[LotResponse]
    updatedBy: Optional[str] = None

class TradingSignalRequest(BaseModel):
    ticker: str
    analysis_type: str = "technical"

# --- End Models ---

MARKET_NEWS_CACHE_KEY = "market_news_feed_v1"
MARKET_NEWS_CACHE_TTL = 180 # 3 minutes

# Get FMP API key from environment
FMP_API_KEY = os.getenv("FMP_API_KEY", "")
FMP_BASE_URL = "https://financialmodelingprep.com/stable"

async def fetch_fmp_data(endpoint: str, params: Dict[str, Any] = None) -> List[Dict]:
    """
    Fetch data from Financial Modeling Prep API (Async)
    """
    if not FMP_API_KEY:
        # Don't raise error to avoid crashing entire app if key missing, just return empty
        print("FMP_API_KEY not configured")
        return []
    
    if params is None:
        params = {}
    
    params["apikey"] = FMP_API_KEY
    
    url = f"{FMP_BASE_URL}/{endpoint}"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            # We treat 404/others as empty result for resilience in portfolio context
            if response.status_code != 200:
                print(f"FMP API error {response.status_code}: {response.text}")
                return []
                
            data = response.json()
            
            if isinstance(data, dict) and "Error Message" in data:
                print(f"FMP API error message: {data['Error Message']}")
                return []
            
            # Return data directly; caller handles dict vs list
            # FMP usually returns list for data endpoints
            return data if isinstance(data, list) else [data] if data else []
            
    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        return []

async def fetch_realtime_prices(tickers: List[str]) -> dict:
    if not tickers:
        return {}
    
    # Deduplicate and clean tickers
    clean_tickers = list(set([t.upper().strip() for t in tickers if t]))
    if not clean_tickers:
        return {}

    prices = {}
    
    # 1. Try FMP Batch
    try:
        # Batch fetch using quote endpoint
        ticker_str = ",".join(clean_tickers)
        data = await fetch_fmp_data("quote", {"symbol": ticker_str})
        
        for item in data:
            sym = item.get("symbol")
            if sym:
                prices[sym.upper()] = item.get("price", 0.0)
            
    except Exception as e:
        print(f"Error fetching FMP prices: {e}")
        
    # 2. Fallback to YFinance for missing tickers
    missing_tickers = [t for t in clean_tickers if t not in prices or prices[t] == 0.0]
    if missing_tickers:
        print(f"Falling back to YFinance for: {missing_tickers}")
        try:
             # Run blocking yfinance in thread pool
            import asyncio
            loop = asyncio.get_running_loop()
            
            def fetch_yf_batch(symbols):
                yf_prices = {}
                try:
                    # yf.Tickers might be faster for batch but lets iterate for reliability or use Tickers
                    # yfinance batch download:
                    # data = yf.download(symbols, period="1d") # This is heavy dataframe
                    # lighter:
                    for sym in symbols:
                        try:
                            t = yf.Ticker(sym)
                            # minimal fetch
                            info = t.fast_info
                            p = info.last_price
                            if p:
                                yf_prices[sym] = p
                            else:
                                # try regular info
                                info = t.info
                                yf_prices[sym] = info.get('currentPrice') or info.get('regularMarketPrice', 0.0)
                        except:
                            pass
                except Exception as ex:
                    print(f"YF batch error: {ex}")
                return yf_prices

            yf_data = await loop.run_in_executor(None, fetch_yf_batch, missing_tickers)
            if yf_data:
                for sym, price in yf_data.items():
                    prices[sym.upper()] = price

        except Exception as e:
            print(f"Error in YFinance fallback: {e}")

    return prices

import models
from database import get_db
from models import PortfolioPosition, PortfolioLot, User


async def require_portfolio_write_access(current_user: User = Depends(require_portfolio_access)):
    """
    Portfolio is a single entity shared by every role. Only admin/creator can
    write to it; contributor and user get view-only access.
    """
    if current_user.role not in ("admin", "creator"):
        raise HTTPException(
            status_code=403,
            detail="Only admin and creator roles can modify the portfolio. Contact an administrator to request write access."
        )
    return current_user


# Position endpoints
@router.get("/positions", response_model=List[PositionResponse])
async def get_positions(
    current_user: models.User = Depends(require_portfolio_access),
    db: Session = Depends(get_db)
):
    """Get every position in the shared portfolio, with lots"""
    positions = db.query(PortfolioPosition).all()

    # Fetch real-time prices for all tickers in parallel
    tickers = [pos.ticker.upper() for pos in positions]
    realtime_prices = await fetch_realtime_prices(tickers)

    result = []
    for pos in positions:
        current_ticker = pos.ticker.upper()
        current_price = realtime_prices.get(current_ticker, 0.0)

        result.append({
            "ticker": pos.ticker,
            "sector": pos.sector,
            "currentPrice": current_price,
            "lots": [
                {
                    "id": lot.id,
                    "purchaseDate": lot.purchase_date,
                    "quantity": lot.quantity,
                    "costPerShare": lot.cost_per_share,
                    "side": lot.side,
                    "link": lot.link,
                    "note": lot.note,
                    "updatedBy": lot.updated_by.username if lot.updated_by else None
                }
                for lot in pos.lots
            ],
            "updatedBy": pos.updated_by.username if pos.updated_by else None
        })

    return result


@router.post("/positions")
async def create_position(
    position: PositionCreate,
    current_user: User = Depends(require_portfolio_write_access),
    db: Session = Depends(get_db)
):
    """Create a new position in the shared portfolio"""
    existing = db.query(PortfolioPosition).filter(
        PortfolioPosition.ticker == position.ticker
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Position already exists in the portfolio")

    # Create position
    db_position = PortfolioPosition(
        ticker=position.ticker,
        sector=position.sector,
        updated_by_user_id=current_user.id
    )
    db.add(db_position)
    db.commit()
    db.refresh(db_position)

    response_price = 0.0
    try:
        prices = await fetch_realtime_prices([position.ticker])
        response_price = prices.get(position.ticker.upper(), 0.0)
    except:
        pass

    return {"ticker": db_position.ticker, "sector": db_position.sector, "currentPrice": response_price}


@router.delete("/positions/{ticker}")
def delete_position(
    ticker: str,
    current_user: User = Depends(require_portfolio_write_access),
    db: Session = Depends(get_db)
):
    """Delete a position and all associated lots from the shared portfolio"""
    position = db.query(PortfolioPosition).filter(
        PortfolioPosition.ticker == ticker
    ).first()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")

    db.delete(position)
    db.commit()

    return {"message": "Position deleted successfully"}


# Trade Lot endpoints
@router.post("/positions/{ticker}/lots")
def add_lot(
    ticker: str,
    lot: LotCreate,
    current_user: User = Depends(require_portfolio_write_access),
    db: Session = Depends(get_db)
):
    """Add a lot to a position in the shared portfolio"""
    position = db.query(PortfolioPosition).filter(
        PortfolioPosition.ticker == ticker
    ).first()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")

    db_lot = PortfolioLot(
        position_id=position.id,
        purchase_date=lot.purchaseDate,
        quantity=lot.quantity,
        cost_per_share=lot.costPerShare,
        side=lot.side,
        link=lot.link,
        note=lot.note,
        updated_by_user_id=current_user.id
    )
    db.add(db_lot)
    position.updated_by_user_id = current_user.id
    db.commit()
    db.refresh(db_lot)

    return {
        "id": db_lot.id,
        "purchaseDate": db_lot.purchase_date,
        "quantity": db_lot.quantity,
        "costPerShare": db_lot.cost_per_share,
        "side": db_lot.side,
        "link": db_lot.link,
        "note": db_lot.note,
        "updatedBy": current_user.username
    }


@router.put("/lots/{lot_id}")
def update_lot(
    lot_id: int,
    lot: LotUpdate,
    current_user: User = Depends(require_portfolio_write_access),
    db: Session = Depends(get_db)
):
    """Update a lot in the shared portfolio"""
    db_lot = db.query(PortfolioLot).filter(PortfolioLot.id == lot_id).first()
    if not db_lot:
        raise HTTPException(status_code=404, detail="Lot not found")

    db_lot.purchase_date = lot.purchaseDate
    db_lot.quantity = lot.quantity
    db_lot.cost_per_share = lot.costPerShare
    db_lot.side = lot.side
    db_lot.link = lot.link
    db_lot.note = lot.note
    db_lot.updated_by_user_id = current_user.id
    db_lot.position.updated_by_user_id = current_user.id

    db.commit()
    db.refresh(db_lot)

    return {
        "id": db_lot.id,
        "purchaseDate": db_lot.purchase_date,
        "quantity": db_lot.quantity,
        "costPerShare": db_lot.cost_per_share,
        "side": db_lot.side,
        "link": db_lot.link,
        "note": db_lot.note,
        "updatedBy": current_user.username
    }


@router.delete("/lots/{lot_id}")
def delete_lot(
    lot_id: int,
    current_user: User = Depends(require_portfolio_write_access),
    db: Session = Depends(get_db)
):
    """Delete a lot from the shared portfolio"""
    db_lot = db.query(PortfolioLot).filter(PortfolioLot.id == lot_id).first()
    if not db_lot:
        raise HTTPException(status_code=404, detail="Lot not found")

    position_id = db_lot.position_id
    db.delete(db_lot)
    db.commit()

    # Check if position has any remaining lots
    remaining_lots = db.query(PortfolioLot).filter(PortfolioLot.position_id == position_id).count()
    if remaining_lots == 0:
        # Delete the position if no lots remain
        position = db.query(PortfolioPosition).filter(PortfolioPosition.id == position_id).first()
        if position:
            db.delete(position)
            db.commit()
            return {"message": "Lot and position deleted successfully"}

    return {"message": "Lot deleted successfully"}


# Stock price endpoint (existing)
@router.get("/portfolio")
async def get_portfolio_summary(current_user: models.User = Depends(require_portfolio_access)):
    """Get current stock price and info"""
    # This function body needs to be adapted to work with a portfolio summary
    # For now, it's a placeholder based on the original get_stock_data
    # It would typically iterate through user's positions and summarize.
    # As per instruction, I'm keeping the original body structure but it's logically flawed for "portfolio"
    # without a ticker. I'll make it return a placeholder for now.
    return {"message": "Portfolio summary endpoint - implementation pending"}


@router.post("/trading-signal")
async def generate_trading_signal(
    signal_request: TradingSignalRequest,
    current_user: models.User = Depends(require_portfolio_access)
):
    """Get current stock prices for multiple tickers"""
    # This function body needs to be adapted for trading signals.
    # As per instruction, I'm keeping the original body structure but it's logically flawed for "trading-signal"
    # without a list of tickers. I'll make it return a placeholder for now.
    return {"message": f"Trading signal for {signal_request.ticker} ({signal_request.analysis_type}) - implementation pending"}


@router.get("/stock-price/{ticker}")
async def get_single_stock_price(ticker: str):
    """Get current price for a single ticker"""
    prices = await fetch_realtime_prices([ticker])
    t_upper = ticker.upper()
    current_price = prices.get(t_upper, 0.0)
    # Round to 2 decimals
    rounded_price = round(current_price, 2)
    return {"ticker": t_upper, "currentPrice": rounded_price}


@router.post("/stock-prices")
async def get_batch_stock_prices(tickers: List[str]):
    """Get current stock prices for multiple tickers"""
    if not tickers:
        return {}
        
    prices = await fetch_realtime_prices(tickers)
    result = {}
    
    # We only have prices from FMP batch quote here, full info (company name/sector) 
    # might need separate call or just return what we have if the frontend just needs price update.
    # The frontend currently expects {ticker: {currentPrice...}}.
    # To keep it simple and fast, we map the price. If more info needed, we might need a richer FMP call.
    # However, fetch_realtime_prices only returns {TICKER: price}.
    
    for ticker in tickers:
        t_upper = ticker.upper()
        price = prices.get(t_upper, 0.0)
        result[ticker] = {
            "ticker": ticker,
            "currentPrice": price,
            # We don't have these from simple price fetch, but usually this endpoint
            # is just for refreshing price. We can leave them empty or unchanged if frontend handles it.
            # Looking at frontend refreshPrices: it updates companyName/sector too if present.
            # For now, let's just return price as primary.
        }
            
    return result






@router.get("/market-movers/{mover_type}")
async def get_market_movers(mover_type: str):
    """
    Get market movers: 'most-actives', 'gainers', 'losers'
    """
    endpoint_map = {
        "most-actives": "most-actives",
        "gainers": "biggest-gainers",
        "losers": "biggest-losers"
    }
    
    if mover_type not in endpoint_map:
        raise HTTPException(status_code=400, detail="Invalid mover type. Use 'most-actives', 'gainers', or 'losers'")
        
    fmp_endpoint = endpoint_map[mover_type]
    data = await fetch_fmp_data(fmp_endpoint)
    
    # Process data to ensure consistent format (FMP returns list of objects)
    # We want: symbol, name, price, changesPercentage, priceChange
    result = []
    
    for item in data:
        result.append({
            "ticker": item.get("symbol"),
            "name": item.get("name") or item.get("companyName", ""), # FMP inconsistent naming
            "price": item.get("price", 0.0),
            "change": item.get("change", 0.0),
            "changesPercentage": item.get("changesPercentage", 0.0)
        })
        
    return result



# Helper to get valid trading date (handling weekends)
def get_latest_trading_date() -> str:
    from datetime import timedelta
    now = datetime.utcnow()
    # If today is Saturday (5) or Sunday (6), go back to Friday
    weekday = now.weekday()
    if weekday == 5:  # Saturday
        last_trade = now - timedelta(days=1)
    elif weekday == 6:  # Sunday
        last_trade = now - timedelta(days=2)
    else:
        last_trade = now
    return last_trade.strftime("%Y-%m-%d")


@router.get("/sector-performance")
async def get_sector_performance(exchange: str = "NASDAQ", date: Optional[str] = None):
    """
    Fetch sector performance snapshot.
    If date is not provided, defaults to latest trading day (handling weekends).
    """
    if not date:
        date = get_latest_trading_date()
        
    params = {"exchange": exchange, "date": date}
        
    data = await fetch_fmp_data("sector-performance-snapshot", params)
    
    # FMP returns a list of dicts like:
    # {
    #   "date": "2025-12-23",
    #   "sector": "Basic Materials",
    #   "exchange": "NASDAQ",
    #   "averageChange": 0.35185130179673507
    # }
    
    # We can perform any backend processing if needed, but for now passing through is fine
    # Frontend expects { sector: val, ... } or list. Let's return the list and let frontend map it.
    
    return data


@router.get("/sector-pe")
async def get_sector_pe(exchange: str = "NASDAQ", date: Optional[str] = None):
    """
    Fetch sector PE snapshot.
    If date is not provided, defaults to latest trading day (handling weekends).
    """
    if not date:
        date = get_latest_trading_date()

    params = {"exchange": exchange, "date": date}
        
    data = await fetch_fmp_data("sector-pe-snapshot", params)
    
    # FMP returns a list of dicts like:
    # {
    #   "date": "2025-12-23",
    #   "sector": "Basic Materials",
    #   "exchange": "NASDAQ",
    #   "pe": 25.261917696069528
    # }
    
    return data


@router.get("/industry-performance")
async def get_industry_performance(exchange: str = "NASDAQ", date: Optional[str] = None):
    """
    Fetch industry performance snapshot.
    If date is not provided, defaults to latest trading day (handling weekends).
    """
    if not date:
        date = get_latest_trading_date()

    params = {"exchange": exchange, "date": date}
        
    data = await fetch_fmp_data("industry-performance-snapshot", params)
    return data


@router.get("/industry-pe")
async def get_industry_pe(exchange: str = "NASDAQ", date: Optional[str] = None):
    """
    Fetch industry PE snapshot.
    If date is not provided, defaults to latest trading day (handling weekends).
    """
    if not date:
        date = get_latest_trading_date()

    params = {"exchange": exchange, "date": date}
        
    data = await fetch_fmp_data("industry-pe-snapshot", params)
    return data

# Market News Feed endpoints
@router.get("/market-news-feed")
async def get_market_news_feed():
    """Get market news feed from cache or fetch fresh"""
    # 1. Try Cache (Primary)
    cached_data = redis_client.get_cache(MARKET_NEWS_CACHE_KEY)
    if cached_data:
        return cached_data

    # 2. Fallback: Fetch immediately if cache is empty (e.g. first run)
    items = await _fetch_market_news_from_source()
    
    if items:
        # Cache for 5 minutes
        redis_client.set_cache(MARKET_NEWS_CACHE_KEY, items, ttl=300)
        
    return items

async def _fetch_market_news_from_source():
    """Fetch market news from RSS feeds"""
    items = []
    
    # Define feeds configuration
    feeds = [
        {"url": "http://feeds.feedburner.com/zerohedge/feed", "tag": "MARKETS", "type": "zerohedge"},
        {"url": "https://thebearcave.substack.com/feed", "tag": "RESEARCH", "type": "bearcave"}
    ]
    
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            tasks = [client.get(feed["url"]) for feed in feeds]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, response in enumerate(responses):
                feed_config = feeds[i]
                
                if isinstance(response, Exception):
                    continue
                    
                if response.status_code != 200:
                    continue
                
                feed_items = _parse_feed_items(response.content, feed_config)
                items.extend(feed_items)
                
        # Sort by date
        def parse_pub_date(date_str):
            try:
                from email.utils import parsedate_to_datetime
                dt = parsedate_to_datetime(date_str)
                if dt: return dt
            except:
                pass
            return datetime.min.replace(tzinfo=None)

        items.sort(key=lambda x: parse_pub_date(x.get("time", "")), reverse=True)
        return items
            
    except Exception as e:
        return []

def _parse_feed_items(content, config):
    """Parse RSS feed items"""
    items = []
    try:
        root = ET.fromstring(content)
        
        for item in root.findall(".//item")[:10]:
            title_elem = item.find("title")
            link_elem = item.find("link")
            pub_date_elem = item.find("pubDate")
            
            if title_elem is not None and link_elem is not None:
                items.append({
                    "title": title_elem.text,
                    "link": link_elem.text,
                    "time": pub_date_elem.text if pub_date_elem is not None else "",
                    "tag": config["tag"]
                })
                    
    except Exception as e:
        pass
        
    return items
