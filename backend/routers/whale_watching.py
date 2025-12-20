"""
Whale Watching API Router
Provides endpoints for tracking institutional position changes from 13F filings
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from routers.auth import get_current_user
import models

router = APIRouter()


@router.get("/summary")
async def get_whale_watching_summary(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get summary statistics for whale watching alerts"""
    try:
        # Count total alerts
        total_alerts = db.query(models.WhaleAlert).count()
        
        # Count unread alerts
        unread_alerts = db.query(models.WhaleAlert).filter(
            models.WhaleAlert.is_read == False
        ).count()
        
        # Count high severity unread alerts
        high_severity_unread = db.query(models.WhaleAlert).filter(
            models.WhaleAlert.is_read == False,
            models.WhaleAlert.severity == "HIGH"
        ).count()
        
        # Count whale position changes
        whale_position_changes = db.query(models.PositionChange).filter(
            models.PositionChange.is_whale == True
        ).count()
        
        # Count total position changes
        total_position_changes = db.query(models.PositionChange).count()
        
        return {
            "total_alerts": total_alerts,
            "unread_alerts": unread_alerts,
            "high_severity_unread": high_severity_unread,
            "whale_position_changes": whale_position_changes,
            "total_position_changes": total_position_changes
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching summary: {str(e)}")


@router.get("/alerts")
async def get_whale_alerts(
    ticker: Optional[str] = Query(None, description="Filter by ticker symbol"),
    severity: Optional[str] = Query(None, description="Filter by severity (HIGH, MEDIUM, LOW)"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of alerts to return"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get whale watching alerts with optional filters"""
    try:
        query = db.query(models.WhaleAlert)
        
        # Apply filters
        if ticker:
            query = query.filter(models.WhaleAlert.ticker == ticker.upper())
        
        if severity:
            query = query.filter(models.WhaleAlert.severity == severity.upper())
        
        # Order by created_at descending (most recent first)
        query = query.order_by(models.WhaleAlert.created_at.desc())
        
        # Limit results
        alerts = query.limit(limit).all()
        
        # Convert to dict for JSON response
        result = []
        for alert in alerts:
            result.append({
                "id": alert.id,
                "ticker": alert.ticker,
                "institution_name": alert.institution_name,
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "message": alert.message,
                "quarter": alert.quarter,
                "percent_change": alert.percent_change,
                "shares_change": alert.shares_change,
                "value_change": alert.value_change,
                "is_read": alert.is_read,
                "created_at": alert.created_at.isoformat() if alert.created_at else None
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching alerts: {str(e)}")


@router.get("/position-changes")
async def get_position_changes(
    ticker: Optional[str] = Query(None, description="Filter by ticker symbol"),
    cik: Optional[str] = Query(None, description="Filter by institution CIK"),
    change_type: Optional[str] = Query(None, description="Filter by change type (NEW, CLOSED, INCREASED, DECREASED)"),
    whales_only: bool = Query(False, description="Show only top 50 whale institutions"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of changes to return"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get institutional position changes with optional filters"""
    try:
        query = db.query(models.PositionChange)
        
        # Apply filters
        if ticker:
            query = query.filter(models.PositionChange.ticker == ticker.upper())
        
        if cik:
            query = query.filter(models.PositionChange.cik == cik)
        
        if change_type:
            query = query.filter(models.PositionChange.change_type == change_type.upper())
        
        if whales_only:
            query = query.filter(models.PositionChange.is_whale == True)
        
        # Order by detected_at descending (most recent first)
        query = query.order_by(models.PositionChange.detected_at.desc())
        
        # Limit results
        changes = query.limit(limit).all()
        
        # Convert to dict for JSON response
        result = []
        for change in changes:
            result.append({
                "id": change.id,
                "cik": change.cik,
                "ticker": change.ticker,
                "institution_name": change.institution_name,
                "change_type": change.change_type,
                "current_quarter": change.current_quarter,
                "prior_quarter": change.prior_quarter,
                "current_shares": change.current_shares,
                "prior_shares": change.prior_shares,
                "shares_change": change.shares_change,
                "percent_change": change.percent_change,
                "current_value": change.current_value,
                "prior_value": change.prior_value,
                "is_whale": change.is_whale,
                "detected_at": change.detected_at.isoformat() if change.detected_at else None,
                "created_at": change.created_at.isoformat() if change.created_at else None
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching position changes: {str(e)}")


@router.post("/alerts/{alert_id}/mark-read")
async def mark_alert_read(
    alert_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark an alert as read"""
    try:
        alert = db.query(models.WhaleAlert).filter(models.WhaleAlert.id == alert_id).first()
        
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        alert.is_read = True
        db.commit()
        
        return {"message": "Alert marked as read", "alert_id": alert_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error marking alert as read: {str(e)}")
