"""
Scheduler for 13F filing processing.
Runs 2-3 days after each 13F deadline (45 days after quarter-end).
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import logging

from database import SessionLocal
from services.filing_13f_service import filing_13f_service

logger = logging.getLogger(__name__)

def process_13f_filings():
    """Process 13F filings for the current quarter"""
    try:
        db = SessionLocal()
        try:
            # Check if scheduler is enabled
            from models import SystemConfig
            enabled_config = db.query(SystemConfig).filter(SystemConfig.key == "13f_scheduler_enabled").first()
            if enabled_config and enabled_config.value.lower() == "false":
                logger.info("13F Scheduler is disabled in SystemConfig, skipping run")
                return

            now = datetime.now()
            current_quarter = filing_13f_service.get_quarter_from_date(now)
            
            # Check delay config
            delay_config = db.query(SystemConfig).filter(SystemConfig.key == "13f_processing_delay_days").first()
            delay_days = int(delay_config.value) if delay_config else 3
            
            # Check if we should process this quarter
            if filing_13f_service.should_process_quarter(current_quarter, delay_days):
                logger.info(f"Processing 13F filings for quarter {current_quarter}")
                
                result = filing_13f_service.process_batch(db, quarters=[current_quarter])
                logger.info(f"13F processing completed: {result}")
            else:
                logger.info(f"Not yet time to process quarter {current_quarter}")
        finally:
            db.close()
    except Exception as e:
        db.rollback()
        logger.error(f"Error in 13F processing scheduler: {e}", exc_info=True)

def setup_13f_scheduler():
    """Setup and start the 13F processing scheduler"""
    scheduler = BackgroundScheduler()
    
    # Schedule to run daily at 2 AM to check for new filings
    # The service will check if it's 2-3 days after the deadline
    scheduler.add_job(
        process_13f_filings,
        trigger=CronTrigger(hour=2, minute=0),
        id='process_13f_filings',
        name='Process 13F filings',
        replace_existing=True
    )
    
    # Also schedule specific dates for each quarter deadline + 2 days
    # Q1 deadline: May 15 -> Process May 17-18
    scheduler.add_job(
        process_13f_filings,
        trigger=CronTrigger(month=5, day=17, hour=2, minute=0),
        id='process_13f_q1',
        name='Process 13F Q1 filings',
        replace_existing=True
    )
    
    # Q2 deadline: Aug 14 -> Process Aug 16-17
    scheduler.add_job(
        process_13f_filings,
        trigger=CronTrigger(month=8, day=16, hour=2, minute=0),
        id='process_13f_q2',
        name='Process 13F Q2 filings',
        replace_existing=True
    )
    
    # Q3 deadline: Nov 14 -> Process Nov 16-17
    scheduler.add_job(
        process_13f_filings,
        trigger=CronTrigger(month=11, day=16, hour=2, minute=0),
        id='process_13f_q3',
        name='Process 13F Q3 filings',
        replace_existing=True
    )
    
    # Q4 deadline: Feb 14 -> Process Feb 16-17
    scheduler.add_job(
        process_13f_filings,
        trigger=CronTrigger(month=2, day=16, hour=2, minute=0),
        id='process_13f_q4',
        name='Process 13F Q4 filings',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("13F filing scheduler started")
    
    return scheduler

