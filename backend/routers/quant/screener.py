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
    BatchScreenRequest,
    BatchScreenStatus,
    FlaggedCompanyResponse,
    StockUniverseUpdate,
    LayeredScreenerResult
)
from services.market.fmp_financial_service import (
    save_stock_universe_to_db,
    FMPAPIError
)
from services.market.fmp_layered_screener import run_layered_screener

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Helper Functions
# ============================================================================

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
# Layered Screener Endpoints
# ============================================================================

@router.get("/fmp-layered/{ticker}", response_model=LayeredScreenerResult)
async def get_fmp_layered_screener(
    ticker: str,
    limit: int = Query(default=5, ge=1, le=10),
    period: str = Query(default="FY"),
):
    """
    Run the 4-layer FMP key-metrics driven screener for a single ticker.
    Layers: Survival Filter → Earnings Quality → Structural Health → Valuation
    """
    try:
        result = run_layered_screener(ticker, limit=limit, period=period)
        eq_raw  = result.get("earnings_quality", {})
        sh_raw  = result.get("structural_health", {})
        val_raw = result.get("valuation", {})
        sf_raw  = result.get("survival_filter", {})

        return LayeredScreenerResult(
            ticker=result.get("ticker"),
            survival_filter={
                "checks":      sf_raw.get("checks", []),
                "top_reasons": sf_raw.get("top_reasons", []),
                "notes":       [],
                "yearly":      sf_raw.get("yearly", []),
            },
            earnings_quality={
                "checks": eq_raw.get("checks", []),
                "notes":  eq_raw.get("red_flags", []),
                "yearly": eq_raw.get("yearly", []),
            },
            structural_health={
                "checks": sh_raw.get("checks", []),
                "notes":  sh_raw.get("notes", []),
                "yearly": sh_raw.get("yearly", []),
            },
            valuation={
                "checks": val_raw.get("checks", []),
                "notes":  val_raw.get("notes", []),
                "yearly": val_raw.get("yearly", []),
            },
            thesis=result.get("thesis", []),
            invalidate_conditions=result.get("invalidate_conditions", []),
            action=result.get("action", {}),
            raw_key_metrics_row=result.get("raw_key_metrics_row")
        )
    except Exception as e:
        logger.error(f"Error running layered screener for {ticker}: {e}")
        # Return user-friendly message; FMPAPIError already has sanitized messages
        user_msg = str(e) if isinstance(e, FMPAPIError) else f"Failed to screen {ticker}. Please try again later."
        raise HTTPException(status_code=500, detail=user_msg)


@router.post("/fmp-layered/flagged", response_model=FlaggedCompanyResponse)
async def save_fmp_layered_result(
    layered: LayeredScreenerResult,
    db: Session = Depends(get_db)
):
    """
    Accept a full layered screener result and persist it as a FlaggedCompany record.
    Derives strategies_flagged and red_flags from layered notes/survival reasons.
    """
    try:
        ticker = layered.ticker.upper()

        strategies_flagged = []
        red_flags = []

        # Helper to check if any yearly row is flagged
        def _has_yearly_flags(layer) -> bool:
            if not layer or not layer.yearly:
                return False
            return any(row.get("is_red_flag") for row in layer.yearly)

        # --- Survival Filter ---
        sf = layered.survival_filter
        if sf:
            sf_reasons = sf.top_reasons or []
            sf_has_flags = bool(sf_reasons) or _has_yearly_flags(sf)
            if sf_has_flags:
                strategies_flagged.append("Survival Filter")
            for r in sf_reasons:
                red_flags.append({"category": "Survival Filter", "note": r})
            # Also add per-row flag reasons from yearly data
            for row in (sf.yearly or []):
                if row.get("is_red_flag"):
                    year = row.get("year", "?")
                    reasons = []
                    if row.get("current_ratio_pass") is False:
                        reasons.append(f"Current Ratio={row.get('current_ratio', 'N/A')}")
                    if row.get("interest_burden_pass") is False:
                        reasons.append(f"Interest Burden={row.get('interest_burden', 'N/A')}")
                    if row.get("net_debt_pass") is False:
                        reasons.append(f"Net Debt/EBITDA={row.get('net_debt_to_ebitda', 'N/A')}")
                    if row.get("fcf_pass") is False:
                        reasons.append(f"FCF={row.get('fcf', 'N/A')}")
                    if reasons:
                        red_flags.append({"category": "Survival Filter", "note": f"{year}: {', '.join(reasons)}"})

        # --- Earnings Quality ---
        eq = layered.earnings_quality
        if eq:
            eq_notes = eq.notes or []
            eq_has_flags = bool(eq_notes) or _has_yearly_flags(eq)
            if eq_has_flags:
                strategies_flagged.append("Earnings Quality")
            for n in eq_notes:
                red_flags.append({"category": "Earnings Quality", "note": n})
            for row in (eq.yearly or []):
                if row.get("is_red_flag"):
                    year = row.get("year", "?")
                    reasons = []
                    if row.get("cfo_to_ni_pass") is False:
                        reasons.append(f"CFO/NI={row.get('cfo_to_ni', 'N/A')}")
                    if row.get("fcf_to_ni_pass") is False:
                        reasons.append(f"FCF/NI={row.get('fcf_to_ni', 'N/A')}")
                    if reasons:
                        red_flags.append({"category": "Earnings Quality", "note": f"{year}: {', '.join(reasons)}"})

        # --- Structural Health ---
        sh = layered.structural_health
        if sh:
            sh_notes = sh.notes or []
            sh_has_flags = bool(sh_notes) or _has_yearly_flags(sh)
            if sh_has_flags:
                strategies_flagged.append("Structural Health")
            for n in sh_notes:
                red_flags.append({"category": "Structural Health", "note": n})
            for row in (sh.yearly or []):
                if row.get("is_red_flag"):
                    year = row.get("year", "?")
                    spread = row.get("roic_spread")
                    note = f"{year}: Negative ROIC spread={spread}" if spread is not None else f"{year}: Red flag"
                    red_flags.append({"category": "Structural Health", "note": note})

        # --- Valuation ---
        val = layered.valuation
        if val:
            val_notes = val.notes or []
            val_has_flags = bool(val_notes) or _has_yearly_flags(val)
            if val_has_flags:
                strategies_flagged.append("Valuation")
            for n in val_notes:
                red_flags.append({"category": "Valuation", "note": n})
            for row in (val.yearly or []):
                if row.get("is_red_flag"):
                    year = row.get("year", "?")
                    fcf_yield = row.get("fcf_yield")
                    note = f"{year}: Low FCF yield={fcf_yield}" if fcf_yield is not None else f"{year}: Red flag"
                    red_flags.append({"category": "Valuation", "note": note})

        metrics_json = layered.dict()

        stock = db.query(StockUniverse).filter(StockUniverse.ticker == ticker).first()
        company_name = stock.company_name if stock else None

        flagged_company = FlaggedCompany(
            ticker=ticker,
            company_name=company_name,
            screening_date=datetime.utcnow(),
            strategies_flagged=strategies_flagged or [],
            metrics=metrics_json,
            red_flags=red_flags or []
        )

        db.add(flagged_company)
        db.commit()
        db.refresh(flagged_company)

        return flagged_company

    except Exception as e:
        logger.error(f"Error saving layered result for {layered.ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save flagged company {layered.ticker}. Please try again.")


# ============================================================================
# Flagged Companies Endpoints
# ============================================================================

@router.get("/flagged", response_model=List[FlaggedCompanyResponse])
async def get_flagged_companies(
    strategy: Optional[str] = Query(default=None),
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0),
    db: Session = Depends(get_db)
):
    """
    Get companies flagged by screening criteria.

    Args:
        strategy: Filter by strategy name (optional)
        limit: Maximum number of results
        offset: Pagination offset
    """
    query = db.query(FlaggedCompany)

    if strategy:
        query = query.filter(FlaggedCompany.strategies_flagged.contains([strategy]))

    query = query.order_by(FlaggedCompany.screening_date.desc())
    flagged_companies = query.offset(offset).limit(limit).all()

    response_list = []
    for company in flagged_companies:
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
# Batch Screening Endpoints
# ============================================================================

@router.post("/batch-screen", response_model=BatchScreenStatus)
async def batch_screen_us_market(
    request: BatchScreenRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Trigger batch screening of the entire U.S. market as a background job.
    """
    screening_run = ScreeningRun(
        strategies_run=request.strategies,
        status="running",
        total_stocks_processed=0,
        total_flagged=0
    )
    db.add(screening_run)
    db.commit()
    db.refresh(screening_run)

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
    Get status of a batch screening run.
    """
    screening_run = db.query(ScreeningRun).filter(ScreeningRun.id == run_id).first()

    if not screening_run:
        raise HTTPException(status_code=404, detail="Screening run not found")

    return BatchScreenStatus(
        run_id=screening_run.id,
        status=screening_run.status,
        total_stocks=screening_run.target_total_stocks,
        processed_stocks=screening_run.total_stocks_processed,
        flagged_stocks=screening_run.total_flagged,
        started_at=screening_run.run_date,
        completed_at=screening_run.completed_at if hasattr(screening_run, 'completed_at') else None,
        error_message=screening_run.error_log
    )


@router.get("/runs", response_model=List[BatchScreenStatus])
async def get_screening_runs(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get history of batch screening runs.
    """
    runs = db.query(ScreeningRun).order_by(ScreeningRun.run_date.desc()).offset(offset).limit(limit).all()

    return [
        BatchScreenStatus(
            run_id=run.id,
            status=run.status,
            total_stocks=run.target_total_stocks,
            processed_stocks=run.total_stocks_processed,
            flagged_stocks=run.total_flagged,
            started_at=run.run_date,
            completed_at=None,
            error_message=run.error_log
        )
        for run in runs
    ]


@router.post("/batch-stop/{run_id}", response_model=BatchScreenStatus)
async def stop_batch_screen(
    run_id: int,
    db: Session = Depends(get_db)
):
    """
    Stop a running batch screening job.
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
        total_stocks=run.target_total_stocks,
        processed_stocks=run.total_stocks_processed,
        flagged_stocks=run.total_flagged,
        started_at=run.run_date,
        completed_at=None,
        error_message=run.error_log
    )


# ============================================================================
# Stock Universe Endpoints
# ============================================================================

@router.post("/update-stock-universe", response_model=StockUniverseUpdate)
async def update_stock_universe(
    db: Session = Depends(get_db)
):
    """
    Update the stock universe cache from FMP API.
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
        raise HTTPException(status_code=500, detail="Failed to update stock universe. Please try again later.")


@router.get("/stock-universe/count")
async def get_stock_universe_count(
    db: Session = Depends(get_db)
):
    """Get count of active stocks in the universe."""
    count = db.query(StockUniverse).filter(StockUniverse.is_active == True).count()
    return {"count": count}
