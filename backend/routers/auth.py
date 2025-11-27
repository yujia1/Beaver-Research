from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import bcrypt
from typing import Optional, List
import os

from database import get_db
import models

router = APIRouter()

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

# Configure passlib to use bcrypt with proper settings
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
    bcrypt__ident="2b"  # Use bcrypt 2b format
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: Optional[str] = "user"  # Default role is "user"
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password length: 6-12 characters"""
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long")
        if len(v) > 12:
            raise ValueError("Password must be no more than 12 characters long")
        return v

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

# Password hashing
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    if not plain_password or not hashed_password:
        return False
    
    # Ensure password is a string
    if not isinstance(plain_password, str):
        plain_password = str(plain_password)
    
    # Ensure hashed_password is a string
    if not isinstance(hashed_password, str):
        hashed_password = str(hashed_password)
    
    # Bcrypt has a 72-byte limit - ensure we don't exceed it
    try:
        password_bytes = plain_password.encode('utf-8')
        # If password exceeds 72 bytes, truncate it
        if len(password_bytes) > 72:
            # Truncate to 72 bytes
            password_bytes = password_bytes[:72]
        
        # Convert hash to bytes if it's a string
        if isinstance(hashed_password, str):
            hash_bytes = hashed_password.encode('utf-8')
        else:
            hash_bytes = hashed_password
        
        # Use bcrypt directly to avoid passlib issues
        try:
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except (ValueError, TypeError):
            # Fallback to passlib if bcrypt fails
            return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        # Log but don't expose the error
        import logging
        logging.error(f"Password verification error: {str(e)}")
        return False

def get_password_hash(password: str) -> str:
    """Hash a password"""
    if not password:
        raise ValueError("Password cannot be empty")
    
    # Ensure password is a string
    if not isinstance(password, str):
        password = str(password)
    
    # Bcrypt has a 72-byte limit, truncate if necessary
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        # Truncate to 72 bytes, then decode back to string
        password = password_bytes[:72].decode('utf-8', errors='ignore')
    
    return pwd_context.hash(password)

# JWT token functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# User authentication
def authenticate_user(db: Session, username: str, password: str):
    """Authenticate a user by username and password"""
    if not password:
        return False
    
    # Ensure password is a string
    if not isinstance(password, str):
        password = str(password)
    
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        return False
    
    if not user.hashed_password:
        return False
    
    # Verify password (verify_password handles truncation internally)
    if not verify_password(password, user.hashed_password):
        return False
    
    return user

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, role=role)
    except JWTError:
        raise credentials_exception
    user = get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

# Role-based access control helpers
def require_role(allowed_roles: List[str]):
    """Dependency factory to check if user has required role"""
    async def role_checker(current_user: models.User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker

# Routes
@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """Create a new user account"""
    try:
        # Validate password length: 6-12 characters
        if len(user_data.password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters long"
            )
        if len(user_data.password) > 12:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be no more than 12 characters long"
            )
        
        # Ensure role defaults to "user" if not provided or None
        if not user_data.role:
            user_data.role = "user"
        
        # Validate role
        valid_roles = ["admin", "creator", "contributor", "user"]
        if user_data.role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            )
        
        # Only allow "user" role for self-registration (admin can create other roles via separate endpoint)
        if user_data.role != "user":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only 'user' role can be assigned during signup. Contact administrator for other roles."
            )
        
        # Check if email already exists
        if get_user_by_email(db, user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if username already exists
        if get_user_by_username(db, user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Create new user
        try:
            hashed_password = get_password_hash(user_data.password)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error hashing password: {str(e)}"
            )
        
        db_user = models.User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            role=user_data.role
        )
        
        try:
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
        except Exception as db_error:
            db.rollback()
            error_msg = str(db_error)
            if "UNIQUE constraint failed" in error_msg or "duplicate key" in error_msg.lower():
                if "email" in error_msg.lower():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already registered"
                    )
                elif "username" in error_msg.lower():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username already taken"
                    )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {error_msg}"
            )
        
        return db_user
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Rollback on any other error
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )

class LoginRequest(BaseModel):
    username: str
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password length: 6-12 characters"""
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long")
        if len(v) > 12:
            raise ValueError("Password must be no more than 12 characters long")
        return v

@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login and get access token"""
    # Validate password length: 6-12 characters
    password = str(login_data.password).strip()  # Ensure it's a string and trim whitespace
    if len(password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long"
        )
    if len(password) > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be no more than 12 characters long"
        )
    
    try:
        user = authenticate_user(db, login_data.username, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Ensure user has a role (default to "user" if missing)
        user_role = getattr(user, 'role', 'user') or 'user'
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username, "role": user_role}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the error and return a generic message
        import logging
        logging.error(f"Login error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login. Please try again."
        )

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@router.get("/creators", response_model=List[UserResponse])
async def get_creators(db: Session = Depends(get_db)):
    """Get all users with creator or admin role"""
    creators = db.query(models.User).filter(
        models.User.role.in_(["creator", "admin"])
    ).order_by(models.User.username).all()
    return creators

@router.post("/create-user", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new user (admin only)"""
    # Check if current user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create users"
        )
    
    # Validate password length: 6-12 characters
    if len(user_data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long"
        )
    if len(user_data.password) > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be no more than 12 characters long"
        )
    
    # Validate role
    valid_roles = ["admin", "creator", "contributor", "user"]
    if user_data.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        )
    
    # Check if email already exists
    if get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    if get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = models.User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        role=user_data.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

