from database import engine
from sqlalchemy import text
import logging

# Configure basic logging to stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_step(conn, step_name, sql, ignore_errors=True):
    """Run a single SQL step with its own transaction management."""
    try:
        logger.info(f"Running step: {step_name}")
        conn.execute(text(sql))
        conn.commit()
        logger.info(f"SUCCESS: {step_name}")
    except Exception as e:
        conn.rollback() # Important: Rollback the failed transaction so the connection is usable again
        if ignore_errors:
            logger.warning(f"SKIPPED {step_name} (Error: {e})")
        else:
            logger.error(f"FAILED {step_name} (Error: {e})")
            raise e

def run_manual_migration():
    """
    Run manual migration SQL for production deployment.
    Executes each step safely to handle existing columns/constraints.
    """
    logger.info("Starting manual DB update script (Robust Mode)...")
    
    # Use a raw connection to control transactions manually
    with engine.connect() as conn:
        
        # 1. Add user_id column
        # Using IF NOT EXISTS is postgres-friendly, but standard SQL fallback is try-catch which we do in run_step
        run_step(conn, "Add user_id column", "ALTER TABLE reports ADD COLUMN IF NOT EXISTS user_id INTEGER;")

        # 2. Add is_uploaded column
        run_step(conn, "Add is_uploaded column", "ALTER TABLE reports ADD COLUMN IF NOT EXISTS is_uploaded BOOLEAN DEFAULT FALSE;")

        # 3. Create index for user_id
        run_step(conn, "Create index ix_reports_user_id", "CREATE INDEX IF NOT EXISTS ix_reports_user_id ON reports(user_id);")
        
        # 4. Add FK constraint
        # Postgres doesn't support IF NOT EXISTS for constraints directly in ADD CONSTRAINT.
        # We can try it, and if it fails (duplicate), the rollback handles it.
        run_step(conn, "Add FK constraint", "ALTER TABLE reports ADD CONSTRAINT fk_reports_user_id FOREIGN KEY (user_id) REFERENCES users(id);")

        # 5. Data Backfill - User ID
        try:
            logger.info("Running Step: Backfill User ID")
            result = conn.execute(text("SELECT id FROM users WHERE username = 'yjia0405@gmail.com'"))
            user_row = result.first()
            if user_row:
                user_id = user_row[0]
                logger.info(f"Found target user ID: {user_id}")
                conn.execute(text(f"UPDATE reports SET user_id = {user_id} WHERE user_id IS NULL"))
                conn.commit()
                logger.info(f"SUCCESS: Backfilled reports with user_id {user_id}")
            else:
                logger.warning("User 'yjia0405@gmail.com' not found. Skipping backfill.")
        except Exception as e:
            conn.rollback()
            logger.error(f"ERROR backfilling user_id: {e}")

        # 6. Data Backfill - is_uploaded
        try:
            logger.info("Running Step: Backfill is_uploaded")
            conn.execute(text("UPDATE reports SET is_uploaded = FALSE WHERE is_uploaded IS NULL"))
            conn.commit()
            logger.info("SUCCESS: Backfilled is_uploaded default values")
        except Exception as e:
            conn.rollback()
            logger.error(f"ERROR backfilling is_uploaded: {e}")

    logger.info("Manual DB update script execution finished.")

if __name__ == "__main__":
    run_manual_migration()
