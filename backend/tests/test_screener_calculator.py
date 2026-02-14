"""
Unit tests for Screener Calculator Service

Tests metric calculations using real financial data from PLTR and CRWV
"""
import os
import pytest
from services.market.fmp_financial_service import fetch_all_financial_statements, fetch_stock_quote
from services.market.screener_calculator import (
    calculate_fcf_to_dividends_buybacks_ratio,
    calculate_fcf_to_revenue_ratio,
    calculate_net_debt_to_ebitda,
    calculate_capitalized_costs_to_revenue,
    calculate_days_sales_outstanding,
    calculate_channel_stuffing_risk,
    calculate_ev_to_revenue,
    calculate_ev_to_ebitda,
    calculate_all_metrics,
    check_red_flags
)

# Skip tests if FMP_API_KEY is not set
pytestmark = pytest.mark.skipif(
    not os.getenv("FMP_API_KEY"),
    reason="FMP_API_KEY not set in environment"
)


class TestScreenerCalculator:
    """Test suite for Screener Calculator Service"""
    
    @pytest.fixture(scope="class")
    def pltr_data(self):
        """Fetch PLTR financial data once for all tests"""
        financial_data = fetch_all_financial_statements("PLTR", years=5)
        quote = fetch_stock_quote("PLTR")
        return {
            "income": financial_data["income"],
            "cashflow": financial_data["cashflow"],
            "balance": financial_data["balance"],
            "price": quote.get("price", 0)
        }
    
    @pytest.fixture(scope="class")
    def crwv_data(self):
        """Fetch CRWV financial data once for all tests"""
        financial_data = fetch_all_financial_statements("CRWV", years=5)
        quote = fetch_stock_quote("CRWV")
        return {
            "income": financial_data["income"],
            "cashflow": financial_data["cashflow"],
            "balance": financial_data["balance"],
            "price": quote.get("price", 0)
        }
    
    # Test Cash Flow Sustainability Metrics
    
    def test_fcf_to_dividends_pltr(self, pltr_data):
        """Test FCF to Dividends/Buybacks for PLTR"""
        result = calculate_fcf_to_dividends_buybacks_ratio(pltr_data["cashflow"])
        
        assert result is not None, "Should return a result"
        assert result.name == "FCF to Dividends/Buybacks", "Should have correct name"
        assert result.latest_value is not None, "Should have a latest value"
        assert result.trend is not None, "Should have trend data"
        
        # PLTR typically has low/no dividends, so ratio might be high or undefined
        print(f"\nPLTR FCF/Div+Buybacks: {result.latest_value}")
        print(f"Red Flag: {result.is_red_flag}, Reason: {result.red_flag_reason}")
    
    def test_fcf_to_revenue_pltr(self, pltr_data):
        """Test FCF to Revenue for PLTR"""
        result = calculate_fcf_to_revenue_ratio(
            pltr_data["cashflow"],
            pltr_data["income"]
        )
        
        assert result is not None, "Should return a result"
        assert result.latest_value is not None, "Should have a latest value"
        
        # PLTR should have some FCF/Revenue ratio
        print(f"\nPLTR FCF/Revenue: {result.latest_value:.2%}")
        print(f"Red Flag: {result.is_red_flag}, Reason: {result.red_flag_reason}")
    
    def test_fcf_to_revenue_crwv(self, crwv_data):
        """Test FCF to Revenue for CRWV"""
        result = calculate_fcf_to_revenue_ratio(
            crwv_data["cashflow"],
            crwv_data["income"]
        )
        
        assert result is not None, "Should return a result"
        
        # CRWV might have negative FCF
        print(f"\nCRWV FCF/Revenue: {result.latest_value}")
        print(f"Red Flag: {result.is_red_flag}, Reason: {result.red_flag_reason}")
    
    # Test Balance Sheet Stress Metrics
    
    def test_net_debt_to_ebitda_pltr(self, pltr_data):
        """Test Net Debt to EBITDA for PLTR"""
        result = calculate_net_debt_to_ebitda(
            pltr_data["balance"],
            pltr_data["income"],
            pltr_data["cashflow"]
        )
        
        assert result is not None, "Should return a result"
        assert result.latest_value is not None, "Should have a latest value"
        
        print(f"\nPLTR Net Debt/EBITDA: {result.latest_value:.2f}x")
        print(f"Red Flag: {result.is_red_flag}, Reason: {result.red_flag_reason}")
    
    def test_net_debt_to_ebitda_crwv(self, crwv_data):
        """Test Net Debt to EBITDA for CRWV"""
        result = calculate_net_debt_to_ebitda(
            crwv_data["balance"],
            crwv_data["income"],
            crwv_data["cashflow"]
        )
        
        assert result is not None, "Should return a result"
        
        # CRWV likely has high leverage
        print(f"\nCRWV Net Debt/EBITDA: {result.latest_value}")
        print(f"Red Flag: {result.is_red_flag}, Reason: {result.red_flag_reason}")
    
    def test_capitalized_costs_pltr(self, pltr_data):
        """Test Capitalized Costs to Revenue for PLTR"""
        result = calculate_capitalized_costs_to_revenue(
            pltr_data["cashflow"],
            pltr_data["balance"],
            pltr_data["income"],
            ticker="PLTR"  # Enable peer comparison
        )
        
        assert result is not None, "Should return a result"
        
        print(f"\nPLTR Capitalized Costs/Revenue: {result.latest_value}")
        print(f"Red Flag: {result.is_red_flag}, Reason: {result.red_flag_reason}")
    
    # Test Working Capital Anomalies
    
    def test_dso_pltr(self, pltr_data):
        """Test Days Sales Outstanding for PLTR"""
        result = calculate_days_sales_outstanding(
            pltr_data["balance"],
            pltr_data["income"],
            ticker="PLTR"  # Enable peer comparison
        )
        
        assert result is not None, "Should return a result"
        assert result.latest_value is not None, "Should have a latest value"
        assert result.latest_value > 0, "DSO should be positive"
        
        print(f"\nPLTR DSO: {result.latest_value:.2f} days")
        print(f"Trend: {result.trend.direction if result.trend else 'N/A'}")
        print(f"Red Flag: {result.is_red_flag}, Reason: {result.red_flag_reason}")
    
    def test_dso_crwv(self, crwv_data):
        """Test Days Sales Outstanding for CRWV"""
        result = calculate_days_sales_outstanding(
            crwv_data["balance"],
            crwv_data["income"],
            ticker="CRWV"
        )
        
        assert result is not None, "Should return a result"
        assert result.latest_value is not None, "Should have a latest value"
        
        print(f"\nCRWV DSO: {result.latest_value:.2f} days")
        print(f"Red Flag: {result.is_red_flag}, Reason: {result.red_flag_reason}")
    
    def test_channel_stuffing_pltr(self, pltr_data):
        """Test Channel Stuffing Risk for PLTR"""
        result = calculate_channel_stuffing_risk(
            pltr_data["income"],
            pltr_data["balance"]
        )
        
        assert result is not None, "Should return a result"
        
        # PLTR was flagged in our previous test
        print(f"\nPLTR Channel Stuffing Risk: {result.latest_value}")
        print(f"Red Flag: {result.is_red_flag}, Reason: {result.red_flag_reason}")
        
        # Verify the flag is correct based on our previous manual test
        if result.is_red_flag:
            assert "AR Growth" in result.red_flag_reason, "Should mention AR Growth"
            assert "DSO" in result.red_flag_reason, "Should mention DSO"
    
    def test_channel_stuffing_crwv(self, crwv_data):
        """Test Channel Stuffing Risk for CRWV"""
        result = calculate_channel_stuffing_risk(
            crwv_data["income"],
            crwv_data["balance"]
        )
        
        assert result is not None, "Should return a result"
        
        # CRWV was not flagged in our previous test
        print(f"\nCRWV Channel Stuffing Risk: {result.latest_value}")
        print(f"Red Flag: {result.is_red_flag}, Reason: {result.red_flag_reason}")
    
    # Test Valuation Metrics
    
    def test_ev_to_revenue_pltr(self, pltr_data):
        """Test EV to Revenue for PLTR"""
        result = calculate_ev_to_revenue(
            pltr_data["income"],
            pltr_data["balance"],
            pltr_data["price"],
            ticker="PLTR"
        )
        
        assert result is not None, "Should return a result"
        assert result.latest_value is not None, "Should have a latest value"
        assert result.latest_value > 0, "EV/Revenue should be positive"
        
        print(f"\nPLTR EV/Revenue: {result.latest_value:.2f}x")
        print(f"Red Flag: {result.is_red_flag}, Reason: {result.red_flag_reason}")
    
    def test_ev_to_ebitda_pltr(self, pltr_data):
        """Test EV to EBITDA for PLTR"""
        result = calculate_ev_to_ebitda(
            pltr_data["income"],
            pltr_data["balance"],
            pltr_data["cashflow"],
            pltr_data["price"]
        )
        
        assert result is not None, "Should return a result"
        
        print(f"\nPLTR EV/EBITDA: {result.latest_value}")
        print(f"Red Flag: {result.is_red_flag}, Reason: {result.red_flag_reason}")
    
    # Test calculate_all_metrics
    
    def test_calculate_all_metrics_pltr(self, pltr_data):
        """Test calculating all metrics for PLTR"""
        metrics = calculate_all_metrics(
            income_data=pltr_data["income"],
            cash_flow_data=pltr_data["cashflow"],
            balance_sheet_data=pltr_data["balance"],
            current_price=pltr_data["price"],
            ticker="PLTR"
        )
        
        assert isinstance(metrics, dict), "Should return a dictionary"
        
        # Check all expected metrics are present
        expected_metrics = [
            "fcf_to_dividends_buybacks",
            "fcf_to_revenue",
            "net_debt_to_ebitda",
            "capitalized_costs_to_revenue",
            "days_sales_outstanding",
            "channel_stuffing_risk",
            "ev_to_revenue",
            "ev_to_ebitda"
        ]
        
        for metric_name in expected_metrics:
            assert metric_name in metrics, f"Should have {metric_name} metric"
            assert metrics[metric_name] is not None, f"{metric_name} should not be None"
        
        print(f"\n\nPLTR All Metrics Summary:")
        for name, result in metrics.items():
            print(f"  {result.name}: {result.latest_value} | Red Flag: {result.is_red_flag}")
    
    def test_calculate_all_metrics_crwv(self, crwv_data):
        """Test calculating all metrics for CRWV"""
        metrics = calculate_all_metrics(
            income_data=crwv_data["income"],
            cash_flow_data=crwv_data["cashflow"],
            balance_sheet_data=crwv_data["balance"],
            current_price=crwv_data["price"],
            ticker="CRWV"
        )
        
        assert isinstance(metrics, dict), "Should return a dictionary"
        assert len(metrics) > 0, "Should have metrics"
        
        print(f"\n\nCRWV All Metrics Summary:")
        for name, result in metrics.items():
            print(f"  {result.name}: {result.latest_value} | Red Flag: {result.is_red_flag}")
    
    # Test check_red_flags
    
    def test_check_red_flags_pltr(self, pltr_data):
        """Test red flag checking for PLTR"""
        metrics = calculate_all_metrics(
            income_data=pltr_data["income"],
            cash_flow_data=pltr_data["cashflow"],
            balance_sheet_data=pltr_data["balance"],
            current_price=pltr_data["price"],
            ticker="PLTR"
        )
        
        red_flags = check_red_flags(metrics)
        
        assert isinstance(red_flags, dict), "Should return a dictionary"
        assert "has_red_flags" in red_flags, "Should have has_red_flags field"
        assert "red_flags" in red_flags, "Should have red_flags list"
        assert "strategies_flagged" in red_flags, "Should have strategies_flagged list"
        
        print(f"\n\nPLTR Red Flags Summary:")
        print(f"  Has Red Flags: {red_flags['has_red_flags']}")
        print(f"  Total Red Flags: {len(red_flags['red_flags'])}")
        print(f"  Strategies Flagged: {red_flags['strategies_flagged']}")
        
        for flag in red_flags["red_flags"]:
            print(f"  - {flag['metric']}: {flag['reason']}")
        
        # PLTR should have at least the channel stuffing red flag
        if red_flags["has_red_flags"]:
            assert len(red_flags["red_flags"]) > 0, "Should have at least one red flag"
    
    def test_check_red_flags_crwv(self, crwv_data):
        """Test red flag checking for CRWV"""
        metrics = calculate_all_metrics(
            income_data=crwv_data["income"],
            cash_flow_data=crwv_data["cashflow"],
            balance_sheet_data=crwv_data["balance"],
            current_price=crwv_data["price"],
            ticker="CRWV"
        )
        
        red_flags = check_red_flags(metrics)
        
        assert isinstance(red_flags, dict), "Should return a dictionary"
        
        print(f"\n\nCRWV Red Flags Summary:")
        print(f"  Has Red Flags: {red_flags['has_red_flags']}")
        print(f"  Total Red Flags: {len(red_flags['red_flags'])}")
        print(f"  Strategies Flagged: {red_flags['strategies_flagged']}")
        
        for flag in red_flags["red_flags"]:
            print(f"  - {flag['metric']}: {flag['reason']}")
        
        # CRWV should have red flags (negative FCF, high leverage)
        assert red_flags["has_red_flags"], "CRWV should have red flags"
        assert len(red_flags["red_flags"]) >= 2, "CRWV should have multiple red flags"
    
    # Test trend analysis
    
    def test_trend_direction_pltr(self, pltr_data):
        """Test that trend direction is calculated correctly for PLTR"""
        result = calculate_fcf_to_revenue_ratio(
            pltr_data["cashflow"],
            pltr_data["income"]
        )
        
        if result.trend:
            assert result.trend.direction in ["improving", "declining", "stable"], \
                "Trend direction should be valid"
            assert len(result.trend.values) > 0, "Should have trend values"
            assert len(result.trend.years) > 0, "Should have trend years"
            assert len(result.trend.values) == len(result.trend.years), \
                "Values and years should match"
            
            print(f"\nPLTR FCF/Revenue Trend:")
            print(f"  Direction: {result.trend.direction}")
            print(f"  Values: {[f'{v:.2%}' for v in result.trend.values]}")
            print(f"  Years: {result.trend.years}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
