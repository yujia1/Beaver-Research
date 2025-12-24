from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import os
import logging

logger = logging.getLogger(__name__)

# Database URL - defaults to PostgreSQL, falls back to SQLite for local dev
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./financial_agent.db"
)

# Determine if using PostgreSQL
is_postgres = SQLALCHEMY_DATABASE_URL.startswith("postgresql")

# Create engine with appropriate configuration
if is_postgres:
    # PostgreSQL configuration with connection pooling
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        poolclass=QueuePool,
        pool_size=20,              # Number of connections to maintain
        max_overflow=40,           # Additional connections when pool is full
        pool_pre_ping=True,        # Verify connections before using
        pool_recycle=3600,         # Recycle connections after 1 hour
        echo=False,                # Set to True for SQL query logging
    )
    logger.info("Database engine created with PostgreSQL connection pooling")
else:
    # SQLite configuration (for local development only)
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
    logger.warning("Using SQLite database - NOT recommended for production")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_db_connection():
    """Health check function to verify database connectivity"""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
