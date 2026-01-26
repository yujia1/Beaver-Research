# FMP API Bandwidth Analysis & Optimization Plan

## Current Status
- **Bandwidth Consumption**: 19.87 GB / 20 GB (99.35% used)
- **Critical Issue**: Approaching bandwidth limit with only 130 MB remaining

## Key Findings

### 1. High-Volume Endpoints (No Caching)

#### **Critical: `/framework/all/{ticker}` endpoint**
Location: `backend/routers/framework/routes.py:590`

This endpoint makes **20+ parallel FMP API calls** per request with **NO CACHING**:
- Income Statement
- Cash Flow Statement
- Balance Sheet
- Revenue Segmentation
- DCF Valuation
- Earnings Calendar
- Employee Count
- Key Metrics TTM
- Financial Ratios (for ticker + 6 peers = 7 API calls)
- Earnings Data
- Dividends
- Stock Splits
- Insider Trading
- Senate Trades
- House Trades
- Historical Price (full)
- Company Profile
- Key Executives
- Stock News

**Impact**: Each call to this endpoint can consume ~20-25 FMP API requests. If called frequently during development/testing, this alone could account for the bandwidth spike.

### 2. Endpoints with Caching (Good)

The following endpoints already implement Redis caching:

| Endpoint | Cache TTL | Cache Key Pattern |
|----------|-----------|-------------------|
| Economic Indicators | 4 hours (14400s) | `macro:{timeframe}` |
| Market Indices | 15 minutes (900s) | `indices:regional:{timeframe}`, `indices:major:{timeframe}` |
| Commodity Data | 30 minutes (1800s) | `commodity:data:monthly` |
| Currency Data | 1 hour (3600s) | `currency:data:monthly:v2` |
| Bond Data | 1 hour (3600s) | Various bond-specific keys |
| Crypto Data | Not specified | `crypto:data:{timeframe}` |
| Market News | 5 minutes (300s) | `market:news:cache` |

### 3. Endpoints Without Caching (Needs Attention)

**Framework Routes** (`backend/routers/framework/routes.py`):
- `/income-statement/{ticker}` - No caching
- `/cash-flow/{ticker}` - No caching
- `/balance-sheet/{ticker}` - No caching
- `/dcf/{ticker}` - No caching
- `/earnings-calendar/{ticker}` - No caching
- `/employee-count/{ticker}` - No caching
- `/profile/{ticker}` - No caching
- `/executives/{ticker}` - No caching
- `/mergers-acquisitions` - No caching
- `/key-metrics-ttm/{ticker}` - No caching
- `/historical-price/{ticker}` - No caching
- `/earnings/{ticker}` - No caching
- `/dividends/{ticker}` - No caching
- `/splits/{ticker}` - No caching
- `/revenue-segmentation/{ticker}` - No caching
- `/insider-trading/{ticker}` - No caching
- `/senate-trades/{ticker}` - No caching
- `/house-trades/{ticker}` - No caching
- `/news/{ticker}` - No caching
- **`/all/{ticker}`** - ⚠️ **CRITICAL - Makes 20+ API calls**

**Quant Routes** (`backend/routers/quant/fibonacci.py`):
- Fibonacci retracement endpoint - No caching

**Portfolio Routes** (`backend/routers/portfolio/routes.py`):
- Various portfolio-related FMP calls - Partial caching

## Recommendations

### Immediate Actions (Priority 1 - Implement Today)

#### 1. Add Caching to `/all/{ticker}` Endpoint
**Impact**: Reduce 20+ API calls to 1 cache hit per ticker
**Recommended TTL**: 1 hour (3600s) for most data, 15 minutes (900s) for real-time data

```python
# Cache the entire response
cache_key = f"framework:all:{ticker}:{period}:{limit}"
cached_data = redis_client.get_cache(cache_key)
if cached_data:
    return cached_data

# ... fetch data ...

redis_client.set_cache(cache_key, result, ttl=3600)
```

#### 2. Add Caching to Individual Framework Endpoints
**Impact**: Reduce redundant calls when endpoints are called individually
**Recommended TTL**: 
- Financial statements (income, cash flow, balance sheet): 24 hours (86400s) - rarely changes
- Company profile, executives: 7 days (604800s) - very static
- News, insider trading: 15 minutes (900s) - more dynamic
- Historical price: 1 hour (3600s)
- Dividends, splits, earnings: 24 hours (86400s)

#### 3. Increase Cache TTL for Static Data
Current economic indicators cache for 4 hours. Consider:
- GDP, CPI, unemployment: Increase to 24 hours (updates monthly/quarterly)
- Federal Funds Rate: Keep at 4 hours (can change during FOMC meetings)

### Short-term Actions (Priority 2 - This Week)

#### 4. Implement Request Deduplication
If multiple users request the same ticker simultaneously, deduplicate requests:

```python
# Use Redis to track in-flight requests
in_flight_key = f"inflight:{cache_key}"
if redis_client.get_cache(in_flight_key):
    # Wait and retry cache
    await asyncio.sleep(0.5)
    return redis_client.get_cache(cache_key)

redis_client.set_cache(in_flight_key, True, ttl=30)
# ... fetch data ...
redis_client.delete_cache(in_flight_key)
```

#### 5. Add Response Compression
Reduce bandwidth by compressing FMP responses before caching:

```python
import gzip
import json

def compress_data(data):
    return gzip.compress(json.dumps(data).encode())

def decompress_data(compressed):
    return json.loads(gzip.decompress(compressed).decode())
```

#### 6. Implement Batch Endpoint Optimization
The `fetch_financial_ratios_batch` function is good, but ensure it's used everywhere instead of sequential calls.

### Medium-term Actions (Priority 3 - Next 2 Weeks)

#### 7. Add Cache Warming Strategy
Pre-populate cache for popular tickers during off-peak hours:

```python
# Scheduled task to warm cache for top 100 tickers
POPULAR_TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", ...]

async def warm_cache():
    for ticker in POPULAR_TICKERS:
        await get_all_statements(ticker)
```

#### 8. Implement Tiered Caching
- **Tier 1** (Redis): Hot data, short TTL (minutes to hours)
- **Tier 2** (Database): Warm data, medium TTL (days)
- **Tier 3** (FMP API): Cold data, fetch on demand

#### 9. Add Monitoring and Alerts
Track FMP API usage:

```python
# Increment counter for each FMP call
redis_client.incr("fmp:api:calls:daily")
redis_client.expire("fmp:api:calls:daily", 86400)

# Alert when approaching limit
if redis_client.get("fmp:api:calls:daily") > THRESHOLD:
    send_alert()
```

### Long-term Actions (Priority 4 - Next Month)

#### 10. Migrate to Database Storage
Store historical financial data in PostgreSQL:
- Financial statements (income, cash flow, balance sheet)
- Historical prices
- Company profiles
- Only fetch new data, not historical

#### 11. Implement Smart Refresh
Only refresh data when needed:
- Check last update timestamp
- Skip refresh if data is recent enough
- Use FMP's rate limit headers to optimize

#### 12. Consider FMP Plan Upgrade
If bandwidth remains an issue after optimizations:
- Evaluate higher-tier FMP plans
- Calculate ROI based on user growth

## Estimated Impact

### Current State (Estimated)
- Average API calls per `/all/{ticker}`: 20-25 calls
- If called 100 times/day: 2,000-2,500 API calls/day
- At ~10KB per response: 20-25 MB/day just from this endpoint

### After Optimization
- With 1-hour cache: 95% reduction in API calls
- Expected savings: 19-24 MB/day from this endpoint alone
- Total bandwidth reduction: 50-70% across all endpoints

## Implementation Priority

1. **TODAY**: Add caching to `/all/{ticker}` endpoint
2. **THIS WEEK**: Add caching to all framework endpoints
3. **THIS WEEK**: Increase TTL for static data
4. **NEXT WEEK**: Implement request deduplication
5. **NEXT WEEK**: Add monitoring and alerts
6. **NEXT 2 WEEKS**: Cache warming for popular tickers
7. **NEXT MONTH**: Database storage for historical data

## Monitoring Checklist

- [ ] Set up FMP API call counter in Redis
- [ ] Create dashboard to track daily bandwidth usage
- [ ] Set up alerts at 80%, 90%, 95% bandwidth thresholds
- [ ] Log cache hit/miss ratios
- [ ] Track most frequently requested tickers
- [ ] Monitor cache memory usage

## Files to Modify

1. `backend/routers/framework/routes.py` - Add caching to all endpoints
2. `backend/routers/quant/fibonacci.py` - Add caching
3. `backend/routers/portfolio/routes.py` - Review and enhance caching
4. `backend/services/market/economic.py` - Increase TTL for static indicators
5. `backend/redis_client.py` - Add compression utilities (optional)
6. `backend/services/scheduler.py` - Add cache warming tasks

## Next Steps

1. Review this analysis
2. Prioritize which endpoints to cache first based on usage logs
3. Implement caching for `/all/{ticker}` immediately
4. Test cache effectiveness
5. Monitor bandwidth reduction
6. Iterate on remaining endpoints
