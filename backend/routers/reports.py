from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import boto3
from botocore.client import Config
import uuid
import os
import json

from database import get_db
from models import Report
from routers.auth import get_current_user
import models

router = APIRouter()

# MinIO configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "reports")
MINIO_USE_SSL = os.getenv("MINIO_USE_SSL", "false").lower() == "true"

# Initialize MinIO client
def get_minio_client():
    return boto3.client(
        's3',
        endpoint_url=f"{'https' if MINIO_USE_SSL else 'http'}://{MINIO_ENDPOINT}",
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        config=Config(signature_version='s3v4'),
        region_name='us-east-1'
    )

# Ensure bucket exists
def ensure_bucket_exists():
    try:
        client = get_minio_client()
        client.head_bucket(Bucket=MINIO_BUCKET)
    except:
        try:
            client = get_minio_client()
            client.create_bucket(Bucket=MINIO_BUCKET)
        except Exception as e:
            print(f"Warning: Could not create bucket {MINIO_BUCKET}: {e}")

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

class ResearchReportCreate(BaseModel):
    ticker: str
    content: str
    view_mode: Optional[str] = "COMPANY"
    active_agent: Optional[str] = None
    report_type: Optional[str] = "daily"  # daily, long, short

@router.post("/publish", status_code=201)
async def publish_research_report(
    report_data: ResearchReportCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Save research report to MinIO with ticker, date, UUID, and content"""
    try:
        # Generate UUID
        report_uuid = str(uuid.uuid4())
        
        # Get current date
        report_date = datetime.utcnow()
        date_str = report_date.strftime("%Y-%m-%d")
        
        # Validate report type
        valid_report_types = ["daily", "long", "short", "market"]
        report_type = report_data.report_type or "daily"
        if report_type not in valid_report_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid report_type. Must be one of: {', '.join(valid_report_types)}"
            )
        
        # Prepare report data
        report_json = {
            "uuid": report_uuid,
            "ticker": report_data.ticker,
            "date": date_str,
            "timestamp": report_date.isoformat(),
            "content": report_data.content,
            "view_mode": report_data.view_mode,
            "active_agent": report_data.active_agent,
            "report_type": report_type,
            "user_id": current_user.id,
            "username": current_user.username
        }
        
        # Convert to JSON string
        report_json_str = json.dumps(report_json, indent=2)
        
        # Create file path: reports/{report_type}/{ticker}/{date}/{uuid}.json
        # For "market" type, use Market/{date}/{uuid}.json (no ticker folder)
        # Map report_type to folder name
        folder_map = {
            "daily": "Daily",
            "long": "Long",
            "short": "Short",
            "market": "Market"
        }
        folder_name = folder_map.get(report_type, "Daily")
        
        # For market reports, don't include ticker in path
        if report_type == "market":
            file_path = f"{folder_name}/{date_str}/{report_uuid}.json"
        else:
            file_path = f"{folder_name}/{report_data.ticker}/{date_str}/{report_uuid}.json"
        
        # Ensure bucket exists
        ensure_bucket_exists()
        
        # Upload to MinIO
        client = get_minio_client()
        client.put_object(
            Bucket=MINIO_BUCKET,
            Key=file_path,
            Body=report_json_str.encode('utf-8'),
            ContentType='application/json'
        )
        
        # Also save to database for quick access
        # Store MinIO path in content field so we can delete it later
        minio_path_in_db = f"minio://{MINIO_BUCKET}/{file_path}"
        db_report = Report(
            title=f"{report_data.ticker} - {date_str}",
            content=minio_path_in_db,  # Store MinIO path instead of content
            report_type=report_type,
            ticker=report_data.ticker
        )
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
        
        return {
            "success": True,
            "uuid": report_uuid,
            "ticker": report_data.ticker,
            "date": date_str,
            "file_path": file_path,
            "report_id": db_report.id
        }
    except Exception as e:
        print(f"Error saving report to MinIO: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save report: {str(e)}"
        )

@router.get("/minio/{report_type}")
async def get_reports_from_minio(
    report_type: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get reports from MinIO by type (daily, long, short, market)"""
    try:
        # Validate report type
        valid_report_types = ["daily", "long", "short", "market"]
        if report_type not in valid_report_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid report_type. Must be one of: {', '.join(valid_report_types)}"
            )
        
        # Map report_type to folder name
        folder_map = {
            "daily": "Daily",
            "long": "Long",
            "short": "Short",
            "market": "Market"
        }
        folder_name = folder_map.get(report_type, "Daily")
        
        # Ensure bucket exists
        ensure_bucket_exists()
        
        # List objects in the folder
        client = get_minio_client()
        prefix = f"{folder_name}/"
        
        reports = []
        seen_uuids = set()  # Track UUIDs to prevent duplicates
        
        try:
            # Use paginator to handle all pages of results
            paginator = client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=MINIO_BUCKET, Prefix=prefix)
            
            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        try:
                            # Get the object
                            obj_response = client.get_object(Bucket=MINIO_BUCKET, Key=obj['Key'])
                            content = obj_response['Body'].read().decode('utf-8')
                            report_data = json.loads(content)
                            
                            # Extract UUID to check for duplicates
                            report_uuid = report_data.get("uuid")
                            if not report_uuid or report_uuid in seen_uuids:
                                continue  # Skip if no UUID or already seen
                            seen_uuids.add(report_uuid)
                            
                            # Extract ticker and date from path
                            # For market: Market/{date}/{uuid}.json (3 parts)
                            # For others: {folder}/{ticker}/{date}/{uuid}.json (4 parts)
                            parts = obj['Key'].split('/')
                            if report_type == "market" and len(parts) >= 3:
                                # Market reports: Market/{date}/{uuid}.json
                                date = parts[1]
                                ticker = "MARKET"  # Use MARKET as ticker for market reports
                            elif len(parts) >= 4:
                                # Other reports: {folder}/{ticker}/{date}/{uuid}.json
                                ticker = parts[1]
                                date = parts[2]
                            else:
                                continue  # Skip invalid paths
                            
                            reports.append({
                                "id": report_uuid,
                                "ticker": ticker,
                                "date": date,
                                "created_at": report_data.get("timestamp") or report_data.get("date"),
                                "content": report_data.get("content"),
                                "report_type": report_type,
                                "uuid": report_uuid
                            })
                        except Exception as e:
                            print(f"Error reading object {obj['Key']}: {e}")
                            continue
        except Exception as e:
            print(f"Error listing objects from MinIO: {e}")
            # Return empty list if folder doesn't exist or error occurs
            return []
        
        # Sort by date (newest first)
        reports.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return reports
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching reports from MinIO: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch reports: {str(e)}"
        )

@router.delete("/{report_id}", status_code=204)
async def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a report (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only administrators can delete reports"
        )
    
    # Get report from database
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=404,
            detail="Report not found"
        )
    
    try:
        client = get_minio_client()
        minio_deleted = False
        
        # Check if content field contains MinIO path
        if report.content and report.content.startswith("minio://"):
            # Extract path from minio://bucket/path format
            minio_path = report.content.replace(f"minio://{MINIO_BUCKET}/", "")
            try:
                client.delete_object(Bucket=MINIO_BUCKET, Key=minio_path)
                print(f"Deleted report from MinIO: {minio_path}")
                minio_deleted = True
            except Exception as e:
                print(f"Warning: Could not delete from MinIO ({minio_path}): {e}")
        
        # For reports published from research view (daily/long/short/market), search MinIO
        if not minio_deleted and report.report_type in ["daily", "long", "short", "market"]:
            folder_map = {
                "daily": "Daily",
                "long": "Long",
                "short": "Short",
                "market": "Market"
            }
            folder_name = folder_map.get(report.report_type, "Daily")
            
            # Get date from report's created_at to match the folder structure
            report_date = report.created_at.strftime("%Y-%m-%d") if report.created_at else None
            
            try:
                prefix = None
                if report.report_type == "market":
                    # Market reports: Market/{date}/{uuid}.json
                    if report_date:
                        prefix = f"{folder_name}/{report_date}/"
                    else:
                        prefix = f"{folder_name}/"
                else:
                    # Other reports: {folder}/{ticker}/{date}/{uuid}.json
                    if report.ticker:
                        if report_date:
                            prefix = f"{folder_name}/{report.ticker}/{report_date}/"
                        else:
                            prefix = f"{folder_name}/{report.ticker}/"
                
                # Only proceed if we have a valid prefix
                if prefix:
                    # List objects with this prefix
                    response = client.list_objects_v2(Bucket=MINIO_BUCKET, Prefix=prefix)
                    
                    if 'Contents' in response:
                        # Delete all files matching this report (same ticker, type, and date)
                        for obj in response['Contents']:
                            minio_path = obj['Key']
                            try:
                                client.delete_object(Bucket=MINIO_BUCKET, Key=minio_path)
                                print(f"Deleted report from MinIO: {minio_path}")
                                minio_deleted = True
                            except Exception as e:
                                print(f"Warning: Could not delete file {minio_path} from MinIO: {e}")
                    else:
                        print(f"No files found in MinIO with prefix: {prefix}")
            except Exception as e:
                print(f"Warning: Could not search MinIO for report: {e}")
        
        # Delete from database
        db.delete(report)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting report: {str(e)}"
        )
