# Financial Agent Setup Guide

## Quick Start

### 1. Backend Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Configure environment variables
# Copy .env.example to .env and add your API keys
cp ../.env.example ../.env
# Edit ../.env and add your OPENAI_API_KEY

# Start the backend server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Setup

```bash
# Install dependencies
cd frontend
npm install

# Start the development server
npm run dev
```

The frontend will be available at `http://localhost:5173` (or another port if 5173 is in use).

## Environment Variables

Create a `.env` file in the project root with the following variables:

- `OPENAI_API_KEY` (required for AI features): Get your key from https://platform.openai.com/api-keys
- `FRED_API_KEY` (optional): Get your key from https://fred.stlouisfed.org/docs/api/api_key.html
- `DATABASE_URL` (optional): Defaults to SQLite if not set

## Features

- **Dashboard**: Market movers (gainers, losers, volatile, active stocks)
- **Macro Economics**: Economic indicators with historical data
- **Micro Economics**: Company deep dive analysis with financial statements, ratios, and AI-powered insights
- **Energy Dashboard**: Energy generation, consumption, grid status, and prices
- **AI Reports**: Upload PDF/HTML documents for AI analysis

## API Endpoints

- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs` (Swagger UI)

## Notes

- The backend will start even without `OPENAI_API_KEY`, but AI features will be disabled
- Without `FRED_API_KEY`, macro data will use fallback/mock data
- The frontend automatically connects to the backend on port 8000


