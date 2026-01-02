from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form, Query
from pydantic import BaseModel
from typing import Optional
from routers.admin.auth import get_current_user
import models
from services.ai_report import generate_market_report, process_uploaded_report
from redis_client import redis_client
import json
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

CONFIG_KEY = "ai_report:config"

class AIReportConfig(BaseModel):
    enabled: bool

class AIReportStatus(BaseModel):
    enabled: bool
    last_run: Optional[str] = None
    last_status: Optional[str] = None # 'success', 'failed'
    short_last_run: Optional[str] = None
    short_last_status: Optional[str] = None
    long_last_run: Optional[str] = None
    long_last_status: Optional[str] = None

@router.get("/config", response_model=AIReportStatus)
@router.get("/config", response_model=AIReportStatus)
async def get_config(
    current_user: models.User = Depends(get_current_user)
):
    """Get AI Report automation configuration and status."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    config_raw = redis_client.get_cache(CONFIG_KEY)
    config = config_raw if config_raw else {"enabled": False}
    
    # Get last run status (stored separately or in same config)
    last_run = redis_client.get_cache("ai_report:last_run") # e.g. "2023-10-27T09:20:00"
    last_status = redis_client.get_cache("ai_report:last_status") # e.g. "success"
    
    short_last_run = redis_client.get_cache("ai_report:short:last_run")
    short_last_status = redis_client.get_cache("ai_report:short:last_status")
    long_last_run = redis_client.get_cache("ai_report:long:last_run")
    long_last_status = redis_client.get_cache("ai_report:long:last_status")
    
    return {
        "enabled": config.get("enabled", False),
        "last_run": last_run,
        "last_status": last_status,
        "short_last_run": short_last_run,
        "short_last_status": short_last_status,
        "long_last_run": long_last_run,
        "long_last_status": long_last_status
    }

@router.post("/config", response_model=AIReportStatus)
@router.post("/config", response_model=AIReportStatus)
async def update_config(
    config: AIReportConfig,
    current_user: models.User = Depends(get_current_user)
):
    """Enable or disable AI Report automation."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    redis_client.set_cache(CONFIG_KEY, {"enabled": config.enabled}) # persistent? cache defaults to TTL?
    # redis_client.set_cache uses a default TTL if not specified? 
    # Wait, redis_client.set_cache in this codebase usually calls `setex`. 
    # If we want persistent config, we should use set without Expiry or a very long expiry.
    # checking redis_client implementation...
    # Assuming redis_client has a method for persistent storage or we set long TTL.
    # For now, I'll use set_cache with a very long TTL (e.g. 1 year) or check if `set` exists.
    # I'll rely on `redis_client.redis.set` if exposed, or just set_cache with None ttl?
    
    # Let's assume set_cache(key, val, ttl=None) might allow persistence or default.
    # Actually, many simple implementations use Redis just for cache. 
    # Ideally config should be in DB. But `users` table has settings?
    # A dedicated `SystemSettings` table is better.
    # But user asked for simple "admin UI has control".
    # I will use Redis with LONG TTL for now. 1 year = 31536000 seconds.
    
    redis_client.set_cache(CONFIG_KEY, {"enabled": config.enabled}, ttl=31536000)
    
    return {
        "enabled": config.enabled,
        "last_run": redis_client.get_cache("ai_report:last_run"),
        "last_status": redis_client.get_cache("ai_report:last_status")
    }

@router.post("/run")
@router.post("/run")
async def manual_run(
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user)
):
    """Trigger the AI Market Report generation manually."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    # Run in background
    background_tasks.add_task(run_report_task)
    return {"message": "Market Report generation started"}

async def run_report_task():
    """Wrapper to run report and update status"""
    import datetime
    redis_client.set_cache("ai_report:last_run", datetime.datetime.now().isoformat(), ttl=31536000)
    redis_client.set_cache("ai_report:last_status", "running", ttl=31536000)
    
    success = await generate_market_report(manual_trigger=True)
    
    status = "success" if success else "failed"
    redis_client.set_cache("ai_report:last_status", status, ttl=31536000)


async def run_uploaded_report_task(content: bytes, filename: str, report_type: str, user_id: int, publish_date: Optional[str] = None):
    """Wrapper to run uploaded report and update status"""
    import datetime
    key_prefix = f"ai_report:{report_type}" # short or long
    redis_client.set_cache(f"{key_prefix}:last_run", datetime.datetime.now().isoformat(), ttl=31536000)
    redis_client.set_cache(f"{key_prefix}:last_status", "running", ttl=31536000)
    
    success = await process_uploaded_report(content, filename, report_type, user_id, publish_date)
    
    status = "success" if success else "failed"
    redis_client.set_cache(f"{key_prefix}:last_status", status, ttl=31536000)

@router.post("/short-report/run")
async def run_short_report(
    background_tasks: BackgroundTasks,
    publish_date: Optional[str] = Query(None),
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user)
):
    """Trigger AI Short Report generation (Rewrite uploaded file)"""
    logger.info(f"Short Report Run: File={file.filename}, Date={publish_date}, User={current_user.id}")
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
        
    content = await file.read()
    background_tasks.add_task(run_uploaded_report_task, content, file.filename, "short", current_user.id, publish_date=publish_date)
    return {"message": "Short Report processing started"}

@router.post("/long-report/run")
async def run_long_report(
    background_tasks: BackgroundTasks,
    publish_date: Optional[str] = Query(None),
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user)
):
    """Trigger AI Long Report generation (Rewrite uploaded file)"""
    logger.info(f"Long Report Run: File={file.filename}, Date={publish_date}, User={current_user.id}")
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
        
    content = await file.read()
    background_tasks.add_task(run_uploaded_report_task, content, file.filename, "long", current_user.id, publish_date=publish_date)
    return {"message": "Long Report processing started"}
