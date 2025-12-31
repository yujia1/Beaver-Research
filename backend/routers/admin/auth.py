from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional, List
import os

from database import get_db
import models
# Import services
from services.email import send_reset_password_email, send_verification_email

router = APIRouter()

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

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
        if len(v) > 20:
            raise ValueError("Password must be no more than 20 characters long")
        return v

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    role: str
    is_active: bool
    has_paid: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class PermissionUpdate(BaseModel):
    role: str
    resource: str
    can_access: bool

class PermissionResponse(BaseModel):
    id: int
    role: str
    resource: str
    can_access: bool
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return v

# Password hashing
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    import bcrypt
    
    if not plain_password or not hashed_password:
        return False
    
    # Ensure password is a string
    if not isinstance(plain_password, str):
        plain_password = str(plain_password)
    
    # Ensure hashed_password is a string
    if not isinstance(hashed_password, str):
        hashed_password = str(hashed_password)
    
    try:
        # Convert to bytes
        password_bytes = plain_password.encode('utf-8')
        hash_bytes = hashed_password.encode('utf-8')
        
        # Use bcrypt to verify
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception as e:
        # Log but don't expose the error
        import logging
        logging.error(f"Password verification error: {str(e)}")
        return False

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    import bcrypt
    
    if not password:
        raise ValueError("Password cannot be empty")
    
    # Ensure password is a string
    if not isinstance(password, str):
        password = str(password)
    
    try:
        # Convert password to bytes
        password_bytes = password.encode('utf-8')
        
        # Generate salt and hash
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        
        # Return as string
        return hashed.decode('utf-8')
    except Exception as e:
        # Log the actual error for debugging
        import logging
        logging.error(f"Password hashing failed for password of length {len(password)}: {str(e)}", exc_info=True)
        raise ValueError("Failed to hash password. Please try a different password.")



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

def create_email_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a token specifically for email actions (shorter/longer expiry)"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15) # Default 15 mins for reset
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_email_token(token: str):
    """Verify email token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

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
        return current_user
    return role_checker

async def verify_premium_access(current_user: models.User = Depends(get_current_user)):
    """
    Dependency to verify if user has premium access.
    Access is granted if:
    1. User has 'admin' or 'creator' role
    2. User has 'has_paid' = True
    """
    # Admins and Creators always have access
    if current_user.role in ["admin", "creator"]:
        return current_user
    
    # Check payment status
    if not current_user.has_paid:
        print(f"Access denied for user {current_user.username}: Payment required")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium access required. Please verify your payment to access this feature."
        )
    return current_user

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
        if len(user_data.password) > 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be no more than 20 characters long"
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
        except ValueError as ve:
            # This is our custom error from get_password_hash
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(ve)
            )
        except Exception as e:
            import logging
            logging.error(f"Unexpected error hashing password: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while processing your password. Please try again."
            )
        
        db_user = models.User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            role=user_data.role,
            is_verified=False  
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
        
        
        # Send verification email in background (non-blocking)
        import asyncio
        import logging
        
        async def send_email_background():
            """Send verification email in background"""
            try:
                verification_token = create_email_token(
                    data={"sub": db_user.username, "type": "verify_email"},
                    expires_delta=timedelta(hours=24)
                )
                await asyncio.wait_for(
                    send_verification_email(db_user.email, verification_token),
                    timeout=10.0
                )
                logging.info(f"✅ Verification email sent to {db_user.email}")
            except asyncio.TimeoutError:
                logging.warning(f"⏱️ Verification email timed out for {db_user.email}")
            except Exception as e:
                logging.error(f"❌ Failed to send verification email to {db_user.email}: {str(e)}")
        
        # Fire and forget - don't wait for email to send
        asyncio.create_task(send_email_background())
        
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
        if len(v) > 20:
            raise ValueError("Password must be no more than 20 characters long")
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
    if len(password) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be no more than 20 characters long"
        )
    
    try:
        user = authenticate_user(db, login_data.username, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if email is verified
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please verify your email address before logging in. Check your inbox for the verification link."
            )
        
        # Check if account is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been deactivated. Please contact support."
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

@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all users (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view all users"
        )
    
    users = db.query(models.User).order_by(models.User.created_at.desc()).all()
    return users

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
    if len(user_data.password) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be no more than 20 characters long"
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

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a user (admin only)"""
    # Check if current user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete users"
        )
    
    # Prevent admin from deleting themselves
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account"
        )
    
    # Find the user to delete
    user_to_delete = db.query(models.User).filter(models.User.id == user_id).first()
    if not user_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Delete the user and all associated data
    try:
        
        # Delete all reports associated with this user (if reports have user_id)
        # Note: Check if Report model has user_id field, if not, this can be skipped
        # For now, we'll delete reports that might be associated via other means if needed
        
        # Delete the user
        db.delete(user_to_delete)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting user: {str(e)}"
        )

# Payment verification endpoints
class PaymentVerificationRequest(BaseModel):
    transaction_id: str
    email: Optional[str] = None

@router.get("/payment-status")
async def get_payment_status(current_user: models.User = Depends(get_current_user)):
    """Get current user's payment status"""
    # Admins always have paid status
    has_paid = True if current_user.role == "admin" else (current_user.has_paid if hasattr(current_user, 'has_paid') else False)
    
    return {
        "has_paid": has_paid,
        "role": current_user.role,
        "payment_date": current_user.payment_date.isoformat() if hasattr(current_user, 'payment_date') and current_user.payment_date else None,
        "transaction_id": current_user.payment_transaction_id if hasattr(current_user, 'payment_transaction_id') else None
    }

@router.post("/verify-payment")
async def verify_payment(
    payment_data: PaymentVerificationRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Verify payment and grant access to Research page (admin can verify manually)"""
    # Only admin can verify payments manually
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can verify payments"
        )
    
    # Find user by email or transaction ID
    user = None
    if payment_data.email:
        user = get_user_by_email(db, payment_data.email)
    elif payment_data.transaction_id:
        user = db.query(models.User).filter(
            models.User.payment_transaction_id == payment_data.transaction_id
        ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update payment status
    user.has_paid = True
    user.payment_transaction_id = payment_data.transaction_id
    user.payment_date = datetime.utcnow()
    
    db.commit()
    db.refresh(user)
    
    return {
        "message": "Payment verified successfully",
        "user": UserResponse.model_validate(user)
    }

class UpdatePaymentStatusRequest(BaseModel):
    user_id: int
    has_paid: bool
    transaction_id: Optional[str] = None

class UserRoleUpdate(BaseModel):
    role: str

@router.post("/update-payment-status")
async def update_payment_status(
    payment_data: UpdatePaymentStatusRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update payment status for a user (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update payment status"
        )
    
    user = db.query(models.User).filter(models.User.id == payment_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.has_paid = payment_data.has_paid
    if payment_data.transaction_id:
        user.payment_transaction_id = payment_data.transaction_id
    if payment_data.has_paid and not user.payment_date:
        user.payment_date = datetime.utcnow()
    
    db.commit()
    db.refresh(user)
    
    return {
        "message": "Payment status updated successfully",
        "user": UserResponse.model_validate(user)
    }

@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    role_data: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update a user's role (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update user roles"
        )
    
    # Prevent admin from changing their own role (avoid lockout)
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own role"
        )

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    valid_roles = ["admin", "creator", "contributor", "user"]
    if role_data.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        )
        
    user.role = role_data.role
    db.commit()
    db.refresh(user)
    
    return {
        "message": "User role updated successfully",
        "user": UserResponse.model_validate(user)
    }

# Permission Management Endpoints

@router.get("/permissions", response_model=List[PermissionResponse])
async def get_permissions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all permissions (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view permissions"
        )
    return db.query(models.RolePermission).all()

from redis_client import redis_client

# ... (imports)

@router.post("/permissions", response_model=PermissionResponse)
async def update_permission(
    permission_data: PermissionUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update or create a permission rule (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can manage permissions"
        )
    
    permission = db.query(models.RolePermission).filter(
        models.RolePermission.role == permission_data.role,
        models.RolePermission.resource == permission_data.resource
    ).first()
    
    if permission:
        permission.can_access = permission_data.can_access
        permission.updated_at = datetime.utcnow()
    else:
        permission = models.RolePermission(
            role=permission_data.role,
            resource=permission_data.resource,
            can_access=permission_data.can_access
        )
        db.add(permission)
    
    try:
        db.commit()
        db.refresh(permission)
        
        # Invalidate cache for this role
        redis_client.delete_cache(f"permissions:{permission_data.role}")
        
        return permission
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating permission: {str(e)}"
        )

@router.get("/my-permissions", response_model=List[str])
async def get_my_permissions(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of resources the current user can access"""
    # Admin gets access to everything by default
    if current_user.role == "admin":
        return ["/research", "/portfolio", "/report", "/investment", "/short-interest", "/agent", "/academy"]
    
    # Try to get from cache
    cache_key = f"permissions:{current_user.role}"
    cached_permissions = redis_client.get_cache(cache_key)
    if cached_permissions is not None:
        return cached_permissions
    
    # Fetch permissions for user's role
    params = db.query(models.RolePermission).filter(
        models.RolePermission.role == current_user.role,
        models.RolePermission.can_access == True
    ).all()
    
    allowed_resources = [p.resource for p in params]
    
    # Set cache (TTL 5 minutes)
    redis_client.set_cache(cache_key, allowed_resources, ttl=300)
    
    return allowed_resources

@router.post("/initialize-permissions")
async def initialize_permissions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Initialize default permissions if empty (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
        
    count = db.query(models.RolePermission).count()
    if count > 0:
        return {"message": "Permissions already initialized", "count": count}
        
    resources = ["/research", "/portfolio", "/report", "/investment", "/short-interest", "/agent", "/academy"]
    roles = ["creator", "contributor", "user"]
    
    # Default Policy:
    # Creator: Access to everything
    # Contributor: Access to everything
    # User: Access to everything (start open, let admin restrict)
    
    added = 0
    for role in roles:
        for resource in resources:
            perm = models.RolePermission(
                role=role,
                resource=resource,
                can_access=True
            )
            db.add(perm)
            added += 1
            
    db.commit()
    
    # Clear all permission caches
    redis_client.delete_cache("permissions:*")
    
    return {"message": "Initialized default permissions", "added": added}


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Initiate password reset flow"""
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if user:
        # Generate token
        token = create_email_token(
            data={"sub": user.username, "type": "reset_password"},
            expires_delta=timedelta(minutes=15)
        )
        # Send email (background task in real app, awaited here for simplicity)
        await send_reset_password_email(user.email, token)
    
    # Always return success to prevent email enumeration
    return {"message": "If this email is registered, we have sent a password reset link."}

@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using token"""
    payload = verify_email_token(request.token)
    if not payload or payload.get("type") != "reset_password":
        raise HTTPException(status_code=400, detail="Invalid or expired token")
        
    username = payload.get("sub")
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Update password
    hashed_password = get_password_hash(request.new_password)
    user.hashed_password = hashed_password
    db.commit()
    
    # Generate access token for auto-login
    user_role = getattr(user, 'role', 'user') or 'user'
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user_role}, expires_delta=access_token_expires
    )
    
    return {
        "message": "Password updated successfully",
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify email address"""
    payload = verify_email_token(token)
    if not payload or payload.get("type") != "verify_email":
        raise HTTPException(status_code=400, detail="Invalid or expired token")
        
    username = payload.get("sub")
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.is_verified = True
    db.commit()
    
    return {"message": "Email verified successfully"}

