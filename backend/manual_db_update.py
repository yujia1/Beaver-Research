from database import engine
from sqlalchemy import text
import logging

# Configure basic logging to stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_manual_migration():
    """
    Run manual migration SQL for production deployment.
    This handles adding the user_id and is_uploaded columns to reports table.
    """
    logger.info("Starting manual DB update script...")
    
    try:
        # Connect to database using engine.begin() for automatic transaction management
        with engine.begin() as conn:
            
            # 1. Add user_id column
            try:
                conn.execute(text("ALTER TABLE reports ADD COLUMN user_id INTEGER;"))
                logger.info("SUCCESS: Added user_id column")
            except Exception as e:
                # Log but continue, common if column exists
                logger.warning(f"SKIPPED add user_id (might already exist): {str(e)}")

            # 2. Add is_uploaded column
            try:
                conn.execute(text("ALTER TABLE reports ADD COLUMN is_uploaded BOOLEAN DEFAULT FALSE;"))
                logger.info("SUCCESS: Added is_uploaded column")
            except Exception as e:
                logger.warning(f"SKIPPED add is_uploaded (might already exist): {str(e)}")

            # 3. Create index for user_id
            try:
                conn.execute(text("CREATE INDEX ix_reports_user_id ON reports(user_id);"))
                logger.info("SUCCESS: Created index ix_reports_user_id")
            except Exception as e:
                logger.warning(f"SKIPPED index creation (might already exist): {str(e)}")
            
            # 4. Add FK constraint (Important for data integrity)
            try:
                conn.execute(text("ALTER TABLE reports ADD CONSTRAINT fk_reports_user_id FOREIGN KEY (user_id) REFERENCES users(id);"))
                logger.info("SUCCESS: Created foreign key fk_reports_user_id")
            except Exception as e:
                logger.warning(f"SKIPPED FK creation (might already exist): {str(e)}")

            # 5. Data Backfill
            try:
                # Find user ID 
                result = conn.execute(text("SELECT id FROM users WHERE username = 'yjia0405@gmail.com'"))
                user_row = result.first()
                if user_row:
                    user_id = user_row[0]
                    logger.info(f"Found target user ID: {user_id}")
                    
                    # Update reports
                    update_result = conn.execute(text(f"UPDATE reports SET user_id = {user_id} WHERE user_id IS NULL"))
                    logger.info(f"SUCCESS: Backfilled {update_result.rowcount} reports with user_id {user_id}")
                else:
                    logger.error("ERROR: User 'yjia0405@gmail.com' not found! Cannot backfill reports.")
            except Exception as e:
                logger.error(f"ERROR backfilling user_id: {str(e)}")

            try:
                update_result = conn.execute(text("UPDATE reports SET is_uploaded = FALSE WHERE is_uploaded IS NULL"))
                logger.info(f"SUCCESS: Set default is_uploaded=False for {update_result.rowcount} rows")
            except Exception as e:
                logger.error(f"ERROR backfilling is_uploaded: {str(e)}")

        logger.info("Manual DB update script execution finished.")
        
    except Exception as e:
        logger.critical(f"FATAL ERROR: Script failed execution: {e}")

if __name__ == "__main__":
    run_manual_migration()
