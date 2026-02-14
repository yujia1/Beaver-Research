"""
Manual test for CRWV to verify channel stuffing risk and other metrics
"""
import os
import pytest
from services.market.fmp_financial_service import fetch_all_financial_statements, fetch_stock_quote, FMPAPIError
from services.market.screener_calculator import calculate_all_metrics, check_red_flags

# Skip tests if FMP_API_KEY is not set
pytestmark = pytest.mark.skipif(
    not os.getenv("FMP_API_KEY"),
    reason="FMP_API_KEY not set in environment"
)

def test_crwv_channel_stuffing():
    """Test CRWV for channel stuffing risk"""
    ticker = "CRWV"
    print(f"\nAnalyzing {ticker}...")
    
    try:
        financial_data = fetch_all_financial_statements(ticker, years=5)
        quote = fetch_stock_quote(ticker)
        current_price = quote.get("price", 0)
        
        metrics = calculate_all_metrics(
            income_data=financial_data["income"],
            cash_flow_data=financial_data["cashflow"],
            balance_sheet_data=financial_data["balance"],
            current_price=current_price
        )
        
        # Check Channel Stuffing Risk
        csr = metrics.get("channel_stuffing_risk")
        dso = metrics.get("days_sales_outstanding")
        
        print(f"\n--- Channel Stuffing Analysis for {ticker} ---")
        if csr:
            print(f"Is Red Flag: {csr.is_red_flag}")
            if csr.is_red_flag:
                 print(f"Reason: {csr.red_flag_reason}")
            else:
                 print("Reason: Not flagged")
            print(f"Latest Value (Spread): {csr.latest_value}")
        else:
            print("Channel Stuffing Risk metric missing")
            
        print(f"\n--- DSO Analysis ---")
        if dso:
            print(f"Latest DSO: {dso.latest_value}")
            if dso.trend:
                print(f"DSO Trend: {[round(v, 2) for v in dso.trend.values]}")
                print(f"Direction: {dso.trend.direction}")
        
        # Check all Red Flags
        red_flags_summary = check_red_flags(metrics)
        print(f"\n--- All Red Flags ---")
        for flag in red_flags_summary["red_flags"]:
            print(f"- {flag['metric']}: {flag['reason']}")
            
    except FMPAPIError as e:
        print(f"FMP API Error: {e}")
        pytest.fail(f"FMP API Error: {e}")

if __name__ == "__main__":
    test_crwv_channel_stuffing()
