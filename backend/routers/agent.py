from fastapi import APIRouter, HTTPException, Body, Depends
from services.agent import agent_service
from services.edgar_service import edgar_service
from typing import Optional
from routers.auth import get_current_user, verify_premium_access
import models
from schemas.agent import ReportRequest, CompanyAnalysisRequest

router = APIRouter()

@router.post("/generate_report")
async def generate_report(
    request: ReportRequest, 
    current_user: models.User = Depends(verify_premium_access)
):
    """
    Generate a report using the AI agent.
    """
    try:
        report = agent_service.generate_report(request.data_context, request.prompt_customization)
        return {"report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/10k/{ticker}")
async def get_10k_chunks(ticker: str):
    """
    Fetch the latest 10-K filing for a ticker.
    Returns the full 10-K document text without AI processing.
    """
    try:
        full_content = edgar_service.get_latest_10k_full(ticker)
        if not full_content:
            raise HTTPException(
                status_code=404,
                detail=f"Could not fetch 10-K filing for {ticker}. The company may not have filed a 10-K, or there was an error retrieving it."
            )
        return {"content": full_content, "ticker": ticker.upper()}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching 10-K for {ticker}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze_company")
async def analyze_company(
    request: CompanyAnalysisRequest,
    current_user: models.User = Depends(verify_premium_access)
):
    """
    Generate a comprehensive forensic business analysis based on the latest 10-K filing.
    """
    try:
        return agent_service.analyze_company(request.ticker, request.company_name, request.sector)
    except Exception as e:
        print(f"Error in analyze_company: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze_operating_drivers")
async def analyze_operating_drivers(
    request: CompanyAnalysisRequest,
    current_user: models.User = Depends(verify_premium_access)
):
    """
    Generate sector-specific operating drivers analysis.
    """
    try:
        return agent_service.analyze_operating_drivers(request.ticker, request.company_name, request.sector)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze_notes_disclosures")
async def analyze_notes_disclosures(
    request: CompanyAnalysisRequest,
    current_user: models.User = Depends(verify_premium_access)
):
    """
    Generate analysis of accounting policies, segment reporting, and risk factors.
    """
    try:
        return agent_service.analyze_notes_disclosures(request.ticker, request.company_name, request.sector)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze_capital_structure")
async def analyze_capital_structure(
    request: CompanyAnalysisRequest,
    current_user: models.User = Depends(verify_premium_access)
):
    """
    Generate comprehensive cash flow analysis based on financial statements.
    """
    try:
        return agent_service.analyze_capital_structure(request.ticker, request.company_name, request.sector)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/clear_cache/{ticker}")
async def clear_analysis_cache(ticker: str):
    """
    Clear all cached analyses for a specific ticker.
    """
    try:
        agent_service.clear_cache_for_ticker(ticker)
        return {"message": f"Cache cleared for {ticker.upper()}", "ticker": ticker.upper()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cache_status/{ticker}")
async def get_cache_status(ticker: str):
    """
    Get cache status for all analysis types for a ticker.
    """
    try:
        status = agent_service.get_cache_status(ticker)
        return {"ticker": ticker.upper(), "cache_status": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
