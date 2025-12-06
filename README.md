# Financial Dashboard Data Sources

This dashboard aggregates data from various real-time and historical sources.

## Test User Credentials

For testing purposes, the following users have been created:

### Regular User
- **Username**: `testuser@gmail.com`
- **Password**: `testpass123`
- **Role**: `user`
- **Permissions**: Can view Market and Investment pages, but cannot add events

### Creator User
- **Username**: `creator@gmail.com`
- **Password**: `creator123`
- **Role**: `creator`
- **Permissions**: Can view Market and Investment pages, and can add/manage their own events on the timeline
### Admin User
- **Username**: `admin@gmail.com`
- **Password**: `admin123`
- **Role**: `admin`

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

## Getting Started

### Backend Server

To start the backend server:

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`
API documentation (Swagger UI) is available at `http://localhost:8000/docs`

### Frontend Server

To start the frontend development server:

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173` (or another port if 5173 is in use)
