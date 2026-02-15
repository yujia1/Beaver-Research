import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import FlaggedCompany
import json

db = SessionLocal()
try:
    results = db.query(FlaggedCompany).all()
    print(f"Found {len(results)} records.")
    for r in results:
        print(f"ID: {r.id}, Ticker: '{r.ticker}', Name: '{r.company_name}'")
        print(f"  Type of RedFlags: {type(r.red_flags)}")
        rf_str = json.dumps(r.red_flags, default=str)[:200]
        print(f"  RedFlags: {rf_str}...")
        
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
