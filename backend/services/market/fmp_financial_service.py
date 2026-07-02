"""
FMP API Service for Financial Data Collection

Fetches financial statements from Financial Modeling Prep API with Redis caching
to minimize API calls and improve performance.
"""

import os
import requests
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

# Redis client
try:
    from redis_client import redis_client
    REDIS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Redis not available: {e}")
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

# FMP API Configuration
FMP_API_KEY = os.getenv("FMP_API_KEY")
FMP_BASE_URL = "https://financialmodelingprep.com/stable"

# Cache TTL (Time To Live)
CACHE_TTL_FINANCIAL_STATEMENTS = 86400  # 24 hours
CACHE_TTL_MARKET_DATA = 300  # 5 minutes


class FMPAPIError(Exception):
    """Custom exception for FMP API errors"""
    pass


def _get_cache_key(key_type: str, ticker: str = None, **kwargs) -> str:
    """Generate Redis cache key"""
    if ticker:
        parts = [f"fmp:{key_type}:{ticker}"]
    else:
        parts = [f"fmp:{key_type}"]
    
    for k, v in kwargs.items():
        parts.append(f"{k}:{v}")
    
    return ":".join(parts)


def _get_from_cache(cache_key: str) -> Optional[Dict]:
    """Get data from Redis cache"""
    if not REDIS_AVAILABLE:
        return None
    
    return redis_client.get_cache(cache_key)


def _set_to_cache(cache_key: str, data: Any, ttl: int):
    """Set data to Redis cache"""
    if not REDIS_AVAILABLE:
        return
    
    redis_client.set_cache(cache_key, data, ttl)


def _sanitize_error(message: str) -> str:
    """Remove sensitive data (API keys, full URLs) from error messages."""
    import re
    # Strip apikey parameter from URLs
    message = re.sub(r'[&?]apikey=[^&\s]+', '', message)
    # Strip any remaining raw API key patterns (32+ char alphanumeric strings)
    if FMP_API_KEY:
        message = message.replace(FMP_API_KEY, '***')
    return message


def _make_fmp_request(endpoint: str, params: Dict = None) -> Dict:
    """Make request to FMP API with error handling"""
    if not FMP_API_KEY:
        raise FMPAPIError("FMP_API_KEY not found in environment variables")
    
    url = f"{FMP_BASE_URL}/{endpoint}"
    params = params or {}
    params["apikey"] = FMP_API_KEY
    
    try:
        logger.info(f"FMP API request: {endpoint}")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Check for API error messages
        if isinstance(data, dict) and "Error Message" in data:
            raise FMPAPIError(f"FMP API Error: {data['Error Message']}")
        
        return data
    
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response is not None else "unknown"
        # Return user-friendly message without exposing URL or API key
        friendly_msg = f"FMP API returned HTTP {status_code} for endpoint '{endpoint}'"
        logger.error(f"FMP API request failed: {_sanitize_error(str(e))}")
        raise FMPAPIError(friendly_msg)
    except requests.exceptions.RequestException as e:
        logger.error(f"FMP API request failed: {_sanitize_error(str(e))}")
        raise FMPAPIError(f"FMP API request failed for endpoint '{endpoint}': connection error")


# ============================================================================
# Financial Statement Fetching
# ============================================================================

def fetch_income_statement(ticker: str, years: int = 10) -> List[Dict]:
    """
    Fetch annual income statements for a ticker
    
    Args:
        ticker: Stock ticker symbol
        years: Number of years of data (default: 10)
    
    Returns:
        List of income statement dictionaries (most recent first)
    """
    cache_key = _get_cache_key("income", ticker, period="annual", years=years)
    
    # Check cache
    cached_data = _get_from_cache(cache_key)
    if cached_data:
        return cached_data
    
    # Fetch from API
    endpoint = "income-statement"
    params = {"symbol": ticker, "period": "annual", "limit": years}
    
    data = _make_fmp_request(endpoint, params)
    
    # Cache the result
    _set_to_cache(cache_key, data, CACHE_TTL_FINANCIAL_STATEMENTS)
    
    return data


def fetch_cash_flow_statement(ticker: str, years: int = 10) -> List[Dict]:
    """
    Fetch annual cash flow statements for a ticker
    
    Args:
        ticker: Stock ticker symbol
        years: Number of years of data (default: 5)
    
    Returns:
        List of cash flow statement dictionaries (most recent first)
    """
    cache_key = _get_cache_key("cashflow", ticker, period="annual", years=years)
    
    # Check cache
    cached_data = _get_from_cache(cache_key)
    if cached_data:
        return cached_data
    
    # Fetch from API
    endpoint = "cash-flow-statement"
    params = {"symbol": ticker, "period": "annual", "limit": years}
    
    data = _make_fmp_request(endpoint, params)
    
    # Cache the result
    _set_to_cache(cache_key, data, CACHE_TTL_FINANCIAL_STATEMENTS)
    
    return data


def fetch_balance_sheet(ticker: str, years: int = 10) -> List[Dict]:
    """
    Fetch annual balance sheets for a ticker
    
    Args:
        ticker: Stock ticker symbol
        years: Number of years of data (default: 5)
    
    Returns:
        List of balance sheet dictionaries (most recent first)
    """
    cache_key = _get_cache_key("balance", ticker, period="annual", years=years)
    
    # Check cache
    cached_data = _get_from_cache(cache_key)
    if cached_data:
        return cached_data
    
    # Fetch from API
    endpoint = "balance-sheet-statement"
    params = {"symbol": ticker, "period": "annual", "limit": years}
    
    data = _make_fmp_request(endpoint, params)
    
    # Cache the result
    _set_to_cache(cache_key, data, CACHE_TTL_FINANCIAL_STATEMENTS)
    
    return data


def fetch_all_financial_statements(ticker: str, years: int = 5) -> Dict[str, List[Dict]]:
    """
    Fetch all financial statements (income, cash flow, balance sheet) for a ticker
    
    This is the recommended function to use as it fetches all statements at once,
    which is more efficient than calling each function separately.
    
    Args:
        ticker: Stock ticker symbol
        years: Number of years of data (default: 5)
    
    Returns:
        Dictionary with keys: 'income', 'cashflow', 'balance'
    """
    return {
        "income": fetch_income_statement(ticker, years),
        "cashflow": fetch_cash_flow_statement(ticker, years),
        "balance": fetch_balance_sheet(ticker, years)
    }


def fetch_key_metrics(ticker: str, limit: int = 5, period: str = "FY") -> List[Dict]:
    """
    Fetch key metrics from FMP for a ticker

    Args:
        ticker: Stock ticker symbol
        limit: Number of records to return (default: 5)
        period: Period string expected by FMP (e.g., 'FY')

    Returns:
        List of key metrics dictionaries (most recent first)
    """
    cache_key = _get_cache_key("key_metrics", ticker, limit=limit, period=period)

    cached_data = _get_from_cache(cache_key)
    if cached_data:
        return cached_data

    endpoint = "key-metrics"
    params = {"symbol": ticker, "limit": limit, "period": period}

    data = _make_fmp_request(endpoint, params)

    # Cache the result
    _set_to_cache(cache_key, data, CACHE_TTL_FINANCIAL_STATEMENTS)

    return data


# ============================================================================
# Market Data (for EV calculation)
# ============================================================================

def fetch_stock_quote(ticker: str) -> Dict:
    """
    Fetch current stock quote (price, market cap, etc.)
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        Quote dictionary with price, market cap, etc.
    """
    cache_key = _get_cache_key("quote", ticker)
    
    # Check cache (short TTL for market data)
    cached_data = _get_from_cache(cache_key)
    if cached_data:
        return cached_data
    
    # Fetch from API
    endpoint = "quote"
    params = {"symbol": ticker}
    data = _make_fmp_request(endpoint, params)
    
    if data and len(data) > 0:
        quote = data[0]
        _set_to_cache(cache_key, quote, CACHE_TTL_MARKET_DATA)
        return quote
    
    return {}


# ============================================================================
# Batch Fetching with Rate Limiting
# ============================================================================

import time

def batch_fetch_financials(tickers: List[str], years: int = 5, delay_seconds: int = 60) -> Dict[str, Dict]:
    """
    Batch fetch financial statements for multiple tickers with rate limiting
    
    Args:
        tickers: List of ticker symbols
        years: Number of years of data
        delay_seconds: Delay between batches (default: 60 seconds / 1 minute)
    
    Returns:
        Dictionary mapping ticker to financial statements
    """
    results = {}
    batch_size = 5  # Process 3-5 stocks per batch (using 5 for efficiency)
    
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}: {batch}")
        
        for ticker in batch:
            try:
                results[ticker] = fetch_all_financial_statements(ticker, years)
            except Exception as e:
                logger.error(f"Error fetching {ticker}: {e}")
                results[ticker] = {"error": str(e)}
        
        # Delay between batches (except for last batch)
        if i + batch_size < len(tickers):
            logger.info(f"Waiting {delay_seconds} seconds before next batch...")
            time.sleep(delay_seconds)
    
    return results
