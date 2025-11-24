from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database URL - Update with actual credentials
# For now using a default local postgres connection string or sqlite for fallback if needed
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost/dbname"
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./financial_agent.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
