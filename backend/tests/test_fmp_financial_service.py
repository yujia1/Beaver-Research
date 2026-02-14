"""
Unit tests for FMP Financial Service

Tests financial data fetching from FMP API using real tickers (PLTR, CRWV)
"""
import os
import pytest
from services.market.fmp_financial_service import (
    fetch_income_statement,
    fetch_cash_flow_statement,
    fetch_balance_sheet,
    fetch_all_financial_statements,
    fetch_stock_quote,
    FMPAPIError
)

# Skip tests if FMP_API_KEY is not set
pytestmark = pytest.mark.skipif(
    not os.getenv("FMP_API_KEY"),
    reason="FMP_API_KEY not set in environment"
)


class TestFMPFinancialService:
    """Test suite for FMP Financial Service"""
    
    @pytest.fixture
    def test_tickers(self):
        """Provide test tickers"""
        return ["PLTR", "CRWV"]
    
    def test_fetch_income_statement_pltr(self):
        """Test fetching income statement for PLTR"""
        data = fetch_income_statement("PLTR", years=5)
        
        assert isinstance(data, list), "Should return a list"
        assert len(data) > 0, "Should have at least one year of data"
        assert len(data) <= 5, "Should not exceed requested years"
        
        # Check required fields
        first_year = data[0]
        assert "revenue" in first_year, "Should have revenue field"
        assert "netIncome" in first_year, "Should have netIncome field"
        assert "date" in first_year or "calendarYear" in first_year, "Should have date field"
        
        # Verify data is sorted (most recent first)
        if len(data) > 1:
            year1 = first_year.get("calendarYear") or first_year.get("date", "")[:4]
            year2 = data[1].get("calendarYear") or data[1].get("date", "")[:4]
            assert year1 >= year2, "Data should be sorted by year descending"
    
    def test_fetch_income_statement_crwv(self):
        """Test fetching income statement for CRWV"""
        data = fetch_income_statement("CRWV", years=5)
        
        assert isinstance(data, list), "Should return a list"
        assert len(data) > 0, "Should have at least one year of data"
        
        # CRWV might have less than 5 years of data
        first_year = data[0]
        assert "revenue" in first_year, "Should have revenue field"
    
    def test_fetch_cash_flow_statement_pltr(self):
        """Test fetching cash flow statement for PLTR"""
        data = fetch_cash_flow_statement("PLTR", years=5)
        
        assert isinstance(data, list), "Should return a list"
        assert len(data) > 0, "Should have at least one year of data"
        
        # Check required fields
        first_year = data[0]
        assert "freeCashFlow" in first_year or "operatingCashFlow" in first_year, \
            "Should have cash flow fields"
        assert "date" in first_year or "calendarYear" in first_year, "Should have date field"
    
    def test_fetch_balance_sheet_pltr(self):
        """Test fetching balance sheet for PLTR"""
        data = fetch_balance_sheet("PLTR", years=5)
        
        assert isinstance(data, list), "Should return a list"
        assert len(data) > 0, "Should have at least one year of data"
        
        # Check required fields
        first_year = data[0]
        assert "totalAssets" in first_year, "Should have totalAssets field"
        assert "totalLiabilities" in first_year, "Should have totalLiabilities field"
        assert "cashAndCashEquivalents" in first_year, "Should have cash field"
    
    def test_fetch_all_financial_statements_pltr(self):
        """Test fetching all financial statements for PLTR"""
        data = fetch_all_financial_statements("PLTR", years=5)
        
        assert isinstance(data, dict), "Should return a dictionary"
        assert "income" in data, "Should have income statements"
        assert "cashflow" in data, "Should have cash flow statements"
        assert "balance" in data, "Should have balance sheets"
        
        # Verify all have data
        assert len(data["income"]) > 0, "Income statements should not be empty"
        assert len(data["cashflow"]) > 0, "Cash flow statements should not be empty"
        assert len(data["balance"]) > 0, "Balance sheets should not be empty"
        
        # Verify same number of years for all statements
        assert len(data["income"]) == len(data["cashflow"]) == len(data["balance"]), \
            "All statements should have same number of years"
    
    def test_fetch_all_financial_statements_crwv(self):
        """Test fetching all financial statements for CRWV"""
        data = fetch_all_financial_statements("CRWV", years=5)
        
        assert isinstance(data, dict), "Should return a dictionary"
        assert "income" in data, "Should have income statements"
        assert "cashflow" in data, "Should have cash flow statements"
        assert "balance" in data, "Should have balance sheets"
        
        # All should have at least some data
        assert len(data["income"]) > 0, "Income statements should not be empty"
        assert len(data["cashflow"]) > 0, "Cash flow statements should not be empty"
        assert len(data["balance"]) > 0, "Balance sheets should not be empty"
    
    def test_fetch_stock_quote_pltr(self):
        """Test fetching stock quote for PLTR"""
        quote = fetch_stock_quote("PLTR")
        
        assert isinstance(quote, dict), "Should return a dictionary"
        assert "price" in quote, "Should have price field"
        assert "symbol" in quote, "Should have symbol field"
        assert quote["symbol"] == "PLTR", "Symbol should match request"
        
        # Price should be a positive number
        price = quote["price"]
        assert isinstance(price, (int, float)), "Price should be a number"
        assert price > 0, "Price should be positive"
    
    def test_fetch_stock_quote_crwv(self):
        """Test fetching stock quote for CRWV"""
        quote = fetch_stock_quote("CRWV")
        
        assert isinstance(quote, dict), "Should return a dictionary"
        assert "price" in quote, "Should have price field"
        assert "symbol" in quote, "Should have symbol field"
        assert quote["symbol"] == "CRWV", "Symbol should match request"
    
    def test_fetch_invalid_ticker(self):
        """Test fetching data for invalid ticker"""
        with pytest.raises(FMPAPIError):
            fetch_income_statement("INVALID_TICKER_XYZ123", years=5)
    
    def test_fetch_with_different_years(self):
        """Test fetching different number of years"""
        data_3y = fetch_income_statement("PLTR", years=3)
        data_5y = fetch_income_statement("PLTR", years=5)
        
        assert len(data_3y) <= 3, "Should return at most 3 years"
        assert len(data_5y) <= 5, "Should return at most 5 years"
        assert len(data_5y) >= len(data_3y), "5 years should have more or equal data"
    
    def test_data_consistency_pltr(self):
        """Test data consistency across statements for PLTR"""
        data = fetch_all_financial_statements("PLTR", years=5)
        
        # Get years from each statement type
        income_years = [
            stmt.get("calendarYear") or stmt.get("date", "")[:4] 
            for stmt in data["income"]
        ]
        cashflow_years = [
            stmt.get("calendarYear") or stmt.get("date", "")[:4] 
            for stmt in data["cashflow"]
        ]
        balance_years = [
            stmt.get("calendarYear") or stmt.get("date", "")[:4] 
            for stmt in data["balance"]
        ]
        
        # All should have the same years
        assert income_years == cashflow_years == balance_years, \
            "All statements should have matching years"
    
    def test_revenue_values_pltr(self):
        """Test that revenue values are reasonable for PLTR"""
        data = fetch_income_statement("PLTR", years=5)
        
        for stmt in data:
            revenue = stmt.get("revenue", 0)
            assert revenue > 0, "Revenue should be positive"
            assert revenue > 1_000_000, "PLTR revenue should be > $1M (sanity check)"
    
    def test_cash_flow_values_crwv(self):
        """Test that cash flow values exist for CRWV"""
        data = fetch_cash_flow_statement("CRWV", years=5)
        
        for stmt in data:
            # CRWV might have negative FCF, so just check it exists
            assert "freeCashFlow" in stmt or "operatingCashFlow" in stmt, \
                "Should have cash flow data"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
