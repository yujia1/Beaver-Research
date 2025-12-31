import httpx
import os
import datetime
from typing import List, Dict, Any, Optional

# FMP Base URL
FMP_BASE_URL = "https://financialmodelingprep.com/stable"
FMP_API_KEY = os.getenv("FMP_API_KEY")

# Economic Indicators Configuration
ECONOMIC_INDICATORS = [
    {"name": "GDP", "indicator": "Gross Domestic Product", "description": "GDP (Billions USD)", "category": "Macro", "chart_type": "line"},
    {"name": "realGDP", "indicator": "Real GDP", "description": "Real GDP (Billions USD)", "category": "Macro", "chart_type": "line"},
    {"name": "nominalPotentialGDP", "indicator": "Nominal Potential GDP", "description": "Nominal Potential GDP (Billions USD)", "category": "Macro", "chart_type": "line"},
    {"name": "realGDPPerCapita", "indicator": "Real GDP Per Capita", "description": "Real GDP Per Capita (USD)", "category": "Macro", "chart_type": "line"},
    {"name": "federalFunds", "indicator": "Federal Funds Rate", "description": "Federal Funds Rate (%)", "category": "Monetary", "chart_type": "line"},
    {"name": "CPI", "indicator": "Consumer Price Index", "description": "CPI (Index)", "category": "Macro", "chart_type": "line"},
    {"name": "inflationRate", "indicator": "Inflation Rate", "description": "Inflation Rate (%)", "category": "Macro", "chart_type": "line"},
    {"name": "inflation", "indicator": "Inflation", "description": "Inflation (%)", "category": "Macro", "chart_type": "line"},
    {"name": "retailSales", "indicator": "Retail Sales", "description": "Retail Sales (Millions USD)", "category": "Business", "chart_type": "line"},
    {"name": "consumerSentiment", "indicator": "Consumer Sentiment", "description": "Consumer Sentiment Index", "category": "Macro", "chart_type": "line"},
    {"name": "durableGoods", "indicator": "Durable Goods", "description": "Durable Goods Orders (Millions USD)", "category": "Business", "chart_type": "line"},
    {"name": "unemploymentRate", "indicator": "Unemployment Rate", "description": "Unemployment Rate (%)", "category": "Labor", "chart_type": "line"},
    {"name": "totalNonfarmPayroll", "indicator": "Non-Farm Payrolls", "description": "Total Nonfarm Payroll (Thousands)", "category": "Labor", "chart_type": "line"},
    {"name": "initialClaims", "indicator": "Initial Jobless Claims", "description": "Initial Claims (Thousands)", "category": "Labor", "chart_type": "line"},
    {"name": "industrialProductionTotalIndex", "indicator": "Industrial Production", "description": "Industrial Production Index", "category": "Business", "chart_type": "line"},
    {"name": "newPrivatelyOwnedHousingUnitsStartedTotalUnits", "indicator": "Housing Starts", "description": "New Housing Units Started (Thousands)", "category": "Housing", "chart_type": "line"},
    {"name": "totalVehicleSales", "indicator": "Vehicle Sales", "description": "Total Vehicle Sales (Millions)", "category": "Business", "chart_type": "line"},
    {"name": "retailMoneyFunds", "indicator": "Retail Money Funds", "description": "Retail Money Funds (Billions USD)", "category": "Financial", "chart_type": "line"},
    {"name": "smoothedUSRecessionProbabilities", "indicator": "Recession Probability", "description": "US Recession Probability (%)", "category": "Macro", "chart_type": "line"},
    {"name": "3MonthOr90DayRatesAndYieldsCertificatesOfDeposit", "indicator": "3-Month CD Rate", "description": "3-Month CD Rate (%)", "category": "Rates", "chart_type": "line"},
    {"name": "commercialBankInterestRateOnCreditCardPlansAllAccounts", "indicator": "Credit Card Interest Rate", "description": "Credit Card Interest Rate (%)", "category": "Credit", "chart_type": "line"},
    {"name": "30YearFixedRateMortgageAverage", "indicator": "30-Year Mortgage Rate", "description": "30-Year Fixed Mortgage Rate (%)", "category": "Housing", "chart_type": "line"},
    {"name": "15YearFixedRateMortgageAverage", "indicator": "15-Year Mortgage Rate", "description": "15-Year Fixed Mortgage Rate (%)", "category": "Housing", "chart_type": "line"},
    {"name": "tradeBalanceGoodsAndServices", "indicator": "Trade Balance", "description": "Trade Balance (Millions USD)", "category": "Macro", "chart_type": "line"}
]

async def fetch_economic_indicator(name: str, from_date: str, to_date: str) -> List[Dict[str, Any]]:
    """
    Fetch a single economic indicator from FMP API.
    
    Args:
        name: The indicator name (e.g., 'GDP', 'CPI', 'unemploymentRate')
        from_date: Start date in YYYY-MM-DD format
        to_date: End date in YYYY-MM-DD format
    
    Returns:
        List of historical data points with date and value
    """
    if not FMP_API_KEY:
        print(f"Warning: FMP_API_KEY not set. Cannot fetch {name}")
        return []
    
    url = f"{FMP_BASE_URL}/economic-indicators"
    params = {
        "name": name,
        "from": from_date,
        "to": to_date,
        "apikey": FMP_API_KEY
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if not data or not isinstance(data, list):
                return []
            
            # Transform to our standard format
            history = []
            for item in data:
                if "date" in item and "value" in item:
                    history.append({
                        "date": item["date"],
                        "value": float(item["value"]) if item["value"] is not None else 0.0
                    })
            
            # Sort by date ascending
            history.sort(key=lambda x: x["date"])
            return history
            
    except httpx.HTTPError as e:
        print(f"HTTP error fetching {name}: {e}")
        return []
    except Exception as e:
        print(f"Error fetching {name}: {e}")
        return []

async def fetch_all_economic_data(timeframe: str = "monthly") -> List[Dict[str, Any]]:
    """
    Fetch all economic indicators from FMP API.
    
    Args:
        timeframe: Time period (monthly, quarterly, yearly, 5y, max)
    
    Returns:
        List of economic indicator data with history
    """
    # Calculate date range based on timeframe
    today = datetime.datetime.now()
    days_map = {
        "monthly": 365,      # 1 year
        "quarterly": 365*3,  # 3 years
        "yearly": 365*5,     # 5 years
        "5y": 365*5,         # 5 years
        "max": 365*30        # 30 years
    }
    days = days_map.get(timeframe, 365)
    from_date = (today - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    to_date = today.strftime("%Y-%m-%d")
    
    results = []
    
    # Fetch each indicator
    for config in ECONOMIC_INDICATORS:
        try:
            history = await fetch_economic_indicator(config["name"], from_date, to_date)
            
            # Get latest value and date
            latest_value = history[-1]["value"] if history else 0.0
            latest_date = history[-1]["date"] if history else to_date
            
            results.append({
                "indicator": config["indicator"],
                "value": latest_value,
                "date": latest_date,
                "description": config["description"],
                "category": config["category"],
                "series_id": config["name"],  # Use FMP name as series_id
                "history": history,
                "chart_type": config["chart_type"]
            })
        except Exception as e:
            print(f"Error processing {config['indicator']}: {e}")
            # Add empty result on error
            results.append({
                "indicator": config["indicator"],
                "value": 0.0,
                "date": to_date,
                "description": config["description"],
                "category": config["category"],
                "series_id": config["name"],
                "history": [],
                "chart_type": config["chart_type"]
            })
    
    return results

async def fetch_economic_series(series_id: str, timeframe: str = "monthly") -> Dict[str, Any]:
    """
    Fetch a single economic series by its ID (FMP name).
    
    Args:
        series_id: The FMP indicator name
        timeframe: Time period
    
    Returns:
        Economic indicator data with history
    """
    # Find the config for this series
    config = next((item for item in ECONOMIC_INDICATORS if item["name"] == series_id), None)
    if not config:
        raise ValueError(f"Unknown series_id: {series_id}")
    
    # Calculate date range
    today = datetime.datetime.now()
    days_map = {
        "monthly": 365,
        "quarterly": 365*3,
        "yearly": 365*5,
        "5y": 365*5,
        "max": 365*30
    }
    days = days_map.get(timeframe, 365)
    from_date = (today - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    to_date = today.strftime("%Y-%m-%d")
    
    # Fetch the data
    history = await fetch_economic_indicator(series_id, from_date, to_date)
    
    # Get latest value and date
    latest_value = history[-1]["value"] if history else 0.0
    latest_date = history[-1]["date"] if history else to_date
    
    return {
        "indicator": config["indicator"],
        "value": latest_value,
        "date": latest_date,
        "description": config["description"],
        "category": config["category"],
        "series_id": series_id,
        "history": history,
        "chart_type": config["chart_type"]
    }
