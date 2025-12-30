from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import yfinance as yf
import pandas as pd
import requests
import datetime


router = APIRouter()

class MicroData(BaseModel):
    ticker: str
    company_name: Optional[str] = None
    price: float
    volume: int
    market_cap: Optional[int] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    # New Fields
    financials: Optional[Dict[str, Any]] = None
    balance_sheet: Optional[Dict[str, Any]] = None
    cashflow: Optional[Dict[str, Any]] = None
    ratios: Optional[Dict[str, Any]] = None
    holders: Optional[Dict[str, Any]] = None
    trading: Optional[Dict[str, Any]] = None
    filings: Optional[List[Dict[str, Any]]] = None



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
            "description": info.get("longBusinessSummary"),
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
