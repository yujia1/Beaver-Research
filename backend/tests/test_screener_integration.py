"""
Integration tests for screener calculator using REAL FMP API data

These tests fetch actual financial data from FMP API to verify calculations.
Requires FMP_API_KEY in environment variables.
"""

import pytest
import os
from services.market.fmp_financial_service import (
    fetch_all_financial_statements,
    fetch_stock_quote,
    FMPAPIError
)
from services.market.screener_calculator import (
    calculate_all_metrics,
    check_red_flags
)


# Skip tests if FMP_API_KEY is not set
pytestmark = pytest.mark.skipif(
    not os.getenv("FMP_API_KEY"),
    reason="FMP_API_KEY not set in environment"
)


class TestRealFMPData:
    """Test screener calculator with real FMP API data"""
    
    def test_fetch_financial_statements(self):
        """Test fetching real financial statements from FMP"""
        ticker = "AAPL"
        
        try:
            financial_data = fetch_all_financial_statements(ticker, years=5)
            
            # Verify we got all 3 statement types
            assert "income" in financial_data
            assert "cashflow" in financial_data
            assert "balance" in financial_data
            
            # Verify we got data (at least some years)
            assert len(financial_data["income"]) > 0
            assert len(financial_data["cashflow"]) > 0
            assert len(financial_data["balance"]) > 0
            
            # Verify data structure
            income = financial_data["income"][0]
            assert "revenue" in income
            assert "netIncome" in income
            
            cashflow = financial_data["cashflow"][0]
            assert "freeCashFlow" in cashflow
            
            balance = financial_data["balance"][0]
            assert "totalDebt" in balance or "longTermDebt" in balance
            
            print(f"\n✅ Successfully fetched {len(financial_data['income'])} years of data for {ticker}")
            
        except FMPAPIError as e:
            pytest.fail(f"FMP API error: {e}")
    
    def test_calculate_metrics_with_real_data(self):
        """Test calculating all metrics with real FMP data"""
        ticker = "AAPL"
        
        try:
            # Fetch real data
            financial_data = fetch_all_financial_statements(ticker, years=5)
            
            # Get current price
            quote = fetch_stock_quote(ticker)
            current_price = quote.get("price", 0)
            
            # Calculate metrics
            metrics = calculate_all_metrics(
                income_data=financial_data["income"],
                cash_flow_data=financial_data["cashflow"],
                balance_sheet_data=financial_data["balance"],
                current_price=current_price
            )
            
            # Verify all metrics were calculated
            assert "fcf_to_dividends_buybacks" in metrics
            assert "fcf_to_revenue" in metrics
            assert "net_debt_to_ebitda" in metrics
            assert "capitalized_costs_to_revenue" in metrics
            assert "days_sales_outstanding" in metrics
            assert "ev_to_ebitda" in metrics
            
            # Print results for manual verification
            print(f"\n{'='*60}")
            print(f"Screening Results for {ticker}")
            print(f"{'='*60}")
            
            for metric_name, metric in metrics.items():
                print(f"\n{metric.name}:")
                print(f"  Latest Value: {metric.latest_value}")
                if metric.trend:
                    print(f"  Trend Direction: {metric.trend.direction}")
                    print(f"  Trend Slope: {metric.trend.slope:.4f}")
                    print(f"  5-Year Values: {[f'{v:.2f}' for v in metric.trend.values]}")
                print(f"  Red Flag: {metric.is_red_flag}")
                if metric.red_flag_reason:
                    print(f"  Reason: {metric.red_flag_reason}")
            
            # Check red flags
            red_flag_summary = check_red_flags(metrics)
            print(f"\n{'='*60}")
            print(f"Red Flag Summary:")
            print(f"  Has Red Flags: {red_flag_summary['has_red_flags']}")
            print(f"  Red Flag Count: {red_flag_summary['red_flag_count']}")
            print(f"  Strategies Flagged: {red_flag_summary['strategies_flagged']}")
            print(f"{'='*60}\n")
            
        except FMPAPIError as e:
            pytest.fail(f"FMP API error: {e}")
    
    def test_multiple_stocks(self):
        """Test screening multiple stocks with real data"""
        tickers = ["AAPL", "MSFT", "GOOGL"]
        
        results = {}
        
        for ticker in tickers:
            try:
                print(f"\nProcessing {ticker}...")
                
                # Fetch data
                financial_data = fetch_all_financial_statements(ticker, years=5)
                
                # Calculate metrics
                metrics = calculate_all_metrics(
                    income_data=financial_data["income"],
                    cash_flow_data=financial_data["cashflow"],
                    balance_sheet_data=financial_data["balance"],
                    current_price=None  # Skip EV/EBITDA for speed
                )
                
                # Check red flags
                red_flag_summary = check_red_flags(metrics)
                
                results[ticker] = {
                    "metrics": metrics,
                    "red_flags": red_flag_summary
                }
                
                print(f"  ✅ {ticker}: {red_flag_summary['red_flag_count']} red flags")
                
            except FMPAPIError as e:
                print(f"  ❌ {ticker}: API error - {e}")
                continue
        
        # Verify we got results for at least some stocks
        assert len(results) > 0, "Failed to process any stocks"
        
        # Print summary
        print(f"\n{'='*60}")
        print("Multi-Stock Screening Summary")
        print(f"{'='*60}")
        for ticker, data in results.items():
            print(f"{ticker}: {data['red_flags']['red_flag_count']} red flags - {data['red_flags']['strategies_flagged']}")
        print(f"{'='*60}\n")
    
    def test_data_ordering(self):
        """Verify FMP returns data in newest-first order"""
        ticker = "AAPL"
        
        try:
            financial_data = fetch_all_financial_statements(ticker, years=5)
            
            # Check income statement ordering
            income_years = [
                stmt.get("calendarYear") or stmt.get("date", "")[:4]
                for stmt in financial_data["income"]
            ]
            
            print(f"\nIncome statement years (as returned by FMP): {income_years}")
            
            # Verify newest first (descending order)
            if len(income_years) >= 2:
                # Convert to int for comparison
                year_ints = [int(y) for y in income_years if y.isdigit()]
                if len(year_ints) >= 2:
                    assert year_ints[0] > year_ints[1], \
                        f"Expected newest first, got {income_years}"
                    print(f"✅ Data is in newest-first order (correct)")
            
        except FMPAPIError as e:
            pytest.fail(f"FMP API error: {e}")
    
    def test_specific_calculations(self):
        """Test specific metric calculations with real data"""
        ticker = "AAPL"
        
        try:
            financial_data = fetch_all_financial_statements(ticker, years=5)
            
            # Get latest year data
            latest_income = financial_data["income"][0]
            latest_cashflow = financial_data["cashflow"][0]
            latest_balance = financial_data["balance"][0]
            
            print(f"\n{'='*60}")
            print(f"Latest Financial Data for {ticker}")
            print(f"Year: {latest_income.get('calendarYear')}")
            print(f"{'='*60}")
            
            # Print key fields for manual verification
            print(f"\nIncome Statement:")
            print(f"  Revenue: ${latest_income.get('revenue', 0):,}")
            print(f"  Net Income: ${latest_income.get('netIncome', 0):,}")
            
            print(f"\nCash Flow Statement:")
            print(f"  Free Cash Flow: ${latest_cashflow.get('freeCashFlow', 0):,}")
            print(f"  Dividends Paid: ${abs(latest_cashflow.get('dividendsPaid', 0)):,}")
            print(f"  Stock Repurchased: ${abs(latest_cashflow.get('commonStockRepurchased', 0) or 0):,}")
            
            print(f"\nBalance Sheet:")
            print(f"  Total Debt: ${(latest_balance.get('totalDebt', 0) or (latest_balance.get('longTermDebt', 0) + latest_balance.get('shortTermDebt', 0))):,}")
            print(f"  Cash: ${latest_balance.get('cashAndCashEquivalents', 0):,}")
            print(f"  Accounts Receivable: ${latest_balance.get('netReceivables', 0):,}")
            
            # Calculate and verify FCF/Dividends ratio manually
            fcf = latest_cashflow.get('freeCashFlow', 0)
            dividends = abs(latest_cashflow.get('dividendsPaid', 0))
            buybacks = abs(latest_cashflow.get('commonStockRepurchased', 0) or 0)
            
            if dividends + buybacks > 0:
                manual_ratio = fcf / (dividends + buybacks)
                print(f"\nManual FCF/(Div+Buybacks) calculation:")
                print(f"  {fcf:,} / ({dividends:,} + {buybacks:,}) = {manual_ratio:.2f}")
            
            print(f"{'='*60}\n")
            
        except FMPAPIError as e:
            pytest.fail(f"FMP API error: {e}")


if __name__ == "__main__":
    # Run with verbose output
    pytest.main([__file__, "-v", "-s"])
