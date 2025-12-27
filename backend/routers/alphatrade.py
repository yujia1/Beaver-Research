
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
            # We treat 404/others as empty result for resilience in alphatrade context
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
from models import AlphaTradePosition, AlphaTradeLot, AlphaTradeFundamentalAnalysis, User
from routers.auth import get_current_user, verify_premium_access

router = APIRouter()

@router.get("/market-news-feed")
async def get_market_news_feed():
    # 1. Try Cache (Primary)
    cached_data = redis_client.get_cache(MARKET_NEWS_CACHE_KEY)
    if cached_data:
        return cached_data

    # 2. Fallback: Fetch immediately if cache is empty (e.g. first run)
    items = await _fetch_market_news_from_source()
    
    if items:
        # Cache for 5 minutes (longer than poll interval of 3 mins)
        redis_client.set_cache(MARKET_NEWS_CACHE_KEY, items, ttl=300)
        
    return items

async def background_news_fetcher():
    """Background task to fetch news every 3 minutes"""
    while True:
        try:
            items = await _fetch_market_news_from_source()
            if items:
                # Set TTL longer than sleep (5m TTL vs 3m Sleep) to ensure overlap
                redis_client.set_cache(MARKET_NEWS_CACHE_KEY, items, ttl=300)
        except Exception as e:
            print(f"Error in background news fetch: {e}")
        
        await asyncio.sleep(180) # Sleep 3 minutes

def start_news_polling():
    """Start the background polling task"""
    asyncio.create_task(background_news_fetcher())

async def _fetch_market_news_from_source():
    items = []
    
    # Define feeds configuration
    feeds = [
        {"url": "http://feeds.feedburner.com/zerohedge/feed", "tag": "MARKETS", "type": "zerohedge"},
        {"url": "https://thebearcave.substack.com/feed", "tag": "RESEARCH", "type": "bearcave"}
    ]
    
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            # Create tasks for all feeds
            tasks = [client.get(feed["url"]) for feed in feeds]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, response in enumerate(responses):
                feed_config = feeds[i]
                
                if isinstance(response, Exception):
                    print(f"Error fetching {feed_config['url']}: {response}")
                    continue
                    
                if response.status_code != 200:
                    print(f"Failed to fetch {feed_config['url']}: {response.status_code}")
                    continue
                
                # Parse the feed
                feed_items = _parse_feed_items(response.content, feed_config)
                items.extend(feed_items)
                
        # Sort items by date (newest first) using the parsed datetime object or string comparison fallback
        # Note: parsing dates strictly can be tricky across feeds, simple string works if standard format, 
        # but robust implementation would parse to datetime.
        # For now, we rely on the fact that both feeds use standard RSS pubDate.
        
        # Helper to parse date for sorting
        def parse_pub_date(date_str):
            try:
                # Common RSS format: "Sat, 27 Dec 2025 23:44:50 GMT"
                # Remove GMT/UTC to make it simpler for naive parsing or use email utils
                from email.utils import parsedate_to_datetime
                dt = parsedate_to_datetime(date_str)
                if dt: return dt
            except:
                pass
            return datetime.min.replace(tzinfo=None)

        items.sort(key=lambda x: parse_pub_date(x.get("time", "")), reverse=True)
        
        return items
            
    except Exception as e:
        print(f"Error in main fetch loop: {str(e)}")
        return []

def _parse_feed_items(content, config):
    items = []
    try:
        root = ET.fromstring(content)
        # Handle namespaces if necessary, but standard find/findall often works for basic RSS
        # Substack/BearCave uses content:encoded often, needing namespace map
        namespaces = {
            'content': 'http://purl.org/rss/1.0/modules/content/',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'atom': 'http://www.w3.org/2005/Atom'
        }
        
        for item in root.findall(".//item"):
            title_elem = item.find("title")
            title = title_elem.text if title_elem is not None else "No Title"
            
            link_elem = item.find("link")
            link = link_elem.text if link_elem is not None else ""
            
            # Date
            pub_date_elem = item.find("pubDate")
            pub_date = pub_date_elem.text if pub_date_elem is not None else ""
            
            # Content / Description
            desc_elem = item.find("description")
            desc_text = desc_elem.text if desc_elem is not None else ""
            
            # For BearCave/Substack, prefer content:encoded if description is short or just a summary
            content_encoded_elem = item.find("content:encoded", namespaces)
            full_content = ""
            
            if content_encoded_elem is not None and content_encoded_elem.text:
                full_content = content_encoded_elem.text
            else:
                full_content = desc_text

            # Clean content based on source type
            cleaned_content = full_content
            
            if config["type"] == "zerohedge" and cleaned_content:
                cleaned_content = re.sub(r'<span[^>]*?schema:author[^>]*?>.*?</span>', '', cleaned_content, flags=re.IGNORECASE | re.DOTALL)
                cleaned_content = re.sub(r'<span[^>]*?schema:dateCreated[^>]*?>.*?</span>', '', cleaned_content, flags=re.IGNORECASE | re.DOTALL)
            
            # Clean Bear Cave specific footers if needed (usually substack buttons)
            if config["type"] == "bearcave" and cleaned_content:
                # Remove subscription widgets and footers
                cleaned_content = re.sub(r'<div class="subscription-widget-wrap-editor".*?</div>', '', cleaned_content, flags=re.IGNORECASE | re.DOTALL)
                cleaned_content = re.sub(r'<p class="button-wrapper".*?</a></p>', '', cleaned_content, flags=re.IGNORECASE | re.DOTALL)
                
                # Remove "Until next week" and everything after
                cleaned_content = re.sub(r'<p>Until next week,</p>.*', '', cleaned_content, flags=re.IGNORECASE | re.DOTALL)
                cleaned_content = re.sub(r'<div><hr></div><p>Until next week,.*', '', cleaned_content, flags=re.IGNORECASE | re.DOTALL)

                # Remove specific footer links/text
                cleaned_content = re.sub(r'<h5><strong>New\? </strong><em><strong><a href="https://thebearcave.substack.com/">Sign Up Here</a></strong></em></h5>', '', cleaned_content, flags=re.IGNORECASE)
                cleaned_content = re.sub(r'<h5><strong>Got Feedback\? Just Hit Reply</strong></h5>', '', cleaned_content, flags=re.IGNORECASE)
                cleaned_content = re.sub(r'<h5><strong>The Bear Cave is Not Investment Advice.*?</strong></h5>', '', cleaned_content, flags=re.IGNORECASE | re.DOTALL)


            # Create Plain Summary
            summary_source = desc_text if desc_text else full_content
            summary = re.sub(r'<[^>]+>', '', summary_source)
            summary = summary.replace("\n", " ").strip()
            if len(summary) > 300:
                summary = summary[:297] + "..."
            
            # Sentiment
            title_lower = title.lower()
            sentiment = "neutral"
            if any(x in title_lower for x in ["surge", "rally", "soar", "record", "jump", "beat", "strong"]):
                sentiment = "positive"
            elif any(x in title_lower for x in ["plunge", "crash", "drop", "fall", "miss", "warn", "freeze", "sanction", "weak", "resign", "problem"]):
                sentiment = "negative"

            items.append({
                "id": link,
                "headline": title,
                "summary": summary,
                "content": cleaned_content, 
                "time": pub_date, 
                "url": link,
                "tags": [config["tag"]],
                "sentiment": sentiment
            })
    except Exception as e:
        print(f"Error parsing feed {config['url']}: {e}")
        
    return items


# Pydantic schemas
class LotCreate(BaseModel):
    purchaseDate: str
    quantity: int
    costPerShare: float
    side: str  # 'LONG' or 'SHORT'
    link: Optional[str] = None
    note: Optional[str] = None


class LotUpdate(BaseModel):
    purchaseDate: str
    quantity: int
    costPerShare: float
    link: Optional[str] = None
    note: Optional[str] = None


class LotResponse(BaseModel):
    id: int
    purchaseDate: str
    quantity: int
    costPerShare: float
    side: str
    link: Optional[str]
    note: Optional[str]

    class Config:
        from_attributes = True


class PositionCreate(BaseModel):
    ticker: str
    sector: Optional[str] = None


class FundamentalAnalysisUpdate(BaseModel):
    questionId: int
    answer: Optional[str] = None
    score: Optional[int] = None


class PositionResponse(BaseModel):
    ticker: str
    sector: Optional[str]
    currentPrice: float
    lots: List[LotResponse]
    fundamentalAnalysis: dict
    fundamentalScores: dict

    class Config:
        from_attributes = True

class TradingSignalRequest(BaseModel):
    ticker: str
    analysis_type: str # e.g., 'technical', 'fundamental'
    parameters: Optional[dict] = None





# Helper function to get stock price
def get_stock_price(ticker: str) -> float:
    # Try FMP first
    try:
        url = f"https://financialmodelingprep.com/stable/quote?symbol={ticker}&apikey={FMP_API_KEY}"
        with httpx.Client() as client:
            response = client.get(url)
            if response.status_code == 200:
                data = response.json()
                if data:
                    return data[0].get('price', 0.0)
    except Exception as e:
        print(f"Error fetching FMP price for {ticker}: {e}")

    # Fallback to yfinance
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return info.get('currentPrice') or info.get('regularMarketPrice', 0.0)
    except:
        return 0.0


# Position endpoints
@router.get("/positions", response_model=List[PositionResponse])
async def get_positions(
    current_user: models.User = Depends(verify_premium_access),
    db: Session = Depends(get_db)
):
    """Get all positions for the current user with lots and fundamental analysis"""
    positions = db.query(AlphaTradePosition).filter(
        AlphaTradePosition.user_id == current_user.id
    ).all()
    
    # Fetch real-time prices for all tickers in parallel
    # Ensure we pass uppercase tickers to helper
    tickers = [pos.ticker.upper() for pos in positions]
    realtime_prices = await fetch_realtime_prices(tickers)
    
    result = []
    for pos in positions:
        # Build fundamental analysis dict
        fundamental_analysis = {}
        fundamental_scores = {}
        for analysis in pos.fundamental_analysis:
            fundamental_analysis[str(analysis.question_id)] = analysis.answer or ""
            if analysis.score:
                fundamental_scores[str(analysis.question_id)] = analysis.score
        
        # Use realtime price if available, otherwise fallback to DB price (which might be stale)
        # 1. Try exact match
        # 2. Try uppercase match
        # 3. Fallback
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
                    "note": lot.note
                }
                for lot in pos.lots
            ],
            "fundamentalAnalysis": fundamental_analysis,
            "fundamentalScores": fundamental_scores
        })
    
    return result


@router.post("/positions")
def create_position(
    position: PositionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new position for the current user"""
    # Check if position already exists for this user
    existing = db.query(AlphaTradePosition).filter(
        AlphaTradePosition.user_id == current_user.id,
        AlphaTradePosition.ticker == position.ticker
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Position already exists for this user")
    
    # Create position
    db_position = AlphaTradePosition(
        user_id=current_user.id,
        ticker=position.ticker,
        sector=position.sector
    )
    db.add(db_position)
    db.commit()
    db.refresh(db_position)
    
    # Try to get real-time price for the response only
    response_price = 0.0
    try:
        response_price = get_stock_price(position.ticker)
    except:
        pass
    
    return {"ticker": db_position.ticker, "sector": db_position.sector, "currentPrice": response_price}


@router.delete("/positions/{ticker}")
def delete_position(
    ticker: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a position and all associated lots for the current user"""
    position = db.query(AlphaTradePosition).filter(
        AlphaTradePosition.user_id == current_user.id,
        AlphaTradePosition.ticker == ticker
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a lot to a position for the current user"""
    position = db.query(AlphaTradePosition).filter(
        AlphaTradePosition.user_id == current_user.id,
        AlphaTradePosition.ticker == ticker
    ).first()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    
    db_lot = AlphaTradeLot(
        position_id=position.id,
        purchase_date=lot.purchaseDate,
        quantity=lot.quantity,
        cost_per_share=lot.costPerShare,
        side=lot.side,
        link=lot.link,
        note=lot.note
    )
    db.add(db_lot)
    db.commit()
    db.refresh(db_lot)
    
    return {
        "id": db_lot.id,
        "purchaseDate": db_lot.purchase_date,
        "quantity": db_lot.quantity,
        "costPerShare": db_lot.cost_per_share,
        "side": db_lot.side,
        "link": db_lot.link,
        "note": db_lot.note
    }


@router.put("/lots/{lot_id}")
def update_lot(
    lot_id: int,
    lot: LotUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a lot (verify user owns the position)"""
    db_lot = db.query(AlphaTradeLot).filter(AlphaTradeLot.id == lot_id).first()
    if not db_lot:
        raise HTTPException(status_code=404, detail="Lot not found")
    
    # Verify user owns the position
    if db_lot.position.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this lot")
    
    db_lot.purchase_date = lot.purchaseDate
    db_lot.quantity = lot.quantity
    db_lot.cost_per_share = lot.costPerShare
    db_lot.link = lot.link
    db_lot.note = lot.note
    
    db.commit()
    db.refresh(db_lot)
    
    return {
        "id": db_lot.id,
        "purchaseDate": db_lot.purchase_date,
        "quantity": db_lot.quantity,
        "costPerShare": db_lot.cost_per_share,
        "side": db_lot.side,
        "link": db_lot.link,
        "note": db_lot.note
    }


@router.delete("/lots/{lot_id}")
def delete_lot(
    lot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a lot (verify user owns the position)"""
    db_lot = db.query(AlphaTradeLot).filter(AlphaTradeLot.id == lot_id).first()
    if not db_lot:
        raise HTTPException(status_code=404, detail="Lot not found")
    
    # Verify user owns the position
    if db_lot.position.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this lot")
    
    position_id = db_lot.position_id
    db.delete(db_lot)
    db.commit()
    
    # Check if position has any remaining lots
    remaining_lots = db.query(AlphaTradeLot).filter(AlphaTradeLot.position_id == position_id).count()
    if remaining_lots == 0:
        # Delete the position if no lots remain
        position = db.query(AlphaTradePosition).filter(AlphaTradePosition.id == position_id).first()
        if position:
            db.delete(position)
            db.commit()
            return {"message": "Lot and position deleted successfully"}
    
    return {"message": "Lot deleted successfully"}


# Fundamental Analysis endpoints
@router.put("/positions/{ticker}/analysis")
def update_fundamental_analysis(
    ticker: str,
    analysis: FundamentalAnalysisUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update fundamental analysis for a position owned by current user"""
    position = db.query(AlphaTradePosition).filter(
        AlphaTradePosition.user_id == current_user.id,
        AlphaTradePosition.ticker == ticker
    ).first()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    
    # Check if analysis for this question already exists
    db_analysis = db.query(AlphaTradeFundamentalAnalysis).filter(
        AlphaTradeFundamentalAnalysis.position_id == position.id,
        AlphaTradeFundamentalAnalysis.question_id == analysis.questionId
    ).first()
    
    if db_analysis:
        # Update existing
        if analysis.answer is not None:
            db_analysis.answer = analysis.answer
        if analysis.score is not None:
            db_analysis.score = analysis.score
        db_analysis.updated_at = datetime.utcnow()
    else:
        # Create new
        db_analysis = AlphaTradeFundamentalAnalysis(
            position_id=position.id,
            question_id=analysis.questionId,
            answer=analysis.answer,
            score=analysis.score
        )
        db.add(db_analysis)
    
    db.commit()
    
    return {"message": "Analysis updated successfully"}



# Stock price endpoint (existing)
@router.get("/portfolio")
async def get_portfolio_summary(current_user: models.User = Depends(verify_premium_access)):
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
    current_user: models.User = Depends(verify_premium_access)
):
    """Get current stock prices for multiple tickers"""
    # This function body needs to be adapted for trading signals.
    # As per instruction, I'm keeping the original body structure but it's logically flawed for "trading-signal"
    # without a list of tickers. I'll make it return a placeholder for now.
    return {"message": f"Trading signal for {signal_request.ticker} ({signal_request.analysis_type}) - implementation pending"}


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
