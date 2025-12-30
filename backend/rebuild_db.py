"""
Database Schema Rebuild Script
Run this to drop all tables and recreate them based on current models.
WARNING: This will delete all data in the database!
"""
from database import Base, engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def rebuild_database():
    """Drop all tables and recreate them from models."""
    try:
        logger.info("Dropping all existing tables...")
        Base.metadata.drop_all(bind=engine)
        logger.info("All tables dropped successfully")
        
        logger.info("Creating all tables from models...")
        Base.metadata.create_all(bind=engine)
        logger.info("All tables created successfully")
        
        logger.info("Database schema rebuild complete!")
        return True
    except Exception as e:
        logger.error(f"Error rebuilding database: {e}")
        return False

if __name__ == "__main__":
    rebuild_database()
