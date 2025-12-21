from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel
from database import get_db
from models import SystemConfig, User
from routers.auth import get_current_user

router = APIRouter()

class SchedulerConfig(BaseModel):
    enabled: bool
    processing_delay_days: int

@router.get("/config", response_model=SchedulerConfig)
def get_scheduler_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    enabled_config = db.query(SystemConfig).filter(SystemConfig.key == "13f_scheduler_enabled").first()
    delay_config = db.query(SystemConfig).filter(SystemConfig.key == "13f_processing_delay_days").first()
    
    return {
        "enabled": enabled_config.value.lower() == "true" if enabled_config else True,
        "processing_delay_days": int(delay_config.value) if delay_config else 3
    }

@router.post("/config", response_model=SchedulerConfig)
def update_scheduler_config(
    config: SchedulerConfig,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Update enabled status
    enabled_config = db.query(SystemConfig).filter(SystemConfig.key == "13f_scheduler_enabled").first()
    if not enabled_config:
        enabled_config = SystemConfig(key="13f_scheduler_enabled", value=str(config.enabled).lower(), description="Enable/Disable 13F Scheduler")
        db.add(enabled_config)
    else:
        enabled_config.value = str(config.enabled).lower()
        
    # Update delay days
    delay_config = db.query(SystemConfig).filter(SystemConfig.key == "13f_processing_delay_days").first()
    if not delay_config:
        delay_config = SystemConfig(key="13f_processing_delay_days", value=str(config.processing_delay_days), description="Days to wait after quarter end")
        db.add(delay_config)
    else:
        delay_config.value = str(config.processing_delay_days)
    
    db.commit()
    
    return config
