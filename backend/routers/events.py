from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

from database import get_db
import models
from routers.auth import get_current_user, get_user_by_username, verify_premium_access
from jose import JWTError, jwt
import os

# Security configuration (same as auth.py)
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"

router = APIRouter()

# Pydantic models
class EventCreate(BaseModel):
    ticker: str
    date: str  # ISO format date string
    title: str
    description: Optional[str] = ""
    type: str  # positive, negative, neutral
    category: str  # macro, micro, market, industry, product
    is_forecast: bool = False

class EventUpdate(BaseModel):
    date: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    category: Optional[str] = None
    is_forecast: Optional[bool] = None

class EventResponse(BaseModel):
    id: int
    user_id: int
    ticker: str
    date: datetime
    title: str
    description: Optional[str]
    type: str
    category: str
    is_forecast: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Helper function to check if user is creator or admin
def require_creator_or_admin(current_user: models.User = Depends(get_current_user)):
    if current_user.role not in ["creator", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only creators and administrators can manage events"
        )
    return current_user

# Routes
@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event: EventCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(verify_premium_access)
):
    """Create a new event (creator/admin only)"""
    # Validate ticker is provided and not empty
    if not event.ticker or not event.ticker.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ticker is required and cannot be empty"
        )
    
    # Validate event type
    valid_types = ["positive", "negative", "neutral"]
    if event.type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid event type. Must be one of: {', '.join(valid_types)}"
        )
    
    # Validate category
    valid_categories = ["macro", "micro", "market", "industry", "product"]
    if event.category not in valid_categories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category. Must be one of: {', '.join(valid_categories)}"
        )
    
    # Parse date
    try:
        event_date = datetime.fromisoformat(event.date.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)"
        )
    
    # Normalize ticker (uppercase, trimmed)
    normalized_ticker = event.ticker.strip().upper()
    
    # Create event - event is associated with the specific ticker and user
    db_event = models.Event(
        user_id=current_user.id,
        ticker=normalized_ticker,
        date=event_date,
        title=event.title,
        description=event.description,
        type=event.type,
        category=event.category,
        is_forecast=event.is_forecast
    )
    
    try:
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        return db_event
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating event: {str(e)}"
        )

# Optional authentication dependency
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[models.User]:
    """Get current user if authenticated, otherwise return None"""
    if not credentials:
        return None
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        user = get_user_by_username(db, username=username)
        return user
    except:
        return None

@router.get("/", response_model=List[EventResponse])
async def read_events(
    skip: int = 0, 
    limit: int = 100, 
    ticker: Optional[str] = None,
    category: Optional[str] = None,
    creator_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional)
):
    """
    Get events associated with a specific ticker.
    - If creator_id is provided: returns events from that specific creator for the ticker
    - If user is creator/admin and no creator_id: returns only their own events for the ticker
    - Otherwise: returns all events for the ticker
    - Ticker is required for proper event filtering
    """
    query = db.query(models.Event)
    
    # Filter by ticker - required for proper event association
    if ticker:
        normalized_ticker = ticker.strip().upper()
        query = query.filter(models.Event.ticker == normalized_ticker)
    else:
        # If no ticker provided, return empty list (events must be associated with a ticker)
        return []
    
    # Filter by creator_id if provided (allows viewing specific creator's events)
    if creator_id is not None:
        # Verify the creator_id belongs to a creator or admin
        creator_user = db.query(models.User).filter(
            models.User.id == creator_id,
            models.User.role.in_(["creator", "admin"])
        ).first()
        if creator_user:
            query = query.filter(models.Event.user_id == creator_id)
        else:
            # Invalid creator_id, return empty list
            return []
    elif current_user and current_user.role in ["creator", "admin"]:
        # If no creator_id specified and user is creator/admin, show only their own events
        query = query.filter(models.Event.user_id == current_user.id)
    # If regular user and no creator_id, show all events for the ticker
    
    events = query.order_by(models.Event.date.desc()).all()
    return events

@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional)
):
    """Get a specific event"""
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # If user is creator/admin, only allow access to their own events
    if current_user and current_user.role in ["creator", "admin"]:
        if event.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own events"
            )
    
    return event

@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event_data: EventUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_creator_or_admin)
):
    """Update an event (creator/admin only, and only their own events)"""
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Only allow updating own events
    if event.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own events"
        )
    
    # Update fields
    if event_data.date is not None:
        try:
            event.date = datetime.fromisoformat(event_data.date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format"
            )
    
    if event_data.title is not None:
        event.title = event_data.title
    
    if event_data.description is not None:
        event.description = event_data.description
    
    if event_data.type is not None:
        valid_types = ["positive", "negative", "neutral"]
        if event_data.type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid event type. Must be one of: {', '.join(valid_types)}"
            )
        event.type = event_data.type
    
    if event_data.category is not None:
        valid_categories = ["macro", "micro", "market", "industry", "product"]
        if event_data.category not in valid_categories:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category. Must be one of: {', '.join(valid_categories)}"
            )
        event.category = event_data.category
    
    if event_data.is_forecast is not None:
        event.is_forecast = event_data.is_forecast
    
    try:
        db.commit()
        db.refresh(event)
        return event
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating event: {str(e)}"
        )

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_creator_or_admin)
):
    """Delete an event (creator/admin only, and only their own events)"""
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Only allow deleting own events
    if event.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own events"
        )
    
    try:
        db.delete(event)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting event: {str(e)}"
        )

