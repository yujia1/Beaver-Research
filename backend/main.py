from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from routers import internal, external, agent, energy, sec, bond, reports, auth, events, research
from database import engine, SessionLocal
import models
import bcrypt

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Initialize default users for each role type
def init_default_users():
    """Create default users for each role type if they don't exist"""
    db = SessionLocal()
    try:
        default_users = [
            {
                "username": "admin",
                "email": "admin@example.com",
                "password": "admin123",
                "role": "admin"
            },
            {
                "username": "creator",
                "email": "creator@example.com",
                "password": "creator123",
                "role": "creator"
            },
            {
                "username": "contributor",
                "email": "contributor@example.com",
                "password": "contributor123",
                "role": "contributor"
            },
            {
                "username": "user",
                "email": "user@example.com",
                "password": "user123",
                "role": "user"
            }
        ]
        
        created_count = 0
        for user_data in default_users:
            existing_user = db.query(models.User).filter(
                models.User.username == user_data["username"]
            ).first()
            
            if not existing_user:
                # Hash password using bcrypt directly to avoid passlib initialization issues
                password_bytes = user_data["password"].encode('utf-8')
                # Truncate to 72 bytes if necessary (bcrypt limit)
                if len(password_bytes) > 72:
                    password_bytes = password_bytes[:72]
                salt = bcrypt.gensalt(rounds=12)
                hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
                
                new_user = models.User(
                    username=user_data["username"],
                    email=user_data["email"],
                    hashed_password=hashed_password,
                    role=user_data["role"]
                )
                db.add(new_user)
                created_count += 1
                print(f"✓ Created default {user_data['role']} user: {user_data['username']} / {user_data['password']}")
            else:
                print(f"✗ User '{user_data['username']}' already exists, skipping")
        
        if created_count > 0:
            db.commit()
            print(f"\n✓ Initialized {created_count} default user(s)")
        else:
            print("\n✓ All default users already exist")
            
    except Exception as e:
        db.rollback()
        print(f"Error initializing default users: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

# Initialize default users on startup
init_default_users()

app = FastAPI(title="Financial Dashboard Agent")

# CORS configuration
origins = [
    "http://localhost:5173",  # Vue.js dev server (default)
    "http://localhost:5174",  # Vue.js dev server (alternative port)
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(events.router, prefix="/api/events", tags=["Events"])
app.include_router(internal.router, prefix="/api/internal", tags=["Internal Data"])
app.include_router(external.router, prefix="/api/external", tags=["External Data"])
app.include_router(agent.router, prefix="/api/agent", tags=["Agent"])
app.include_router(energy.router, prefix="/api/energy", tags=["Energy"])
app.include_router(sec.router, prefix="/api/sec", tags=["SEC Data"])
app.include_router(bond.router, prefix="/api/bond", tags=["Bond Data"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(research.router, prefix="/api/research", tags=["Research"])

@app.get("/")
def read_root():
    return {"message": "Financial Dashboard Agent API is running"}
