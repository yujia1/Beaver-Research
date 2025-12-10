"""
Test script for institution holdings API endpoint.
This demonstrates how to test the 13F institution buy/sell feature.
"""
import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
# You'll need to get a token by logging in first
# Or use: docker-compose exec backend python -c "from routers.auth import create_access_token; from models import User; from database import SessionLocal; db = SessionLocal(); user = db.query(User).filter(User.username == 'admin@gmail.com').first(); print(create_access_token({'sub': user.username}))"

def test_institution_holdings(ticker: str, token: str = None):
    """Test the institution holdings endpoint"""
    url = f"{BASE_URL}/api/filing-13f/holdings/{ticker}"
    
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    print(f"Testing institution holdings for: {ticker}")
    print(f"URL: {url}")
    print("-" * 60)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Success! Found {data.get('count', 0)} holdings")
            print()
            
            holdings = data.get('holdings', [])
            if holdings:
                print("Sample holdings:")
                for i, h in enumerate(holdings[:5], 1):
                    print(f"\n{i}. Institution: {h.get('Holder', 'N/A')}")
                    print(f"   Date: {h.get('Date Reported', 'N/A')[:10]}")
                    print(f"   Shares: {h.get('Shares', 0):,}")
                    print(f"   Value: ${h.get('Value', 0):,.2f}")
                    print(f"   Action: {h.get('action', 'N/A')}")
                    print(f"   % Change: {h.get('pctChange', 0):.2f}%")
                    if h.get('sharesChange'):
                        print(f"   Shares Change: {h.get('sharesChange', 0):+,}")
            else:
                print("No holdings found for this ticker.")
                print("This could mean:")
                print("  - No 13F filings have been processed yet")
                print("  - The ticker hasn't been mapped from CUSIP yet")
                print("  - No institutions hold this stock")
            
            return data
        elif response.status_code == 401:
            print("✗ Authentication required")
            print("Please provide a valid token")
            return None
        else:
            print(f"✗ Error: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def get_token_via_login(email: str, password: str):
    """Get access token by logging in"""
    url = f"{BASE_URL}/api/auth/login"
    
    response = requests.post(
        url,
        data={
            "username": email,
            "password": password
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        data = response.json()
        return data.get('access_token')
    else:
        print(f"Login failed: {response.status_code}")
        print(response.text)
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("13F Institution Holdings Test")
    print("=" * 60)
    print()
    
    # Option 1: Test with login
    print("Option 1: Testing with login...")
    token = get_token_via_login("admin@gmail.com", "admin123")
    
    if token:
        print(f"✓ Login successful! Token: {token[:20]}...")
        print()
        
        # Test with a common ticker
        test_tickers = ["AAPL", "TSLA", "MSFT", "GOOGL"]
        
        for ticker in test_tickers:
            result = test_institution_holdings(ticker, token)
            if result and result.get('count', 0) > 0:
                print(f"\n✓ Found data for {ticker}!")
                break
            print()
    else:
        print("✗ Login failed. Using test without authentication...")
        print()
        # Option 2: Test without token (will fail but shows the endpoint)
        test_institution_holdings("AAPL")
    
    print()
    print("=" * 60)
    print("Test Complete")
    print("=" * 60)
    print()
    print("To test in the frontend:")
    print("1. Go to http://localhost:5173/investment")
    print("2. Search for a stock (e.g., TSLA, AAPL)")
    print("3. Click 'Company Basic' → 'Holders' → 'Institutions'")
    print("4. You should see institution holdings with BUY/SELL/HOLD actions")

