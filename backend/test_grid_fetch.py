import gridstatus
import pandas as pd
import time

def test_fetch():
    iso = gridstatus.NYISO()
    end = pd.Timestamp.now(tz="America/New_York")
    start = end - pd.Timedelta(days=365)
    
    print(f"Fetching data from {start} to {end}...")
    t0 = time.time()
    # Fetching 1 year of data might be split into chunks by the library or I might need to
    # But let's try get_load for a shorter period first, say 1 month, to estimate.
    # gridstatus get_load usually fetches daily files for some ISOs.
    
    try:
        # Let's try 1 year
        start_1y = end - pd.Timedelta(days=365)
        data = iso.get_load(start=start_1y, end=end)
        print(f"Fetched 365 days in {time.time() - t0:.2f} seconds")
        print(f"Rows: {len(data)}")
        print(data.head())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_fetch()
