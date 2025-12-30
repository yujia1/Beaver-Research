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
        report = await agent_service.generate_report(request.data_context, request.prompt_customization)
        return {"report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


