import pandas_datareader.data as web
import pandas as pd
import datetime
import time

def test_fred():
    start = datetime.datetime(2010, 1, 1)
    end = datetime.datetime.now()
    
    print("Fetching FRED data...")
    t0 = time.time()
    try:
        # IPG2211N: Industrial Production: Electric Power Generation, Transmission, and Distribution (Not Seasonally Adjusted)
        df = web.DataReader('IPG2211N', 'fred', start, end)
        print(f"Fetched {len(df)} rows in {time.time() - t0:.2f} seconds")
        print(df.tail())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_fred()
