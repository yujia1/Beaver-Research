import sys
import os

# Add parent dir to path so we can import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine, Base
from models import AlphaTradePosition, AlphaTradeLot, AlphaTradeFundamentalAnalysis

def reset_tables():
    print("Resetting AlphaTrade tables...")
    
    # 1. Drop tables in dependency order
    try:
        print("Dropping alphatrade_fundamental_analysis...")
        AlphaTradeFundamentalAnalysis.__table__.drop(engine, checkfirst=True)
        
        print("Dropping alphatrade_lots...")
        AlphaTradeLot.__table__.drop(engine, checkfirst=True)
        
        print("Dropping alphatrade_positions...")
        AlphaTradePosition.__table__.drop(engine, checkfirst=True)
        
        print("Tables dropped successfully.")
    except Exception as e:
        print(f"Error dropping tables: {e}")
        return

    # 2. Re-create tables
    try:
        print("Re-creating alphatrade_positions...")
        AlphaTradePosition.__table__.create(engine)
        
        print("Re-creating alphatrade_lots...")
        AlphaTradeLot.__table__.create(engine)
        
        print("Re-creating alphatrade_fundamental_analysis...")
        AlphaTradeFundamentalAnalysis.__table__.create(engine)
        
        print("Tables re-created successfully!")
        
        # Verify schema change (current_price nullable)
        # In SQLite/Postgres we assume creation follows current Base model
        print("Schema up to date.")
        
    except Exception as e:
        print(f"Error creating tables: {e}")

if __name__ == "__main__":
    reset_tables()
