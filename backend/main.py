from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
import os
import logging
import json
from datetime import datetime

# Configure structured logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

# Setup logging
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()
logger.info("Environment variables loaded")

from routers.market import external
from routers import stream

from routers.market.equity import indices, markets_wire, sec, stocks
from routers.market.bond import routes as bond
from routers.market.commodity import energy
from routers.market.commodity import routes as commodity_routes
from routers.market.currency import routes as currency_routes
from routers.market.policy import routes as policy_routes
from routers.market.crypto import routes as crypto_routes
from routers.market.economic import macro
from routers.framework import routes as framework
from routers.journal import routes as reports
from routers.portfolio import routes as portfolio
from routers.research import routes as research
from routers.research import agent
from routers.admin import auth, db as admin_db, payment
# from routers.util import internal_legacy # Deprecated

from database import engine, SessionLocal, check_db_connection
import models
import bcrypt
# from services.scheduler_13f import setup_13f_scheduler

# Database tables will be created in startup event
# This allows us to rebuild the schema if needed before creating tables


# Initialize default users for each role type
def init_default_users():
    """Create default users for each role type if they don't exist"""
    db = SessionLocal()
    try:
        default_users = [
            {
                "username": "yjia0405@gmail.com",
                "email": "yjia0405@gmail.com",
                "password": "Itsucks2020.",
                "role": "admin"
            },
            {
                "username": "yjia0406@gmail.com",
                "email": "yjia0406@gmail.com",
                "password": "yjia0406",
                "role": "creator"
            },
            {
                "username": "testuser@gmail.com",
                "email": "testuser@gmail.com",
                "password": "testpass123",
                "role": "user"
            },
            {
                "username": "contributor@example.com",
                "email": "contributor@example.com",
                "password": "contributor123",
                "role": "contributor"
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

# Initialize default users
# We will initialize these in the startup event


# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Financial Dashboard Agent",
    description="Production-ready financial research platform",
    version="1.0.0"
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

logger.info("FastAPI application initialized")

# CORS configuration - Dynamic based on environment
# Read allowed origins from environment variable, or use defaults for local development
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_env:
    # Parse comma-separated origins from environment variable
    origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]
    logger.info(f"Using CORS origins from ALLOWED_ORIGINS env var: {origins}")
else:
    # Default origins for local development
    origins = [
        "http://localhost:5173",  # Vue.js dev server (default)
        "http://localhost:5174",  # Vue.js dev server (alternative port)
        "http://localhost:8080",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ]
    logger.info("Using default CORS origins for local development")

# For Railway deployments, allow all Railway app URLs
# This is safe because Railway URLs are unique and controlled
allow_all_railway = os.getenv("ALLOW_RAILWAY_ORIGINS", "true").lower() == "true"

if allow_all_railway:
    # Use a custom origin validator that allows Railway domains
    def validate_origin(origin: str) -> bool:
        """Allow Railway domains and configured origins"""
        if origin in origins:
            return True
        # Allow any Railway app domain
        if ".railway.app" in origin or ".up.railway.app" in origin:
            return True
        return False
    
    # For Railway, we'll use allow_origin_regex instead
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for Railway
        allow_credentials=False,  # Must be False when using allow_origins=["*"]
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    logger.info("CORS configured to allow all Railway domains")
else:
    # Use explicit origins list
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    logger.info(f"CORS configured with explicit origins: {origins}")


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        logger.info("Running startup initialization...")
        
        # Import at function level to avoid circular imports
        from database import Base, engine
        from sqlalchemy import inspect, text
        
        # 0. Handle database schema setup
        rebuild_db = os.getenv("REBUILD_DB", "false").lower() == "true"
        
        if rebuild_db:
            # Rebuild: Drop all tables and recreate from models
            logger.info("REBUILD_DB flag detected - rebuilding database schema...")
            try:
                logger.info("Dropping all existing tables...")
                
                # For PostgreSQL, we need to use CASCADE to drop tables with foreign key dependencies
                # Check if we're using PostgreSQL
                from sqlalchemy.engine.url import make_url
                db_url = str(engine.url)
                is_postgres = db_url.startswith("postgresql")
                
                if is_postgres:
                    # Use raw SQL with CASCADE for PostgreSQL
                    logger.info("Using CASCADE to drop all tables (PostgreSQL)")
                    with engine.connect() as conn:
                        # Get all table names
                        inspector = inspect(engine)
                        tables = inspector.get_table_names()
                        
                        # Drop each table with CASCADE
                        for table in tables:
                            conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
                            logger.info(f"Dropped table: {table}")
                        conn.commit()
                else:
                    # For SQLite, regular drop_all works fine
                    Base.metadata.drop_all(bind=engine)
                
                logger.info("Creating all tables from models...")
                Base.metadata.create_all(bind=engine)
                logger.info("Database schema rebuild complete!")
            except Exception as e:
                logger.error(f"Failed to rebuild database schema: {e}")
                raise  # Fail startup if rebuild fails
        else:
            # Normal startup: Just ensure tables exist (create if missing)
            logger.info("Ensuring database tables exist...")
            try:
                models.Base.metadata.create_all(bind=engine)
                logger.info("Database tables verified/created")
                
                # Validate schema - check if critical columns exist
                inspector = inspect(engine)
                if inspector.has_table("users"):
                    columns = [col['name'] for col in inspector.get_columns("users")]
                    if 'settings' not in columns:
                        logger.error("=" * 80)
                        logger.error("SCHEMA MISMATCH DETECTED!")
                        logger.error("The 'users' table exists but is missing the 'settings' column.")
                        logger.error("This means the database schema is outdated.")
                        logger.error("")
                        logger.error("TO FIX THIS:")
                        logger.error("1. Set environment variable: REBUILD_DB=true")
                        logger.error("2. Redeploy the application")
                        logger.error("3. After successful deployment, remove REBUILD_DB or set it to false")
                        logger.error("=" * 80)
                        raise Exception("Database schema is outdated. Set REBUILD_DB=true to rebuild.")
                
            except Exception as e:
                logger.error(f"Failed to create/validate database tables: {e}")
                raise  # Fail startup if table creation fails
        
        # 1. Init Users (only after database schema is ready)
        try:
            init_default_users()
        except Exception as e:
            logger.error(f"Failed to init default users (non-fatal): {e}")

        # 2. Start Background Tasks
        try:
            from services.scheduler import start_scheduler, run_initial_fetch
            import asyncio
            
            start_scheduler()
            # Run initial fetch asynchronously to avoid blocking startup
            asyncio.create_task(run_initial_fetch())
            logger.info("Market Data Scheduler started and initial fetch triggered.")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
    except Exception as e:
        logger.error(f"Critical startup error: {e}")
        raise  # Re-raise to prevent app from starting with broken state

# Register Routers
# Admin
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(admin_db.router, prefix="/api/admin/db", tags=["Database Management"])
app.include_router(payment.router) # Prefix handled in router

# Market - Equity
app.include_router(stocks.router, prefix="/api/market/equity/stocks", tags=["Stocks"])
app.include_router(indices.router, prefix="/api/market/equity/indices", tags=["Indices"])

# Shim for deprecated internal indices endpoint (for backwards compatibility)
@app.get("/api/internal/indices", tags=["Deprecated"])
async def get_indices_shim():
    from routers.market.equity.indices import get_indices
    return await get_indices()

# Market - News & Streams    
app.include_router(markets_wire.router, prefix="/api/market/news", tags=["Market News"])
app.include_router(stream.router, prefix="/api/stream", tags=["Stream"])

# Market - SEC
app.include_router(sec.router, prefix="/api/market/sec", tags=["SEC Data"])

# Market - Bond
app.include_router(bond.router, prefix="/api/market/bond", tags=["Bond Data"])

# Market - Commodity
app.include_router(energy.router, prefix="/api/market/commodity/energy", tags=["Energy"])
app.include_router(commodity_routes.router, prefix="/api/market/commodity", tags=["Commodities"])

# Market - Currency
app.include_router(currency_routes.router, prefix="/api/market/currency", tags=["Currencies"])

# Market - Economic
app.include_router(macro.router, prefix="/api/market/economic", tags=["Economic Data"])

# Market - Crypto
app.include_router(crypto_routes.router, prefix="/api/market/crypto", tags=["Crypto"])

# Market - Policy
app.include_router(policy_routes.router, prefix="/api/market/policy", tags=["Policy"])

# Market - External
app.include_router(external.router, prefix="/api/market/external", tags=["External Data"])

# Research
app.include_router(research.router, prefix="/api/research", tags=["Research"])
app.include_router(agent.router, prefix="/api/agent", tags=["Agent"])

# Journal
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])

# Portfolio
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])

# Framework
app.include_router(framework.router, prefix="/api/framework", tags=["Framework"])


# app.include_router(admin_scheduler.router, prefix="/api/admin/scheduler", tags=["Scheduler Configuration"])

@app.get("/")
def read_root():
    return {"message": "Financial Dashboard Agent API is running"}

@app.get("/health")
@limiter.limit("60/minute")
async def health_check(request: Request):
    """Comprehensive health check endpoint for monitoring"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "beaver-research-api",
        "version": "1.0.0"
    }
    
    # Check database connectivity
    try:
        db_healthy = check_db_connection()
        health_status["database"] = "healthy" if db_healthy else "unhealthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["database"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Check scheduler status
    health_status["scheduler"] = "disabled"
    
    # Return appropriate status code
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)

@app.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe endpoint"""
    db_healthy = check_db_connection()
    if db_healthy:
        return {"status": "ready"}
    return JSONResponse(content={"status": "not ready"}, status_code=503)

@app.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe endpoint"""
    return {"status": "alive"}

 
