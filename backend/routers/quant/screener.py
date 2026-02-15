"""
Stock Screener API Router

Provides endpoints for quantitative stock screening based on financial metrics.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from database import get_db, SessionLocal
from models import StockUniverse, FlaggedCompany, ScreeningRun
from schemas.screener_schemas import (
    ScreenerCriteria,
    ScreenerResult,
    StockMetrics,
    MetricData,
    TrendData,
    RedFlagSummary,
    BatchScreenRequest,
    BatchScreenStatus,
    FlaggedCompanyResponse,
    FlaggedStockRequest,
    FlaggedCompaniesFilter,
    PeerComparisonRequest,
    PeerComparisonResult,
    StockUniverseUpdate
)
from services.market.fmp_financial_service import (
    fetch_all_financial_statements,
    fetch_stock_quote,
    save_stock_universe_to_db,
    FMPAPIError
)
from services.market.screener_calculator import (
    calculate_all_metrics,
    check_red_flags,
    MetricResult
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Helper Functions
# ============================================================================

def metric_result_to_schema(metric: MetricResult) -> MetricData:
    """Convert MetricResult dataclass to Pydantic schema"""
    trend_data = None
    if metric.trend:
        trend_data = TrendData(
            values=metric.trend.values,
            years=metric.trend.years,
            slope=metric.trend.slope,
            direction=metric.trend.direction,
            latest_value=metric.trend.latest_value
        )
    
    return MetricData(
        name=metric.name,
        latest_value=metric.latest_value,
        trend=trend_data,
        is_red_flag=metric.is_red_flag,
        red_flag_reason=metric.red_flag_reason
    )


def execute_batch_screen_background(
    run_id: int,
    batch_size: int,
    delay_seconds: int,
    limit: Optional[int],
    enable_peer_comparison: bool
):
    """
    Execute batch screening in background with a dedicated DB session
    """
    db = SessionLocal()
    try:
        from services.market.batch_screener import run_batch_screen
        logger.info(f"Starting background batch screen for run {run_id}")
        run_batch_screen(
            db=db,
            batch_size=batch_size,
            delay_seconds=delay_seconds, 
            limit=limit,
            enable_peer_comparison=enable_peer_comparison,
            screening_run_id=run_id
        )
        logger.info(f"Completed background batch screen for run {run_id}")
    except Exception as e:
        logger.error(f"Background batch screen failed: {e}")
        # Try to update status if possible
        try:
            run = db.query(ScreeningRun).filter(ScreeningRun.id == run_id).first()
            if run:
                run.status = "failed"
                run.error_log = f"Background task error: {str(e)}"
                db.commit()
        except:
            pass
    finally:
        db.close()


# ============================================================================
# Screening Endpoints
# ============================================================================

@router.post("/screen", response_model=List[ScreenerResult])
async def screen_stocks(
    criteria: ScreenerCriteria,
    db: Session = Depends(get_db)
):
    """
    Screen multiple stocks based on criteria
    
    Args:
        criteria: Screening criteria (tickers, strategies, years)
    
    Returns:
        List of screening results
    """
    results = []
    
    for ticker in criteria.tickers:
        try:
            # Fetch financial statements
            logger.info(f"Screening {ticker}")
            financial_data = fetch_all_financial_statements(ticker, criteria.years)
            
            # Get current price for EV calculation
            try:
                quote = fetch_stock_quote(ticker)
                current_price = quote.get("price", 0)
            except:
                current_price = None
            
            # Calculate metrics
            result = calculate_all_metrics(
                income_data=financial_data["income"],
                cash_flow_data=financial_data["cashflow"],
                balance_sheet_data=financial_data["balance"],
                current_price=current_price
            )
            
            metrics = result["metrics"]
            cash_flow_yearly_breakdown = result.get("cash_flow_yearly_breakdown", [])
            balance_sheet_yearly_breakdown = result.get("balance_sheet_yearly_breakdown", [])
            working_capital_yearly_breakdown = result.get("working_capital_yearly_breakdown", [])
            valuation_yearly_breakdown = result.get("valuation_yearly_breakdown", [])
            
            # Convert to schema
            metrics_schema = {
                key: metric_result_to_schema(value)
                for key, value in metrics.items()
            }
            
            # Check red flags
            red_flag_summary = check_red_flags(metrics)
            
            results.append(ScreenerResult(
                ticker=ticker,
                company_name=None,  # TODO: Get from stock universe
                metrics=metrics_schema,
                cash_flow_yearly_breakdown=cash_flow_yearly_breakdown,
                balance_sheet_yearly_breakdown=balance_sheet_yearly_breakdown,
                working_capital_yearly_breakdown=working_capital_yearly_breakdown,
                valuation_yearly_breakdown=valuation_yearly_breakdown,
                red_flag_summary=RedFlagSummary(**red_flag_summary),
                screened_at=datetime.utcnow()
            ))
        
        except FMPAPIError as e:
            logger.error(f"FMP API error for {ticker}: {e}")
            raise HTTPException(status_code=502, detail=f"FMP API error: {str(e)}")
        except Exception as e:
            logger.error(f"Error screening {ticker}: {e}")
            raise HTTPException(status_code=500, detail=f"Error screening {ticker}: {str(e)}")
    
    return results


@router.get("/metrics/{ticker}", response_model=StockMetrics)
async def get_stock_metrics(
    ticker: str,
    years: int = Query(default=10, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Get all screening metrics for a single stock
    
    Args:
        ticker: Stock ticker symbol
        years: Number of years of data (default: 5)
    
    Returns:
        StockMetrics with all calculated metrics
    """
    try:
        # Fetch financial statements
        financial_data = fetch_all_financial_statements(ticker, years)
        
        # Get current price
        try:
            quote = fetch_stock_quote(ticker)
            current_price = quote.get("price", 0)
        except:
            current_price = None
        
        # Calculate metrics
        result = calculate_all_metrics(
            income_data=financial_data["income"],
            cash_flow_data=financial_data["cashflow"],
            balance_sheet_data=financial_data["balance"],
            current_price=current_price
        )
        metrics = result["metrics"]
        
        # Check red flags
        red_flag_summary = check_red_flags(metrics)
        
        # Get company name from stock universe
        stock = db.query(StockUniverse).filter(StockUniverse.ticker == ticker).first()
        company_name = stock.company_name if stock else None
        
        return StockMetrics(
            ticker=ticker,
            company_name=company_name,
            fcf_to_dividends_buybacks=metric_result_to_schema(metrics.get("fcf_to_dividends_buybacks")) if "fcf_to_dividends_buybacks" in metrics else None,
            fcf_to_revenue=metric_result_to_schema(metrics.get("fcf_to_revenue")) if "fcf_to_revenue" in metrics else None,
            net_debt_to_ebitda=metric_result_to_schema(metrics.get("net_debt_to_ebitda")) if "net_debt_to_ebitda" in metrics else None,
            capitalized_costs_to_revenue=metric_result_to_schema(metrics.get("capitalized_costs_to_revenue")) if "capitalized_costs_to_revenue" in metrics else None,
            days_sales_outstanding=metric_result_to_schema(metrics.get("days_sales_outstanding")) if "days_sales_outstanding" in metrics else None,
            ev_to_ebitda=metric_result_to_schema(metrics.get("ev_to_ebitda")) if "ev_to_ebitda" in metrics else None,
            red_flag_summary=RedFlagSummary(**red_flag_summary),
            calculated_at=datetime.utcnow(),
            data_years=years
        )
    
    except FMPAPIError as e:
        logger.error(f"FMP API error for {ticker}: {e}")
        raise HTTPException(status_code=502, detail=f"FMP API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting metrics for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ============================================================================
# Batch Screening Endpoints
# ============================================================================

@router.post("/batch-screen", response_model=BatchScreenStatus)
async def batch_screen_us_market(
    request: BatchScreenRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Trigger batch screening of entire U.S. market (background job)
    
    Args:
        request: Batch screening request
        background_tasks: FastAPI background tasks
    
    Returns:
        BatchScreenStatus with job information
    """
    # Create screening run record
    screening_run = ScreeningRun(
        strategies_run=request.strategies,
        status="running",
        total_stocks_processed=0,
        total_flagged=0
    )
    db.add(screening_run)
    db.commit()
    db.refresh(screening_run)
    
    # Trigger background task
    background_tasks.add_task(
        execute_batch_screen_background,
        run_id=screening_run.id,
        batch_size=request.batch_size,
        delay_seconds=request.delay_seconds,
        limit=request.limit,
        enable_peer_comparison=request.enable_peer_comparison
    )
    
    logger.info(f"Batch screening queued: run_id={screening_run.id}")
    
    return BatchScreenStatus(
        run_id=screening_run.id,
        status=screening_run.status,
        total_stocks=screening_run.total_stocks_processed,
        processed_stocks=screening_run.total_stocks_processed,
        flagged_stocks=screening_run.total_flagged,
        started_at=screening_run.run_date,
        completed_at=None,
        estimated_completion=None
    )


@router.get("/batch-status/{run_id}", response_model=BatchScreenStatus)
async def get_batch_status(
    run_id: int,
    db: Session = Depends(get_db)
):
    """
    Get status of batch screening run
    
    Args:
        run_id: Screening run ID
    
    Returns:
        BatchScreenStatus
    """
    screening_run = db.query(ScreeningRun).filter(ScreeningRun.id == run_id).first()
    
    if not screening_run:
        raise HTTPException(status_code=404, detail="Screening run not found")
    
    return BatchScreenStatus(
        run_id=screening_run.id,
        status=screening_run.status,
        total_stocks=screening_run.total_stocks_processed,
        processed_stocks=screening_run.total_stocks_processed,
        flagged_stocks=screening_run.total_flagged,
        started_at=screening_run.run_date,
        completed_at=screening_run.completed_at if hasattr(screening_run, 'completed_at') else None, # ScreeningRun model might not have completed_at? Let's check.
        error_message=screening_run.error_log
    )


@router.get("/runs", response_model=List[BatchScreenStatus])
async def get_screening_runs(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get history of batch screening runs
    """
    runs = db.query(ScreeningRun).order_by(ScreeningRun.run_date.desc()).offset(offset).limit(limit).all()
    
    return [
        BatchScreenStatus(
            run_id=run.id,
            status=run.status,
            total_stocks=run.total_stocks_processed,
            processed_stocks=run.total_stocks_processed,
            flagged_stocks=run.total_flagged,
            started_at=run.run_date,
            completed_at=None, # ScreeningRun likely doesn't have completed_at based on plan, using None or we'd need to add column
            error_message=run.error_log
        )
        for run in runs
    ]


# ============================================================================
# Flagged Companies Endpoints
# ============================================================================

@router.post("/flagged", response_model=FlaggedCompanyResponse)
async def flag_company_manually(
    request: FlaggedStockRequest,
    db: Session = Depends(get_db)
):
    """
    Manually flag a company.
    Calculates metrics and stores them in the flagged_companies table.
    """
    ticker = request.ticker.upper()
    
    # 1. Fetch financial data
    try:
        financial_data = fetch_all_financial_statements(ticker)
        income_data = financial_data.get("income", [])
        balance_sheet_data = financial_data.get("balance", [])
        cash_flow_data = financial_data.get("cashflow", [])
        
        quote = fetch_stock_quote(ticker)
        current_price = quote.get("price")
        company_name = quote.get("name")
        
    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {e}")
        raise HTTPException(status_code=400, detail=f"Error fetching data for {ticker}: {str(e)}")
        
    # 2. Calculate Metrics
    try:
        metrics_result = calculate_all_metrics(
            income_data,
            cash_flow_data,
            balance_sheet_data,
            current_price,
            ticker=ticker
        )
        
        metrics = metrics_result["metrics"]
    
    except Exception as e:
        logger.error(f"Error calculating metrics for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating metrics: {str(e)}")
        
    # 3. Check Red Flags
    red_flag_summary = check_red_flags(metrics)
    
    # 4. Prepare for DB
    metrics_schema = {
        key: metric_result_to_schema(value)
        for key, value in metrics.items()
    }
    
    # Convert to JSON-friendly dicts
    metrics_json = {k: v.dict() for k, v in metrics_schema.items()}
    
    # Extract red flags list from summary to match schema (List[Dict])
    # The schema FlaggedCompanyResponse expects red_flags to be List[Dict]
    # check_red_flags returns a summary Dict that contains "red_flags" list
    red_flags_list = red_flag_summary.get("red_flags", [])
    
    strategies_flagged = request.strategies or []
    if not strategies_flagged and red_flag_summary.get("total_flags", 0) > 0:
        strategies_flagged = list(red_flag_summary.get("flags_by_category", {}).keys())

    # Ensure company_name is set (fallback to StockUniverse if quote missing)
    if not company_name:
        stock_u = db.query(StockUniverse).filter(StockUniverse.ticker == ticker).first()
        if stock_u:
            company_name = stock_u.company_name

    # Create or Update FlaggedCompany
    existing_company = db.query(FlaggedCompany).filter(FlaggedCompany.ticker == ticker).first()
    
    if existing_company:
        # Update existing record
        existing_company.company_name = company_name
        existing_company.screening_date = datetime.utcnow()
        existing_company.strategies_flagged = strategies_flagged
        existing_company.metrics = metrics_json
        existing_company.red_flags = red_flags_list
        # existing_company.sector = ... # if available
        flagged_company = existing_company
    else:
        # Create new record
        flagged_company = FlaggedCompany(
            ticker=ticker,
            company_name=company_name,
            screening_date=datetime.utcnow(), 
            strategies_flagged=strategies_flagged,
            metrics=metrics_json,
            red_flags=red_flags_list # Store as List[Dict]
        )
        db.add(flagged_company)
    
    db.commit()
    db.refresh(flagged_company)
    
    return flagged_company


@router.get("/flagged", response_model=List[FlaggedCompanyResponse])
async def get_flagged_companies(
    strategy: Optional[str] = Query(default=None),
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0),
    db: Session = Depends(get_db)
):
    """
    Get companies flagged by screening criteria
    
    Args:
        strategy: Filter by strategy (optional)
        limit: Maximum number of results
        offset: Offset for pagination
    
    Returns:
        List of flagged companies
    """
    query = db.query(FlaggedCompany)
    
    # Filter by strategy if provided
    if strategy:
        # Filter companies that have this strategy in their strategies_flagged list
        query = query.filter(FlaggedCompany.strategies_flagged.contains([strategy]))
    
    # Order by screening date (most recent first)
    query = query.order_by(FlaggedCompany.screening_date.desc())
    
    # Pagination
    flagged_companies = query.offset(offset).limit(limit).all()
    
    response_list = []
    for company in flagged_companies:
        # Handle legacy formatting where red_flags might be stored as a dict (summary) instead of list
        red_flags_data = company.red_flags
        if isinstance(red_flags_data, dict):
            red_flags_data = red_flags_data.get("red_flags", [])
            
        response_list.append(
            FlaggedCompanyResponse(
                id=company.id,
                ticker=company.ticker,
                company_name=company.company_name,
                sector=company.sector,
                screening_date=company.screening_date,
                strategies_flagged=company.strategies_flagged,
                metrics=company.metrics,
                red_flags=red_flags_data or []
            )
        )
            
    return response_list


# ============================================================================
# Stock Universe Endpoints
# ============================================================================

@router.post("/update-stock-universe", response_model=StockUniverseUpdate)
async def update_stock_universe(
    db: Session = Depends(get_db)
):
    """
    Update stock universe from FMP API
    
    Returns:
        StockUniverseUpdate with statistics
    """
    try:
        result = save_stock_universe_to_db(db)
        
        total_stocks = db.query(StockUniverse).count()
        
        return StockUniverseUpdate(
            total_stocks=total_stocks,
            new_stocks=result["saved"],
            updated_stocks=result["updated"],
            updated_at=datetime.utcnow()
        )
    
    except Exception as e:
        logger.error(f"Error updating stock universe: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/stock-universe/count")
async def get_stock_universe_count(
    db: Session = Depends(get_db)
):
    """Get count of stocks in universe"""
    count = db.query(StockUniverse).filter(StockUniverse.is_active == True).count()
    return {"count": count}

@router.post("/batch-stop/{run_id}", response_model=BatchScreenStatus)
async def stop_batch_screen(
    run_id: int,
    db: Session = Depends(get_db)
):
    """
    Stop a running batch screening job
    """
    run = db.query(ScreeningRun).filter(ScreeningRun.id == run_id).first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Screening run not found")
    
    if run.status == "running":
        run.status = "stopped"
        db.commit()
        db.refresh(run)
        logger.info(f"Batch screening run {run_id} stopped by user")
    
    return BatchScreenStatus(
        run_id=run.id,
        status=run.status,
        total_stocks=run.total_stocks_processed,
        processed_stocks=run.total_stocks_processed,
        flagged_stocks=run.total_flagged,
        started_at=run.run_date,
        completed_at=None,
        error_message=run.error_log
    )
