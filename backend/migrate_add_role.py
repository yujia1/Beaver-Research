"""
Migration script to add role column to users table.
Run this if the users table exists but doesn't have the role column.
"""
from database import engine
from sqlalchemy import text, inspect

def migrate_add_role():
    """Add role column to users table if it doesn't exist"""
    inspector = inspect(engine)
    
    if 'users' not in inspector.get_table_names():
        print("Users table doesn't exist. It will be created with the role column.")
        return
    
    # Check if column exists
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'role' in columns:
        print("Role column already exists in users table.")
        return
    
    print("Adding role column to users table...")
    with engine.connect() as conn:
        try:
            # For SQLite
            if 'sqlite' in str(engine.url):
                conn.execute(text('ALTER TABLE users ADD COLUMN role VARCHAR DEFAULT "user" NOT NULL'))
            else:
                # For PostgreSQL and other databases
                conn.execute(text('ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT \'user\' NOT NULL'))
            conn.commit()
            print("Role column added successfully!")
        except Exception as e:
            conn.rollback()
            print(f"Error adding role column: {e}")
            raise

if __name__ == "__main__":
    migrate_add_role()

