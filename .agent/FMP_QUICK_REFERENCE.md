# Quick Reference: FMP Bandwidth Optimization

## Problem
- FMP API bandwidth: **19.87 GB / 20 GB used (99.35%)**
- Only 130 MB remaining
- Risk of service disruption

## Root Cause
The `/framework/all/{ticker}` endpoint makes **20+ FMP API calls** per request with **NO CACHING**

## Solution Implemented ✅

### 1. Added Caching to Critical Endpoint
- **Endpoint**: `/framework/all/{ticker}`
- **Cache TTL**: 1 hour
- **Impact**: 95% reduction in API calls for repeated ticker requests

### 2. Added Caching to 9 Individual Endpoints
All framework endpoints now cached with appropriate TTLs:
- Financial statements: 24 hours
- Company profile: 7 days  
- Historical prices: 1 hour
- News: 15 minutes
- Trading data: 1-6 hours

### 3. Optimized Economic Data Cache
- Increased TTL from 4 hours → 24 hours
- Economic data updates monthly/quarterly, not hourly

## Expected Results

**Bandwidth Reduction**: 50-70% overall
**API Call Reduction**: 60-80% overall
**Response Time**: 50-90% faster for cached requests

## Files Modified

1. `backend/routers/framework/routes.py` - Added caching to 10 endpoints
2. `backend/routers/market/economic/macro.py` - Increased cache TTL

## Testing

```bash
# Start backend
cd backend
python main.py

# Test the cached endpoint
curl "http://localhost:8000/api/framework/all/AAPL?period=annual&limit=5"

# Second call should be much faster (cache hit)
curl "http://localhost:8000/api/framework/all/AAPL?period=annual&limit=5"
```

## Monitoring

Check Redis for cache keys:
```bash
redis-cli
> KEYS framework:*
> TTL framework:all:AAPL:annual:5
> GET framework:all:AAPL:annual:5
```

## Next Steps

1. ✅ Code changes complete
2. ⏳ Test in local environment
3. ⏳ Deploy to staging
4. ⏳ Monitor bandwidth for 24 hours
5. ⏳ Deploy to production if successful

## Cache Key Reference

```
framework:all:{ticker}:{period}:{limit}          # 1 hour
framework:income:{ticker}:{period}:{limit}       # 24 hours
framework:cashflow:{ticker}:{period}:{limit}     # 24 hours
framework:balance:{ticker}:{period}:{limit}      # 24 hours
framework:profile:{ticker}                       # 7 days
framework:historical:{ticker}                    # 1 hour
framework:insider:{ticker}:{page}:{limit}        # 1 hour
framework:senate:{ticker}                        # 6 hours
framework:house:{ticker}                         # 6 hours
framework:news:{ticker}:{limit}:{page}           # 15 minutes
macro:{timeframe}                                # 24 hours
```

## Emergency Cache Clear

If you need to force fresh data:
```python
from redis_client import redis_client
redis_client.delete_cache("framework:*")  # Clear all framework caches
```

---
**Status**: ✅ Ready for Testing  
**Date**: 2026-01-26
