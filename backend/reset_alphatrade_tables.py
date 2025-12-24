import sys
import os

# Add current dir to path (backend/) so we can import modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

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
        print("Schema up to date.")
        
    except Exception as e:
        print(f"Error creating tables: {e}")

if __name__ == "__main__":
    reset_tables()
