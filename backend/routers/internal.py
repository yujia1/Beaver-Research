from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import yfinance as yf
import pandas as pd
import datetime
import random
import os
from pandas_datareader import data as web

router = APIRouter()

# Mapping for timeframe to FRED offset
period_map = {
    "daily": "30d",
    "weekly": "3mo",
    "monthly": "1y",
    "yearly": "5y",
    "max": "max"
}

# FRED indicator configurations
fred_indicators = [
    {
        "indicator": "Consumer Price Index (CPI)",
        "series_id": "CPIAUCSL",
        "description": "Consumer Price Index (YoY %)",
        "category": "Macro",
        "chart_type": "line"
    },
    {
        "indicator": "Unemployment Rate",
        "series_id": "UNRATE",
        "description": "Unemployment Rate (%)",
        "category": "Labor",
        "chart_type": "line"
    },
    {
        "indicator": "10Y Treasury Yield",
        "series_id": "DGS10",
        "description": "10-Year Treasury Yield (%)",
        "category": "Rates",
        "chart_type": "line"
    },
    {
        "indicator": "Consumer Spending (PCE)",
        "series_id": "PCE",
        "description": "Personal Consumption Expenditures ($B)",
        "category": "Macro",
        "chart_type": "line"
    },
    {
        "indicator": "Manufacturing Output",
        "series_id": "IPMAN",
        "description": "Industrial Production: Manufacturing (Index)",
        "category": "Business",
        "chart_type": "line"
    },
    {
        "indicator": "Bank Lending",
        "series_id": "TOTLL",
        "description": "Total Loans and Leases ($B)",
        "category": "Financial",
        "chart_type": "line"
    },
    {
        "indicator": "Financial Stress Index",
        "series_id": "STLFSI4",
        "description": "St. Louis Fed Financial Stress Index",
        "category": "Financial",
        "chart_type": "line"
    },

    {
        "indicator": "Housing Permits",
        "series_id": "PERMIT",
        "description": "New Privately-Owned Housing Units Authorized (Thousands)",
        "category": "Housing",
        "chart_type": "line"
    }
]

def fetch_fred_series(series_id: str, start_date: str):
    """Fetch a series from FRED and return list of {'date': str, 'value': float} sorted oldest to newest."""
    try:
        df = web.DataReader(series_id, 'fred', start=start_date, api_key=os.getenv('FRED_API_KEY'))
        df = df.dropna()
        df = df.reset_index()
        df.columns = ['date', 'value']
        df['date'] = df['date'].dt.strftime('%Y-%m-%d')
        df['value'] = df['value'].astype(float)
        return df.to_dict(orient='records')
    except Exception as e:
        print(f"Error fetching FRED series {series_id}: {e}")
        return []
class HistoricalData(BaseModel):
    date: str
    value: float

class MacroData(BaseModel):
    indicator: str
    value: float
    date: str
    description: str
    category: str
    series_id: Optional[str] = None
    history: Optional[List[Dict[str, Any]]] = None
    chart_type: str = "line" # line, bar

class MicroData(BaseModel):
    ticker: str
    company_name: Optional[str] = None
    price: float
    volume: int
    market_cap: Optional[int] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    # New Fields
    financials: Optional[Dict[str, Any]] = None
    balance_sheet: Optional[Dict[str, Any]] = None
    cashflow: Optional[Dict[str, Any]] = None
    ratios: Optional[Dict[str, Any]] = None
    holders: Optional[Dict[str, Any]] = None
    trading: Optional[Dict[str, Any]] = None
    filings: Optional[List[Dict[str, Any]]] = None

@router.get("/macro", response_model=List[MacroData])
async def get_macro_data(timeframe: str = "monthly"):
    """
    Fetch macro economic data.
    Includes 8 key indicators with historical data (Mocked for now).
    Timeframe options: daily, weekly, monthly, yearly
    """


    start_offset = period_map.get(timeframe, "1y")
    # Convert offset to a date string (approximate)
    from datetime import datetime, timedelta
    
    if start_offset == "max":
        start_date = "1900-01-01" # Fetch all available history
    elif start_offset.endswith('d'):
        days = int(start_offset.rstrip('d'))
        start_date = (datetime.today() - timedelta(days=days)).strftime('%Y-%m-%d')
    elif start_offset.endswith('mo'):
        months = int(start_offset.rstrip('mo'))
        start_date = (datetime.today() - timedelta(days=months*30)).strftime('%Y-%m-%d')
    elif start_offset.endswith('y'):
        years = int(start_offset.rstrip('y'))
        start_date = (datetime.today() - timedelta(days=years*365)).strftime('%Y-%m-%d')
    else:
        start_date = (datetime.today() - timedelta(days=365)).strftime('%Y-%m-%d')

    # Build results list using real data
    results = []
    for cfg in fred_indicators:
        history = fetch_fred_series(cfg["series_id"], start_date)
        # Always append the indicator, even if history is empty (frontend handles empty history)
        latest_val = history[-1]["value"] if history else None
        latest_date = history[-1]["date"] if history else None
        
        results.append({
            "indicator": cfg["indicator"],
            "value": latest_val,
            "date": latest_date,
            "description": cfg["description"],
            "category": cfg["category"],
            "history": history, # Can be empty list
            "chart_type": cfg["chart_type"],
            "series_id": cfg["series_id"] # Ensure series_id is passed to frontend
        })

    # Add FedWatch Tool as it's not from FRED and has a different history format
    today = datetime.today().date()
    
    # Calculate next FOMC meeting date
    def get_next_fomc_meeting_date():
        """Calculate the next FOMC meeting date based on typical schedule"""
        from datetime import date
        today = date.today()
        
        # FOMC meetings typically occur 8 times per year
        # Common months: Jan/Feb, Mar, May, Jun, Jul, Sep, Nov, Dec
        # For 2025, known dates include: Dec 9-10, 2025
        # This is a simplified calculation - in production, you'd want to fetch from FOMC calendar
        
        # Known upcoming FOMC meeting dates (2025-2026)
        fomc_dates = [
            date(2025, 12, 9),   # December 9-10, 2025
            date(2026, 1, 28),   # January 28-29, 2026 (typical)
            date(2026, 3, 18),   # March 18-19, 2026 (typical)
            date(2026, 5, 6),    # May 6-7, 2026 (typical)
            date(2026, 6, 17),   # June 17-18, 2026 (typical)
            date(2026, 7, 29),   # July 29-30, 2026 (typical)
            date(2026, 9, 16),   # September 16-17, 2026 (typical)
            date(2026, 11, 6),   # November 6-7, 2026 (typical)
            date(2026, 12, 15),  # December 15-16, 2026 (typical)
        ]
        
        # Find next meeting date
        for meeting_date in fomc_dates:
            if meeting_date >= today:
                return meeting_date.strftime('%B %d, %Y')
        
        # Fallback if no future date found
        return "TBD"
    
    next_meeting_date = get_next_fomc_meeting_date()
    
    results.append({
        "indicator": "FedWatch Tool",
        "value": 5.25, # Current Fed Funds Rate (Upper)
        "date": str(today),
        "description": f"Target Rate Probabilities (next meeting date: {next_meeting_date})",
        "category": "Monetary",
        "chart_type": "bar",
        "series_id": "FEDWATCH",
        "history": [
            {"date": "Hold", "value": 60},
            {"date": "Cut 25bps", "value": 35},
            {"date": "Cut 50bps", "value": 5},
            {"date": "Hike 25bps", "value": 0}
        ]
    })
    
    return results

@router.get("/macro/series/{series_id}", response_model=MacroData)
async def get_macro_series(series_id: str, timeframe: str = "monthly"):
    """
    Fetch a single macro economic data series.
    """
    start_offset = period_map.get(timeframe, "1y")
    from datetime import datetime, timedelta
    
    # Calculate start date (duplicate logic, could be refactored)
    if start_offset.endswith('d'):
        days = int(start_offset.rstrip('d'))
        start_date = (datetime.today() - timedelta(days=days)).strftime('%Y-%m-%d')
    elif start_offset.endswith('mo'):
        months = int(start_offset.rstrip('mo'))
        start_date = (datetime.today() - timedelta(days=months*30)).strftime('%Y-%m-%d')
    elif start_offset.endswith('y'):
        years = int(start_offset.rstrip('y'))
        start_date = (datetime.today() - timedelta(days=years*365)).strftime('%Y-%m-%d')
    else:
        start_date = (datetime.today() - timedelta(days=365)).strftime('%Y-%m-%d')

    # Handle FedWatch special case
    if series_id == "FEDWATCH":
        today = datetime.today().date()
        
        # Calculate next FOMC meeting date
        def get_next_fomc_meeting_date():
            """Calculate the next FOMC meeting date based on typical schedule"""
            from datetime import date
            today = date.today()
            
            # Known upcoming FOMC meeting dates (2025-2026)
            fomc_dates = [
                date(2025, 12, 9),   # December 9-10, 2025
                date(2026, 1, 28),   # January 28-29, 2026 (typical)
                date(2026, 3, 18),   # March 18-19, 2026 (typical)
                date(2026, 5, 6),    # May 6-7, 2026 (typical)
                date(2026, 6, 17),   # June 17-18, 2026 (typical)
                date(2026, 7, 29),   # July 29-30, 2026 (typical)
                date(2026, 9, 16),   # September 16-17, 2026 (typical)
                date(2026, 11, 6),   # November 6-7, 2026 (typical)
                date(2026, 12, 15),  # December 15-16, 2026 (typical)
            ]
            
            # Find next meeting date
            for meeting_date in fomc_dates:
                if meeting_date >= today:
                    return meeting_date.strftime('%B %d, %Y')
            
            # Fallback if no future date found
            return "TBD"
        
        next_meeting_date = get_next_fomc_meeting_date()
        
        return {
            "indicator": "FedWatch Tool",
            "value": 5.25,
            "date": str(today),
            "description": f"Target Rate Probabilities (next meeting date: {next_meeting_date})",
            "category": "Monetary",
            "chart_type": "bar",
            "series_id": "FEDWATCH",
            "history": [
                {"date": "Hold", "value": 60},
                {"date": "Cut 25bps", "value": 35},
                {"date": "Cut 50bps", "value": 5},
                {"date": "Hike 25bps", "value": 0}
            ]
        }

    # Find config
    cfg = next((item for item in fred_indicators if item["series_id"] == series_id), None)
    if not cfg:
        raise HTTPException(status_code=404, detail="Series not found")

    history = fetch_fred_series(series_id, start_date)
    latest_val = history[-1]["value"] if history else None
    latest_date = history[-1]["date"] if history else None

    return {
        "indicator": cfg["indicator"],
        "value": latest_val,
        "date": latest_date,
        "description": cfg["description"],
        "category": cfg["category"],
        "history": history,
        "chart_type": cfg["chart_type"],
        "series_id": cfg["series_id"]
    }

@router.get("/stock/{ticker}/history")
async def get_stock_history(ticker: str, period: str = "2y"):
    """
    Fetch historical stock price data from Yahoo Finance.
    Period options: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    """
    try:
        stock = yf.Ticker(ticker)
        
        # Map period to interval
        interval_map = {
            "1d": "1m",
            "5d": "5m",
            "1mo": "1d",
            "3mo": "1d",
            "6mo": "1d",
            "1y": "1d",
            "2y": "1d",
            "5y": "1wk",
            "10y": "1mo",
            "ytd": "1d",
            "max": "1mo"
        }
        
        interval = interval_map.get(period, "1d")
        
        hist = stock.history(period=period, interval=interval)
        
        if hist.empty:
            raise HTTPException(status_code=404, detail="No data found for ticker")
        
        # Convert to list of {date, price} objects
        history = []
        for date, row in hist.iterrows():
            history.append({
                "date": date.strftime("%Y-%m-%d"),
                "price": float(row['Close'])
            })
        
        # Get current price info
        info = stock.info
        current_price = float(hist['Close'].iloc[-1])
        
        # Calculate price change from first date in history
        first_price = float(hist['Close'].iloc[0])
        price_change = current_price - first_price
        price_change_percent = (price_change / first_price) * 100 if first_price > 0 else 0
        
        # Calculate today's percentage change (current vs previous close)
        today_change_percent = 0
        if len(hist) >= 2:
            previous_close = float(hist['Close'].iloc[-2])
            today_change = current_price - previous_close
            today_change_percent = (today_change / previous_close) * 100 if previous_close > 0 else 0
        elif 'regularMarketChangePercent' in info:
            # Use yfinance info if available
            today_change_percent = info.get('regularMarketChangePercent', 0)
        
        return {
            "ticker": ticker,
            "company_name": info.get("longName", ticker),
            "history": history,
            "current_price": current_price,
            "price_change": price_change,
            "price_change_percent": price_change_percent,
            "today_change_percent": round(today_change_percent, 2),
            "reference_date": hist.index[0].strftime("%b %Y")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stock data: {str(e)}")

@router.get("/micro/{ticker}", response_model=MicroData)
async def get_micro_data(ticker: str):
    """
    Fetch comprehensive micro economic data (company specific) using yfinance.
    Includes Financials (Annual + LTM), Ratios, Holders, and Trading data.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        history = stock.history(period="1d")
        
        if history.empty:
             raise HTTPException(status_code=404, detail="Ticker not found")

        current_price = history['Close'].iloc[-1]
        volume = history['Volume'].iloc[-1]
        
        # Helper to safely get dataframe as dict
        def df_to_dict(df):
            if df is None or df.empty:
                return {}
            # yfinance returns: rows=metrics, columns=dates
            # We need: {metric_name: {date: value, date: value}}
            result = {}
            for metric in df.index:
                result[metric] = {}
                for date_col in df.columns:
                    # Convert timestamp to string
                    date_str = str(date_col)
                    value = df.loc[metric, date_col]
                    # Handle NaN values and convert numpy types to Python types
                    if pd.isna(value):
                        result[metric][date_str] = None
                    else:
                        # Convert numpy types to Python native types for JSON serialization
                        if hasattr(value, 'item'):  # numpy scalar
                            result[metric][date_str] = value.item()
                        elif isinstance(value, (int, float)):
                            result[metric][date_str] = float(value)
                        else:
                            result[metric][date_str] = value
            return result
        
        # Helper to calculate LTM from quarterly data
        def calculate_ltm(quarterly_df):
            if quarterly_df is None:
                return {}
            # Check if it's a DataFrame
            if not hasattr(quarterly_df, 'empty'):
                return {}
            if quarterly_df.empty or len(quarterly_df.columns) < 4:
                return {}
            # Sum last 4 quarters for each line item
            ltm = {}
            for index in quarterly_df.index:
                try:
                    ltm[index] = quarterly_df.loc[index].iloc[:4].sum()
                except:
                    ltm[index] = None
            return ltm

        # Fetch Annual Financials
        financials_annual = df_to_dict(stock.financials)
        balance_sheet_annual = df_to_dict(stock.balance_sheet)
        cashflow_annual = df_to_dict(stock.cashflow)
        
        # Fetch Quarterly Financials for LTM and quarterly view
        financials_quarterly = stock.quarterly_financials
        balance_sheet_quarterly = stock.quarterly_balance_sheet
        cashflow_quarterly = stock.quarterly_cashflow
        
        # Convert quarterly dataframes to dict
        financials_quarterly_dict = df_to_dict(financials_quarterly)
        balance_sheet_quarterly_dict = df_to_dict(balance_sheet_quarterly)
        cashflow_quarterly_dict = df_to_dict(cashflow_quarterly)
        
        # Calculate LTM
        financials_ltm = calculate_ltm(financials_quarterly)
        balance_sheet_ltm = calculate_ltm(balance_sheet_quarterly)
        cashflow_ltm = calculate_ltm(cashflow_quarterly)
        
        # Combine annual + quarterly + LTM
        financials = {
            "annual": financials_annual,
            "quarterly": financials_quarterly_dict,
            "ltm": financials_ltm
        }
        balance_sheet = {
            "annual": balance_sheet_annual,
            "quarterly": balance_sheet_quarterly_dict,
            "ltm": balance_sheet_ltm
        }
        cashflow = {
            "annual": cashflow_annual,
            "quarterly": cashflow_quarterly_dict,
            "ltm": cashflow_ltm
        }
        
        # Calculate Comprehensive Ratios
        market_cap = info.get("marketCap", 0)
        
        # Get key values for calculations
        try:
            # From financials
            total_revenue = financials_ltm.get("Total Revenue", 0) or 0
            gross_profit = financials_ltm.get("Gross Profit", 0) or 0
            operating_income = financials_ltm.get("Operating Income", 0) or 0
            ebitda = financials_ltm.get("EBITDA", 0) or info.get("ebitda", 0) or 0
            net_income = financials_ltm.get("Net Income", 0) or 0
            interest_expense = abs(financials_ltm.get("Interest Expense", 0) or 0)
            
            # From balance sheet (use most recent quarter)
            total_assets = info.get("totalAssets", 0) or 0
            total_equity = info.get("totalStockholderEquity", 0) or 0
            total_debt = info.get("totalDebt", 0) or 0
            current_assets = balance_sheet_ltm.get("Current Assets", 0) or 0
            current_liabilities = balance_sheet_ltm.get("Current Liabilities", 0) or 0
            inventory = balance_sheet_ltm.get("Inventory", 0) or 0
            accounts_receivable = balance_sheet_ltm.get("Accounts Receivable", 0) or 0
            accounts_payable = balance_sheet_ltm.get("Accounts Payable", 0) or 0
            
            # From cash flow
            operating_cf = cashflow_ltm.get("Operating Cash Flow", 0) or 0
            capex = abs(cashflow_ltm.get("Capital Expenditure", 0) or 0)
            free_cash_flow = operating_cf - capex
            
            # Calculate COGS
            cogs = total_revenue - gross_profit if total_revenue and gross_profit else 0
            
        except Exception as e:
            print(f"Error extracting financial values: {e}")
            total_revenue = ebitda = net_income = total_assets = total_equity = 0
            free_cash_flow = operating_cf = capex = 0
            cogs = inventory = accounts_receivable = accounts_payable = 0
            interest_expense = total_debt = 0
        
        # Profitability Ratios
        profitability = {
            "grossMargins": info.get("grossMargins"),
            "operatingMargins": info.get("operatingMargins"),
            "ebitdaMargins": info.get("ebitdaMargins"),
            "netMargin": (net_income / total_revenue * 100) if total_revenue else None,
            "returnOnAssets": (net_income / total_assets * 100) if total_assets else info.get("returnOnAssets"),
            "returnOnEquity": (net_income / total_equity * 100) if total_equity else info.get("returnOnEquity"),
            "returnOnInvestedCapital": (operating_income / (total_debt + total_equity) * 100) if (total_debt + total_equity) else None,
            "fcfYield": (free_cash_flow / market_cap * 100) if market_cap else None
        }
        
        # Liquidity & Solvency
        liquidity = {
            "currentRatio": info.get("currentRatio"),
            "quickRatio": info.get("quickRatio"),
            "debtToEquity": info.get("debtToEquity"),
            "debtToEbitda": (total_debt / ebitda) if ebitda else None,
            "interestCoverage": (ebitda / interest_expense) if interest_expense else None
        }
        
        # Efficiency Ratios
        efficiency = {
            "inventoryTurnover": (cogs / inventory) if inventory else None,
            "daysSalesOutstanding": (accounts_receivable / total_revenue * 365) if total_revenue else None,
            "daysPayableOutstanding": (accounts_payable / cogs * 365) if cogs else None,
            "assetTurnover": (total_revenue / total_assets) if total_assets else None,
            "workingCapital": current_assets - current_liabilities
        }
        
        # Valuation
        valuation = {
            "trailingPE": info.get("trailingPE"),
            "forwardPE": info.get("forwardPE"),
            "priceToBook": info.get("priceToBook"),
            "enterpriseToEbitda": info.get("enterpriseToEbitda"),
            "priceToSales": info.get("priceToSalesTrailing12Months"),
            "evToRevenue": info.get("enterpriseToRevenue")
        }
        
        ratios = {
            "profitability": profitability,
            "liquidity": liquidity,
            "efficiency": efficiency,
            "valuation": valuation
        }
        
        # Holders (Institutional & Insider)
        holders = {
            "major": df_to_dict(stock.major_holders),
            "institutional": df_to_dict(stock.institutional_holders),
            "insider": df_to_dict(stock.insider_transactions)
        }
        
        # Trading Data
        trading = {
            "shortRatio": info.get("shortRatio"),
            "shortPercentOfFloat": info.get("shortPercentOfFloat"),
            "sharesShort": info.get("sharesShort"),
            "averageVolume": info.get("averageVolume"),
            "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
            "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
            "beta": info.get("beta"),
            "impliedSharesOutstanding": info.get("impliedSharesOutstanding"),
            "options": [],
            "availableOptionsDates": []
        }

        # Try to fetch options data for all available expiry dates
        try:
            options_dates = stock.options
            if options_dates:
                trading["availableOptionsDates"] = list(options_dates)
                
                # Fetch data for all expiry dates (limit to first 20 to avoid timeout)
                options_list = []
                for date in options_dates[:20]:  # Limit to first 20 dates
                    try:
                        chain = stock.option_chain(date)
                        
                        # Calculate totals for this expiration
                        calls_vol = chain.calls['volume'].sum() if not chain.calls.empty else 0
                        puts_vol = chain.puts['volume'].sum() if not chain.puts.empty else 0
                        calls_oi = chain.calls['openInterest'].sum() if not chain.calls.empty else 0
                        puts_oi = chain.puts['openInterest'].sum() if not chain.puts.empty else 0
                        
                        options_list.append({
                            "expirationDate": date,
                            "callsVolume": int(calls_vol),
                            "putsVolume": int(puts_vol),
                            "callsOpenInterest": int(calls_oi),
                            "putsOpenInterest": int(puts_oi),
                            "totalVolume": int(calls_vol + puts_vol),
                            "totalOpenInterest": int(calls_oi + puts_oi)
                        })
                    except Exception as e:
                        print(f"Error fetching chain for {date}: {e}")
                        continue
                
                trading["options"] = options_list
        except Exception as e:
            print(f"Error fetching options data: {e}")

        
        # SEC Filings - Use SEC EDGAR API directly
        filings = []
        try:
            import requests
            # Get CIK from ticker - try multiple methods
            cik = info.get("cik") or info.get("companyOfficers", [{}])[0].get("cik") if info.get("companyOfficers") else None
            
            # If no CIK in info, try to look it up by ticker
            if not cik:
                # Try SEC company tickers JSON
                try:
                    tickers_url = "https://www.sec.gov/files/company_tickers.json"
                    headers = {'User-Agent': 'Financial Dashboard contact@example.com'}
                    resp = requests.get(tickers_url, headers=headers, timeout=10)
                    if resp.status_code == 200:
                        tickers_data = resp.json()
                        # Search for ticker
                        for entry in tickers_data.values():
                            if entry.get("ticker") == ticker.upper():
                                cik = entry.get("cik_str")
                                break
                except:
                    pass
            
            if cik:
                # Pad CIK to 10 digits
                cik_padded = str(cik).zfill(10)
                
                # Fetch filings from SEC EDGAR API
                headers = {'User-Agent': 'Financial Dashboard contact@example.com'}
                url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    sec_data = response.json()
                    recent_filings = sec_data.get("filings", {}).get("recent", {})
                    
                    if recent_filings:
                        # Get arrays of filing data
                        forms = recent_filings.get("form", [])
                        dates = recent_filings.get("filingDate", [])
                        accession_numbers = recent_filings.get("accessionNumber", [])
                        primary_documents = recent_filings.get("primaryDocument", [])
                        
                        # Build filings list (limit to 50 most recent)
                        for i in range(min(50, len(forms))):
                            accession = accession_numbers[i].replace("-", "")
                            primary_doc = primary_documents[i] if i < len(primary_documents) else ""
                            
                            # Direct link to the filing document
                            if primary_doc:
                                filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{primary_doc}"
                            else:
                                # Fallback to filing detail page
                                filing_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik_padded}&type={forms[i]}&dateb=&owner=exclude&count=100"
                            
                            filings.append({
                                "type": forms[i],
                                "date": dates[i],
                                "link": filing_url
                            })
                else:
                    print(f"SEC API returned status {response.status_code} for CIK {cik_padded}")
            else:
                print(f"No CIK found for ticker {ticker}")
        except Exception as e:
            print(f"Error fetching SEC filings: {e}")
            import traceback
            traceback.print_exc()
            # If filings fail, just return empty list

        return {
            "ticker": ticker.upper(),
            "company_name": info.get("longName"),
            "price": round(current_price, 2),
            "volume": int(volume),
            "market_cap": info.get("marketCap"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "financials": financials,
            "balance_sheet": balance_sheet,
            "cashflow": cashflow,
            "ratios": ratios,
            "holders": holders,
            "trading": trading,
            "filings": filings
        }
    except Exception as e:
        print(f"Error fetching micro data for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class OptionsRequest(BaseModel):
    ticker: str
    expirationDates: List[str]

@router.post("/micro/options")
async def get_options_aggregation(request: OptionsRequest):
    """
    Fetch aggregated options data for specified expiration dates.
    """
    try:
        stock = yf.Ticker(request.ticker)
        
        total_calls_vol = 0
        total_puts_vol = 0
        total_calls_oi = 0
        total_puts_oi = 0
        
        for date in request.expirationDates:
            try:
                chain = stock.option_chain(date)
                if not chain.calls.empty:
                    total_calls_vol += chain.calls['volume'].sum()
                    total_calls_oi += chain.calls['openInterest'].sum()
                if not chain.puts.empty:
                    total_puts_vol += chain.puts['volume'].sum()
                    total_puts_oi += chain.puts['openInterest'].sum()
            except Exception as e:
                print(f"Error fetching chain for {date}: {e}")
                continue
        
        return {
            "totalVolume": int(total_calls_vol + total_puts_vol),
            "totalOpenInterest": int(total_calls_oi + total_puts_oi),
            "callsVolume": int(total_calls_vol),
            "putsVolume": int(total_puts_vol),
            "callsOpenInterest": int(total_calls_oi),
            "putsOpenInterest": int(total_puts_oi),
            "selectedDates": request.expirationDates
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class MarketMover(BaseModel):
    ticker: str
    price: float
    change: float
    change_percent: float
    volume: str

class MarketMoversResponse(BaseModel):
    gainers: List[MarketMover]
    losers: List[MarketMover]
    volatile: List[MarketMover]
    active: List[MarketMover]

@router.get("/market-movers", response_model=MarketMoversResponse)
async def get_market_movers():
    """
    Fetch market movers (Gainers, Losers, Volatile, Active) using Real Data.
    Scans a curated list of popular stocks to find top performers.
    """
    # Curated list of active/popular stocks to scan (Expanded for more results)
    tickers = [
        "NVDA", "TSLA", "AAPL", "AMD", "MSFT", "GOOGL", "AMZN", "META", "NFLX", 
        "INTC", "COIN", "GME", "AMC", "PLTR", "SPY", "QQQ", "IWM", "BA", "WMT", 
        "JPM", "V", "PG", "JNJ", "XOM", "CVX", "BAC", "WFC", "C", "GS", "DIS",
        "UBER", "ABNB", "PYPL", "SQ", "ROKU", "SHOP", "SNOW", "CRM", "ADBE", "ORCL",
        "CSCO", "PEP", "KO", "MCD", "NKE", "IBM", "CAT", "MMM", "GE", "F", "GM",
        "T", "VZ", "TMUS", "CMCSA", "PFE", "MRK", "ABBV", "LLY", "UNH", "COST",
        "HD", "LOW", "SBUX", "TGT", "TJX", "LULU", "NIO", "BABA", "JD", "BIDU",
        "ZM", "DOCU", "TWLO", "NET", "CRWD", "PANW", "FTNT", "ZS", "DDOG", "MDB",
        "OKTA", "TEAM", "WDAY", "NOW", "SNPS", "CDNS", "ADSK", "ANSS", "KLAC", "LRCX"
    ]
    
    try:
        # Batch fetch data for efficiency
        # We need 'price' (regularMarketPrice) and 'previousClose' to calculate change
        # yf.Tickers is good for getting info, but download is faster for price history.
        # However, for "current" snapshot, Tickers().tickers[].info is often used but can be slow sequentially.
        # Let's use yf.download for last 2 days to calculate change if market is open/closed.
        # Actually, yf.download returns a DataFrame.
        
        data = yf.download(tickers, period="5d", interval="1d", progress=False)
        
        # Extract latest data
        # data['Close'] is a DataFrame with columns as Tickers
        
        if data.empty:
             raise HTTPException(status_code=500, detail="No data fetched")

        movers = []
        
        # We need the last two rows to calculate change if we want "daily" change
        # If market is open, the last row is current.
        
        try:
            closes = data['Close']
            volumes = data['Volume']
        except KeyError as e:
            # yfinance structure might vary if multi-level columns
            # If only one ticker, it's Series. If multiple, it's DataFrame.
            # But we passed a list, so it should be MultiIndex or DataFrame.
            # Let's check columns again.
            return {"gainers": [], "losers": [], "volatile": [], "active": []}
        
        # Iterate through tickers
        for ticker in tickers:
            try:
                # Get series for this ticker
                # If MultiIndex, accessing by ticker might need level
                if isinstance(closes.columns, pd.MultiIndex):
                     # This shouldn't happen with 'Close' selected unless structure is different
                     pass
                
                if ticker not in closes.columns:
                    continue

                ticker_closes = closes[ticker].dropna()
                if len(ticker_closes) < 2:
                    continue
                
                current_price = float(ticker_closes.iloc[-1])
                prev_close = float(ticker_closes.iloc[-2])
                
                change = current_price - prev_close
                change_percent = (change / prev_close) * 100
                
                # Get volume (last available)
                ticker_vol = volumes[ticker].dropna()
                volume_num = float(ticker_vol.iloc[-1]) if not ticker_vol.empty else 0
                
                # Format volume
                if volume_num >= 1_000_000:
                    volume_str = f"{round(volume_num / 1_000_000, 1)}M"
                elif volume_num >= 1_000:
                    volume_str = f"{round(volume_num / 1_000, 1)}K"
                else:
                    volume_str = str(int(volume_num))

                movers.append({
                    "ticker": ticker,
                    "price": round(current_price, 2),
                    "change": round(change, 2),
                    "change_percent": round(change_percent, 2),
                    "volume": volume_str,
                    "raw_vol": volume_num,
                    "abs_change": abs(change_percent)
                })
            except Exception:
                continue

        # Sort lists
        # Gainers: Top 15 by change_percent desc
        gainers = sorted([m for m in movers if m['change_percent'] > 0], key=lambda x: x['change_percent'], reverse=True)[:15]
        
        # Losers: Top 15 by change_percent asc
        losers = sorted([m for m in movers if m['change_percent'] < 0], key=lambda x: x['change_percent'])[:15]
        
        # Volatile: Top 15 by abs_change desc
        volatile = sorted(movers, key=lambda x: x['abs_change'], reverse=True)[:15]
        
        # Active: Top 15 by raw_vol desc
        active = sorted(movers, key=lambda x: x['raw_vol'], reverse=True)[:15]
        
        # Fallback if empty (e.g. flat market or data issue)
        if not gainers and movers: gainers = movers[:15]
        if not losers and movers: losers = movers[-15:]

        print(f"DEBUG: Movers count: {len(movers)}")
        print(f"DEBUG: Gainers count: {len(gainers)}")
        print(f"DEBUG: Losers count: {len(losers)}")

        return {
            "gainers": gainers,
            "losers": losers,
            "volatile": volatile,
            "active": active
        }

    except Exception as e:
        print(f"Error fetching market movers: {e}")
        # Fallback to empty or mock if critical failure, but let's return empty lists for now to see error
        return {"gainers": [], "losers": [], "volatile": [], "active": []}
