from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from database import get_db
from models import Report

router = APIRouter()

class ReportCreate(BaseModel):
    title: str
    content: str
    report_type: str
    ticker: str

class ReportResponse(BaseModel):
    id: int
    title: str
    content: str
    report_type: str
    ticker: str
    created_at: datetime

    class Config:
        from_attributes = True

class ReportSummary(BaseModel):
    id: int
    title: str
    report_type: str
    ticker: str
    created_at: datetime

    class Config:
        from_attributes = True

@router.post("/", response_model=ReportResponse)
def create_report(report: ReportCreate, db: Session = Depends(get_db)):
    db_report = Report(
        title=report.title,
        content=report.content,
        report_type=report.report_type,
        ticker=report.ticker
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

@router.get("/", response_model=List[ReportSummary])
def list_reports(db: Session = Depends(get_db)):
    reports = db.query(Report).order_by(Report.created_at.desc()).all()
    return reports

@router.get("/{report_id}", response_model=ReportResponse)
def get_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
