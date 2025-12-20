from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import boto3
from botocore.client import Config
import uuid
import os
import json
from jose import JWTError, jwt

from database import get_db
from models import Report
from routers.auth import get_current_user, verify_premium_access
import models

# Token verification for query parameter (for iframe access)
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"

async def verify_token_from_query(token: str = Query(...), db: Session = Depends(get_db)):
    """Verify token from query parameter"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(models.User).filter(models.User.username == username).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

router = APIRouter()

# MinIO configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "reports")
MINIO_USE_SSL = os.getenv("MINIO_USE_SSL", "false").lower() == "true"

# Initialize MinIO client
def get_minio_client():
    # Check if endpoint already has protocol
    if MINIO_ENDPOINT.startswith('http://') or MINIO_ENDPOINT.startswith('https://'):
        endpoint_url = MINIO_ENDPOINT
    else:
        endpoint_url = f"{'https' if MINIO_USE_SSL else 'http'}://{MINIO_ENDPOINT}"
    
    return boto3.client(
        's3',
        endpoint_url=endpoint_url,
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
async def get_reports(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(verify_premium_access)
):
    reports = db.query(Report).order_by(Report.created_at.desc()).all()
    return reports

@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(verify_premium_access)
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@router.post("/publish", status_code=201)
async def publish_research_report(
    pdf_file: UploadFile = File(...),
    ticker: str = Form(...),
    view_mode: Optional[str] = Form("COMPANY"),
    active_agent: Optional[str] = Form(None),
    report_type: Optional[str] = Form("daily"),
    report_name: Optional[str] = Form("Untitled Report"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Save research report PDF to MinIO with ticker, date, UUID"""
    try:
        # Generate UUID
        report_uuid = str(uuid.uuid4())
        
        # Get current date
        report_date = datetime.utcnow()
        date_str = report_date.strftime("%Y-%m-%d")
        
        # Validate report type
        valid_report_types = ["daily", "long", "short", "market"]
        if report_type not in valid_report_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid report_type. Must be one of: {', '.join(valid_report_types)}"
            )
        
        # Validate PDF file
        if pdf_file.content_type != "application/pdf":
            raise HTTPException(
                status_code=400,
                detail="File must be a PDF"
            )
        
        # Read PDF file content
        pdf_content = await pdf_file.read()
        
        # Map report_type to folder name
        folder_map = {
            "daily": "Daily",
            "long": "Long",
            "short": "Short",
            "market": "Market"
        }
        folder_name = folder_map.get(report_type, "Daily")
        
        # Use report_name for filename, sanitize it
        safe_report_name = report_name.strip() if report_name and report_name.strip() else f"{ticker} - {date_str}"
        # Remove invalid filename characters
        safe_report_name = "".join(c for c in safe_report_name if c.isalnum() or c in (' ', '-', '_')).strip()
        
        # Create file path: folder/report-name-uuid.pdf
        file_path = f"{folder_name}/{safe_report_name}-{report_uuid}.pdf"
        
        # Ensure bucket exists
        ensure_bucket_exists()
        
        # Upload PDF to MinIO
        client = get_minio_client()
        client.put_object(
            Bucket=MINIO_BUCKET,
            Key=file_path,
            Body=pdf_content,
            ContentType='application/pdf'
        )
        
        # Also save to database for quick access
        # Store MinIO path in content field so we can delete it later
        minio_path_in_db = f"minio://{MINIO_BUCKET}/{file_path}"
        # Use report_name if provided, otherwise use default format
        report_title = report_name if report_name and report_name.strip() else f"{ticker} - {date_str}"
        db_report = Report(
            title=report_title,
            content=minio_path_in_db,  # Store MinIO path instead of content
            report_type=report_type,
            ticker=ticker
        )
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
        
        return {
            "success": True,
            "uuid": report_uuid,
            "ticker": ticker,
            "date": date_str,
            "file_path": file_path,
            "report_id": db_report.id
        }
    except HTTPException:
        raise
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
                            # New structure: {folder}/{report-name}-{uuid}.pdf
                            # Example: Market/GOLD-test-4bc6319b-54cd-4fc0-8c50-d981b9be65f4.pdf
                            parts = obj['Key'].split('/')
                            if len(parts) >= 2:
                                folder = parts[0]
                                filename = parts[1]
                                
                                # Extract report name and UUID from filename
                                # Format: report-name-uuid.pdf
                                if filename.endswith('.pdf'):
                                    filename_without_ext = filename[:-4]  # Remove .pdf
                                    
                                    # Find the last occurrence of UUID pattern (last 36 chars before .pdf)
                                    # UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx (36 chars)
                                    if len(filename_without_ext) > 36:
                                        # Extract UUID (last 36 characters)
                                        uuid_from_filename = filename_without_ext[-36:]
                                        # Extract report name (everything before the last dash and UUID)
                                        report_name = filename_without_ext[:-37]  # Remove -uuid
                                        
                                        # Use report name as ticker for display
                                        ticker = report_name if report_name else "UNKNOWN"
                                    else:
                                        # Fallback for old format or short names
                                        uuid_from_filename = filename_without_ext
                                        ticker = "UNKNOWN"
                                    
                                    # Check for duplicates by UUID
                                    if uuid_from_filename in seen_uuids:
                                        continue
                                    seen_uuids.add(uuid_from_filename)
                                    
                                    # Get file metadata (last modified time)
                                    last_modified = obj.get('LastModified', datetime.utcnow())
                                    
                                    # Use last modified date as the report date
                                    date = last_modified.strftime("%Y-%m-%d") if hasattr(last_modified, 'strftime') else "Unknown"
                                    
                                    reports.append({
                                        "id": uuid_from_filename,
                                        "ticker": ticker,
                                        "date": date,
                                        "created_at": last_modified.isoformat() if hasattr(last_modified, 'isoformat') else str(last_modified),
                                        "report_type": report_type,
                                        "uuid": uuid_from_filename,
                                        "file_path": obj['Key'],
                                        "report_name": ticker
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

@router.get("/minio/pdf/{report_type}/{ticker}/{date}/{uuid}")
async def get_pdf_from_minio(
    report_type: str,
    ticker: str,
    date: str,
    uuid: str,
    current_user: models.User = Depends(verify_token_from_query)
):
    """Get PDF content from MinIO"""
    try:
        # Map report_type to folder name
        folder_map = {
            "daily": "Daily",
            "long": "Long",
            "short": "Short",
            "market": "Market"
        }
        folder_name = folder_map.get(report_type, "Daily")
        
        # New structure: {folder}/{report-name}-{uuid}.pdf
        # We need to search for the file with this UUID
        client = get_minio_client()
        
        try:
            # List all files in the folder
            prefix = f"{folder_name}/"
            response = client.list_objects_v2(Bucket=MINIO_BUCKET, Prefix=prefix)
            
            file_path = None
            if 'Contents' in response:
                for obj in response['Contents']:
                    # Check if this file contains the UUID
                    if uuid in obj['Key']:
                        file_path = obj['Key']
                        break
            
            if not file_path:
                raise HTTPException(
                    status_code=404,
                    detail="PDF not found"
                )
            
            # Get PDF from MinIO
            obj_response = client.get_object(Bucket=MINIO_BUCKET, Key=file_path)
            pdf_content = obj_response['Body'].read()
            
            from fastapi.responses import Response
            return Response(
                content=pdf_content,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"inline; filename={uuid}.pdf"
                }
            )
        except client.exceptions.NoSuchKey:
            raise HTTPException(
                status_code=404,
                detail="PDF not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching PDF from MinIO: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch PDF: {str(e)}"
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
                    # Market reports: Market/{date}/{uuid}.pdf
                    if report_date:
                        prefix = f"{folder_name}/{report_date}/"
                    else:
                        prefix = f"{folder_name}/"
                else:
                    # Other reports: {folder}/{ticker}/{date}/{uuid}.pdf
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
