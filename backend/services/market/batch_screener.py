"""
Batch Screener Service

Background service for batch screening entire U.S. market.
Processes stocks in batches with rate limiting and saves flagged companies to database.
"""

import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from models import StockUniverse, FlaggedCompany, ScreeningRun
from services.market.fmp_financial_service import (
    fetch_all_financial_statements,
    fetch_stock_quote,
    FMPAPIError
)
from services.market.screener_calculator import calculate_all_metrics, check_red_flags
from database import get_db

logger = logging.getLogger(__name__)


def fetch_and_save_us_stock_list(db: Session) -> int:
    """
    Fetch all U.S. stock tickers from FMP and save to database
    
    Args:
        db: Database session
    
    Returns:
        Number of stocks saved
    """
    try:
        from services.market.fmp_financial_service import _make_fmp_request
        
        # Fetch stock list from FMP
        endpoint = "stock-list"
        data = _make_fmp_request(endpoint, {})
        
        if not isinstance(data, list):
            logger.error(f"Unexpected stock list format: {type(data)}")
            return 0
        
        # Filter for U.S. exchanges
        us_exchanges = ['NASDAQ', 'NYSE', 'AMEX']
        us_stocks = [
            stock for stock in data 
            if stock.get('exchangeShortName') in us_exchanges
        ]
        
        logger.info(f"Found {len(us_stocks)} U.S. stocks")
        
        # Save to database (upsert)
        saved_count = 0
        for stock in us_stocks:
            ticker = stock.get('symbol')
            if not ticker:
                continue
            
            # Check if exists
            existing = db.query(StockUniverse).filter(StockUniverse.ticker == ticker).first()
            
            if existing:
                # Update existing
                existing.company_name = stock.get('name')
                existing.exchange = stock.get('exchangeShortName')
                existing.is_active = True
            else:
                # Create new
                new_stock = StockUniverse(
                    ticker=ticker,
                    company_name=stock.get('name'),
                    exchange=stock.get('exchangeShortName'),
                    is_active=True
                )
                db.add(new_stock)
            
            saved_count += 1
            
            # Commit in batches of 100
            if saved_count % 100 == 0:
                db.commit()
                logger.info(f"Saved {saved_count} stocks...")
        
        # Final commit
        db.commit()
        logger.info(f"Successfully saved {saved_count} U.S. stocks to database")
        
        return saved_count
    
    except Exception as e:
        logger.error(f"Error fetching/saving stock list: {e}")
        db.rollback()
        return 0


def get_stock_universe(db: Session, limit: Optional[int] = None) -> List[str]:
    """
    Get list of stock tickers from database
    
    Args:
        db: Database session
        limit: Optional limit on number of stocks
    
    Returns:
        List of ticker symbols
    """
    query = db.query(StockUniverse.ticker).filter(StockUniverse.is_active == True)
    
    if limit:
        query = query.limit(limit)
    
    tickers = [row[0] for row in query.all()]
    logger.info(f"Retrieved {len(tickers)} tickers from stock universe")
    
    return tickers


def screen_single_stock(
    ticker: str,
    enable_peer_comparison: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Screen a single stock and return metrics
    
    Args:
        ticker: Stock ticker symbol
        enable_peer_comparison: Whether to enable peer comparison (slower)
    
    Returns:
        Dictionary with metrics and red flags, or None if error
    """
    try:
        # Fetch financial data
        financial_data = fetch_all_financial_statements(ticker, years=5)
        
        # Fetch current price
        quote = fetch_stock_quote(ticker)
        current_price = quote.get('price', 0)
        
        # Calculate metrics
        metrics = calculate_all_metrics(
            income_data=financial_data["income"],
            cash_flow_data=financial_data["cashflow"],
            balance_sheet_data=financial_data["balance"],
            current_price=current_price,
            ticker=ticker if enable_peer_comparison else None
        )
        
        # Check red flags
        red_flags_summary = check_red_flags(metrics)
        
        return {
            "ticker": ticker,
            "metrics": metrics,
            "red_flags": red_flags_summary,
            "current_price": current_price,
            "financial_data": financial_data
        }
    
    except FMPAPIError as e:
        logger.warning(f"FMP API error for {ticker}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error screening {ticker}: {e}")
        return None


def save_flagged_company(
    db: Session,
    screening_result: Dict[str, Any],
    screening_run_id: int
) -> bool:
    """
    Save flagged company to database
    
    Args:
        db: Database session
        screening_result: Result from screen_single_stock
        screening_run_id: ID of the screening run
    
    Returns:
        True if saved, False otherwise
    """
    try:
        red_flags = screening_result["red_flags"]
        
        # Only save if there are red flags
        if not red_flags["has_red_flags"]:
            return False
        
        ticker = screening_result["ticker"]
        
        # Convert metrics to JSON-serializable format
        metrics_dict = {}
        for key, metric_result in screening_result["metrics"].items():
            metrics_dict[key] = {
                "name": metric_result.name,
                "latest_value": metric_result.latest_value,
                "is_red_flag": metric_result.is_red_flag,
                "red_flag_reason": metric_result.red_flag_reason,
                "trend": {
                    "values": metric_result.trend.values if metric_result.trend else [],
                    "years": metric_result.trend.years if metric_result.trend else [],
                    "direction": metric_result.trend.direction if metric_result.trend else None,
                    "slope": metric_result.trend.slope if metric_result.trend else None
                } if metric_result.trend else None
            }
        
        # Create flagged company record
        flagged_company = FlaggedCompany(
            ticker=ticker,
            company_name=None,  # Could fetch from stock universe
            screening_run_id=screening_run_id,
            strategies_flagged=red_flags["strategies_flagged"],
            metrics=metrics_dict,
            red_flags=[
                {
                    "metric": flag["metric"],
                    "reason": flag["reason"]
                }
                for flag in red_flags["red_flags"]
            ],
            financial_data=screening_result["financial_data"]
        )
        
        db.add(flagged_company)
        db.commit()
        
        logger.info(f"Saved flagged company: {ticker} ({len(red_flags['red_flags'])} red flags)")
        return True
    
    except Exception as e:
        logger.error(f"Error saving flagged company {screening_result.get('ticker')}: {e}")
        db.rollback()
        return False


def run_batch_screen(
    db: Session,
    batch_size: int = 5,
    delay_seconds: int = 60,
    limit: Optional[int] = None,
    enable_peer_comparison: bool = False,
    screening_run_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run batch screening on entire U.S. market
    
    Args:
        db: Database session
        batch_size: Number of stocks to process per batch
        delay_seconds: Delay between batches (for rate limiting)
        limit: Optional limit on total stocks to process
        enable_peer_comparison: Whether to enable peer comparison (much slower)
        screening_run_id: Optional ID of existing run record
    
    Returns:
        Dictionary with screening run statistics
    """
    start_time = datetime.now()
    
    if screening_run_id:
        screening_run = db.query(ScreeningRun).filter(ScreeningRun.id == screening_run_id).first()
        if not screening_run:
            logger.error(f"Screening run {screening_run_id} not found")
            return {"status": "failed", "error": "Run not found"}
        
        # Update status if needed
        if screening_run.status != "running":
            screening_run.status = "running"
            screening_run.run_date = start_time
            db.commit()
    else:
        # Create screening run record
        screening_run = ScreeningRun(
            run_date=start_time,
            strategies_run=["all"],
            status="running"
        )
        db.add(screening_run)
        db.commit()
        screening_run_id = screening_run.id
    
    try:
        # Get stock universe
        tickers = get_stock_universe(db, limit=limit)
        
        if not tickers:
            logger.warning("No tickers found in stock universe. Fetching from FMP...")
            fetch_and_save_us_stock_list(db)
            tickers = get_stock_universe(db, limit=limit)
        
        total_stocks = len(tickers)
        processed_count = 0
        flagged_count = 0
        error_count = 0
        
        logger.info(f"Starting batch screening of {total_stocks} stocks (batch size: {batch_size}, delay: {delay_seconds}s)")
        
        # Process in batches
        for i in range(0, total_stocks, batch_size):
            batch = tickers[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_stocks + batch_size - 1) // batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches}: {batch}")
            
            for ticker in batch:
                # Screen stock
                result = screen_single_stock(ticker, enable_peer_comparison)
                
                if result:
                    processed_count += 1
                    
                    # Save if flagged
                    if save_flagged_company(db, result, screening_run_id):
                        flagged_count += 1
                else:
                    error_count += 1
            
            # Update screening run progress
            screening_run.total_stocks_processed = processed_count
            screening_run.total_flagged = flagged_count
            db.commit()
            
            # Rate limiting delay (except for last batch)
            if i + batch_size < total_stocks:
                logger.info(f"Waiting {delay_seconds}s before next batch...")
                time.sleep(delay_seconds)
        
        # Update screening run as completed
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        screening_run.status = "completed"
        screening_run.total_stocks_processed = processed_count
        screening_run.total_flagged = flagged_count
        db.commit()
        
        summary = {
            "screening_run_id": screening_run_id,
            "status": "completed",
            "total_stocks": total_stocks,
            "processed": processed_count,
            "flagged": flagged_count,
            "errors": error_count,
            "duration_seconds": duration,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
        
        logger.info(f"Batch screening completed: {summary}")
        return summary
    
    except Exception as e:
        logger.error(f"Error in batch screening: {e}")
        
        # Update screening run as failed
        screening_run.status = "failed"
        screening_run.error_log = str(e)
        db.commit()
        
        return {
            "screening_run_id": screening_run_id,
            "status": "failed",
            "error": str(e)
        }
