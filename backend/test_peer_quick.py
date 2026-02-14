"""
Quick test to verify peer comparison integration
"""
import os
from services.market.fmp_financial_service import fetch_all_financial_statements, fetch_stock_quote
from services.market.screener_calculator import calculate_all_metrics

# Set API key
os.environ["FMP_API_KEY"] = "l4DHwKBRg3uFTkojVxlRAV1KE90I9gOm"

ticker = "AAPL"
print(f"\nTesting {ticker} WITHOUT peer comparison...")

financial_data = fetch_all_financial_statements(ticker, years=5)
quote = fetch_stock_quote(ticker)
current_price = quote.get("price", 0)

# Test without ticker (no peer comparison)
metrics_no_peer = calculate_all_metrics(
    income_data=financial_data["income"],
    cash_flow_data=financial_data["cashflow"],
    balance_sheet_data=financial_data["balance"],
    current_price=current_price,
    ticker=None
)

print(f"\nDSO (no peer): {metrics_no_peer['days_sales_outstanding'].latest_value}")
print(f"DSO Red Flag: {metrics_no_peer['days_sales_outstanding'].is_red_flag}")
print(f"DSO Reason: {metrics_no_peer['days_sales_outstanding'].red_flag_reason}")

print(f"\n\nTesting {ticker} WITH peer comparison...")

# Test with ticker (enable peer comparison)
metrics_with_peer = calculate_all_metrics(
    income_data=financial_data["income"],
    cash_flow_data=financial_data["cashflow"],
    balance_sheet_data=financial_data["balance"],
    current_price=current_price,
    ticker=ticker
)

print(f"\nDSO (with peer): {metrics_with_peer['days_sales_outstanding'].latest_value}")
print(f"DSO Red Flag: {metrics_with_peer['days_sales_outstanding'].is_red_flag}")
print(f"DSO Reason: {metrics_with_peer['days_sales_outstanding'].red_flag_reason}")

print("\n✅ Test complete!")
