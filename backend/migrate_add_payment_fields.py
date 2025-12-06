"""
Migration script to add payment-related fields to User model.
Run this script once to update existing database tables.
"""
from database import SessionLocal, engine
from sqlalchemy import text
import models

def migrate():
    """Add payment fields to User table if they don't exist"""
    db = SessionLocal()
    try:
        # For SQLite, we can use PRAGMA to check table info
        if 'sqlite' in str(engine.url):
            # SQLite migration
            with engine.connect() as conn:
                # Check if has_paid column exists
                result = conn.execute(text("PRAGMA table_info(users)"))
                columns = [row[1] for row in result]
                
                if 'has_paid' not in columns:
                    print("Adding has_paid column...")
                    conn.execute(text("ALTER TABLE users ADD COLUMN has_paid BOOLEAN DEFAULT 0 NOT NULL"))
                    conn.commit()
                    print("✓ Added has_paid column")
                else:
                    print("✓ has_paid column already exists")
                
                if 'payment_transaction_id' not in columns:
                    print("Adding payment_transaction_id column...")
                    conn.execute(text("ALTER TABLE users ADD COLUMN payment_transaction_id VARCHAR"))
                    conn.commit()
                    print("✓ Added payment_transaction_id column")
                else:
                    print("✓ payment_transaction_id column already exists")
                
                if 'payment_date' not in columns:
                    print("Adding payment_date column...")
                    conn.execute(text("ALTER TABLE users ADD COLUMN payment_date DATETIME"))
                    conn.commit()
                    print("✓ Added payment_date column")
                else:
                    print("✓ payment_date column already exists")
        else:
            # For PostgreSQL and other databases, use SQLAlchemy
            print("Using SQLAlchemy migration for non-SQLite database...")
            # The columns will be added automatically when models are recreated
            # For existing databases, you may need to use Alembic or manual SQL
            print("Note: For PostgreSQL/MySQL, consider using Alembic migrations")
        
        print("\n✓ Migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Running payment fields migration...")
    migrate()

