# Financial Dashboard Data Sources

This dashboard aggregates data from various real-time and historical sources.

## 1. Macro Economics
-   **Source**: Yahoo Finance (`yfinance`)
-   **Indicators**:
    -   10Y Treasury Yield (`^TNX`)
    -   VIX (`^VIX`)
    -   S&P 500 (`^GSPC`)
-   **FRED API Key**: `d88880486954fc460aea0154b0ff827a` (now available for real data).

## 2. Micro Economics
-   **Source**: Yahoo Finance (`yfinance`)
-   **Data**: Real-time stock prices, volume, market cap, sector, and industry data for searched tickers.

## 3. Energy Dashboard
-   **Grid Status**: `gridstatus` Python Library
    -   **Source**: NYISO (New York Independent System Operator)
    -   **Data**: Real-time Fuel Mix, Real-time Load/Demand.
-   **Energy Prices**: Yahoo Finance (`yfinance`)
    -   **Crude Oil**: `CL=F`
    -   **Natural Gas**: `NG=F`
    -   **Data**: Historical prices (Days, Weekly, Monthly, Yearly, 5 Years).

## 4. AI Reports
-   **Source**: OpenAI API (`gpt-4o`)
-   **Data**: Generates reports based on uploaded documents (PDF/HTML) and context.
