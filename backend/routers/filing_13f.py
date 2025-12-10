"""
API endpoints for 13F filing processing and management.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime
import uuid
import threading

from database import get_db
from models import Filing13F
from routers.auth import get_current_user
from services.filing_13f_service import filing_13f_service
import models

router = APIRouter()

# In-memory job status tracking
job_status: Dict[str, Dict] = {}
job_lock = threading.Lock()

class Filing13FResponse(BaseModel):
    id: int
    cik: str
    accession_number: str
    form_type: str
    filing_date: datetime
    period_end_date: datetime
    quarter: str
    is_amended: bool
    minio_path: Optional[str]
    holdings_count: Optional[int]
    total_value: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True

class ProcessBatchRequest(BaseModel):
    quarters: Optional[List[str]] = None
    force_reprocess: bool = False

class ProcessBatchResponse(BaseModel):
    job_id: str
    status: str
    message: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # 'pending', 'running', 'completed', 'error'
    result: Optional[Dict] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class QuarterComparisonResponse(BaseModel):
    cik: str
    current_quarter: str
    prior_quarter: str
    new_positions: List[dict]
    closed_positions: List[dict]
    size_changes: List[dict]
    new_positions_count: int
    closed_positions_count: int
    size_changes_count: int

def process_13f_batch_background(
    job_id: str,
    quarters: Optional[List[str]],
    force_reprocess: bool
):
    """Background task to process 13F filings"""
    with job_lock:
        job_status[job_id]['status'] = 'running'
        job_status[job_id]['started_at'] = datetime.utcnow()
    
    try:
        # Get a new database session for the background task
        from database import SessionLocal
        db = SessionLocal()
        try:
            result = filing_13f_service.process_batch(
                db, 
                quarters=quarters,
                force_reprocess=force_reprocess
            )
            with job_lock:
                job_status[job_id]['status'] = 'completed'
                job_status[job_id]['result'] = result
                job_status[job_id]['completed_at'] = datetime.utcnow()
        finally:
            db.close()
    except Exception as e:
        with job_lock:
            job_status[job_id]['status'] = 'error'
            job_status[job_id]['error'] = str(e)
            job_status[job_id]['completed_at'] = datetime.utcnow()

@router.post("/process", response_model=ProcessBatchResponse)
async def process_13f_filings(
    request: ProcessBatchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Manually trigger 13F filing processing (admin only) - runs asynchronously"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only administrators can trigger 13F processing"
        )
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Initialize job status
    with job_lock:
        job_status[job_id] = {
            'status': 'pending',
            'result': None,
            'error': None,
            'started_at': None,
            'completed_at': None
        }
    
    # Add background task
    background_tasks.add_task(
        process_13f_batch_background,
        job_id=job_id,
        quarters=request.quarters,
        force_reprocess=request.force_reprocess
    )
    
    return ProcessBatchResponse(
        job_id=job_id,
        status='pending',
        message='13F batch processing started. Use the job_id to check status.'
    )

@router.get("/process/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    current_user: models.User = Depends(get_current_user)
):
    """Get the status of a 13F batch processing job"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only administrators can check job status"
        )
    
    with job_lock:
        if job_id not in job_status:
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )
        
        job = job_status[job_id].copy()
    
    return JobStatusResponse(
        job_id=job_id,
        status=job['status'],
        result=job.get('result'),
        error=job.get('error'),
        started_at=job.get('started_at'),
        completed_at=job.get('completed_at')
    )

@router.get("/filings", response_model=List[Filing13FResponse])
async def list_13f_filings(
    cik: Optional[str] = Query(None),
    quarter: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    skip: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List processed 13F filings"""
    query = db.query(Filing13F)
    
    if cik:
        query = query.filter(Filing13F.cik == cik)
    if quarter:
        query = query.filter(Filing13F.quarter == quarter)
    
    filings = query.order_by(Filing13F.filing_date.desc()).offset(skip).limit(limit).all()
    return filings

@router.get("/filings/{filing_id}", response_model=Filing13FResponse)
async def get_13f_filing(
    filing_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get a specific 13F filing"""
    filing = db.query(Filing13F).filter(Filing13F.id == filing_id).first()
    if not filing:
        raise HTTPException(status_code=404, detail="Filing not found")
    return filing

@router.get("/compare", response_model=QuarterComparisonResponse)
async def compare_quarters(
    cik: str = Query(...),
    current_quarter: str = Query(...),
    prior_quarter: str = Query(...),
    min_change_pct: float = Query(5.0, ge=0, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Compare holdings between two quarters"""
    try:
        result = filing_13f_service.compare_quarters(
            db, cik, current_quarter, prior_quarter, min_change_pct
        )
        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error comparing quarters: {str(e)}"
        )

@router.get("/ciks")
async def list_ciks(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all CIKs that have processed 13F filings"""
    ciks = db.query(Filing13F.cik).distinct().all()
    return [cik[0] for cik in ciks]

@router.get("/holdings/{ticker}")
async def get_institution_holdings_by_ticker(
    ticker: str,
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get institution holdings for a specific ticker with buy/sell indicators"""
    try:
        holdings = filing_13f_service.get_institution_holdings_by_ticker(db, ticker, limit)
        return {
            'ticker': ticker.upper(),
            'holdings': holdings,
            'count': len(holdings)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching institution holdings: {str(e)}"
        )

