# API Path Standardization - Market Routes

## Date: 2025-12-30

## Overview
Standardized all market-related API routes to use a consistent `/api/market/` prefix pattern for better organization and clarity.

## Changes Summary

### Backend (`backend/main.py`)

All market-related routes now follow the pattern: `/api/market/{category}/{subcategory}`

#### Before → After

| Category | Old Path | New Path |
|----------|----------|----------|
| **Equity - Stocks** | `/api/internal` | `/api/market/equity/stocks` |
| **Equity - Indices** | `/api/indices` | `/api/market/equity/indices` |
| **Market News** | `/api/stream-news` | `/api/market/news` |
| **SEC Data** | `/api/sec` | `/api/market/sec` |
| **Bond** | `/api/bond` | `/api/market/bond` |
| **Commodity - General** | `/api/internal/commodities` | `/api/market/commodity` |
| **Commodity - Energy** | `/api/energy` | `/api/market/commodity/energy` |
| **Currency** | `/api/internal/currencies` | `/api/market/currency` |
| **Economic** | `/api/internal` (macro) | `/api/market/economic` |
| **Crypto** | `/api/internal/crypto` | `/api/market/crypto` |
| **Policy** | `/api/internal` (policy) | `/api/market/policy` |
| **External** | `/api/external` | `/api/market/external` |

### Frontend Updates

Updated all frontend components to use the new API paths:

#### 1. **KeyLogsSection.vue**
- Economic: `/api/internal/macro` → `/api/market/economic/macro`
- Currency: `/api/internal/currencies` → `/api/market/currency/currencies`
- Commodity: `/api/internal/commodities` → `/api/market/commodity/commodities`
- Crypto: `/api/internal/crypto` → `/api/market/crypto`

#### 2. **BondView.vue**
- Bond data: `/api/bond/all` → `/api/market/bond/all`
- Bond series: `/api/bond/series/{id}` → `/api/market/bond/series/{id}`

#### 3. **BondMarketSection.vue**
- Bond data: `/api/bond/all` → `/api/market/bond/all`
- Bond series: `/api/bond/series/{id}` → `/api/market/bond/series/{id}`

#### 4. **IndicesSection.vue**
- Regional indices: `/api/indices/regional` → `/api/market/equity/indices/regional`
- Index series: `/api/indices/regional/series/{symbol}` → `/api/market/equity/indices/regional/series/{symbol}`

## New API Structure

```
/api/
├── auth/                          # Authentication
├── admin/                         # Admin functions
├── stream/                        # SSE streams
├── research/                      # Research features
├── reports/                       # Journal/Reports
├── portfolio/                     # Portfolio management
└── market/                        # ⭐ All market data
    ├── equity/
    │   ├── stocks/               # Stock data
    │   └── indices/              # Index data
    │       └── regional/         # Regional indices
    ├── bond/                     # Bond market data
    │   ├── all                   # All bonds
    │   └── series/{id}           # Specific bond series
    ├── commodity/                # Commodity data
    │   ├── commodities           # All commodities (categorized)
    │   ├── commodities/{symbol}  # Specific commodity
    │   └── energy/               # Energy-specific endpoints
    ├── currency/                 # Currency/Forex data
    │   ├── currencies            # All currencies
    │   └── currencies/{id}       # Specific currency
    ├── economic/                 # Economic indicators
    │   └── macro                 # Macro economic data
    ├── crypto/                   # Cryptocurrency data
    │   ├── all                   # All crypto
    │   └── {id}/history          # Crypto history
    ├── policy/                   # Policy data (Fed, etc.)
    ├── news/                     # Market news streams
    ├── sec/                      # SEC filings
    └── external/                 # External market data
```

## Backwards Compatibility

### Deprecated Endpoint (Maintained)
- `/api/internal/indices` → Shim redirects to new indices endpoint
- This ensures old clients don't break immediately

## Benefits

### 1. **Consistency**
- All market data under `/api/market/`
- Clear categorization by asset type
- Predictable URL patterns

### 2. **Scalability**
- Easy to add new market categories
- Clear namespace separation
- Better API documentation structure

### 3. **Clarity**
- `/api/market/bond/all` is clearer than `/api/bond/all`
- Category is explicit in the path
- Easier for developers to understand

### 4. **Organization**
- Related endpoints grouped together
- Hierarchical structure matches domain model
- Better for API versioning in the future

## Testing Checklist

### Backend
- [ ] All routes registered correctly
- [ ] Swagger docs updated at `/docs`
- [ ] Old shim endpoint still works
- [ ] No 404 errors on new paths

### Frontend
- [ ] Economic tab loads data
- [ ] Currency tab loads data
- [ ] Commodity tab loads data
- [ ] Crypto tab loads data
- [ ] Bond tab loads data
- [ ] Indices load correctly
- [ ] No console errors
- [ ] All charts display properly

## Migration Guide

### For External API Consumers

If you're consuming our API externally, update your endpoints:

**Economic Data**:
```javascript
// Old
fetch('/api/internal/macro?timeframe=monthly')

// New
fetch('/api/market/economic/macro?timeframe=monthly')
```

**Currency Data**:
```javascript
// Old
fetch('/api/internal/currencies')

// New
fetch('/api/market/currency/currencies')
```

**Commodity Data**:
```javascript
// Old
fetch('/api/internal/commodities')

// New
fetch('/api/market/commodity/commodities')
```

**Crypto Data**:
```javascript
// Old
fetch('/api/internal/crypto/all')

// New
fetch('/api/market/crypto/all')
```

**Bond Data**:
```javascript
// Old
fetch('/api/bond/all')

// New
fetch('/api/market/bond/all')
```

**Indices Data**:
```javascript
// Old
fetch('/api/indices/regional')

// New
fetch('/api/market/equity/indices/regional')
```

## Files Modified

### Backend (1 file)
- `backend/main.py` - Updated all market route registrations

### Frontend (4 files)
- `frontend/src/components/dashboard/KeyLogsSection.vue` - Economic, Currency, Commodity, Crypto
- `frontend/src/views/BondView.vue` - Bond data
- `frontend/src/components/dashboard/BondMarketSection.vue` - Bond data
- `frontend/src/components/dashboard/IndicesSection.vue` - Indices data

## Deployment Notes

1. **Deploy backend first** - New routes must be available
2. **Deploy frontend** - Update to use new paths
3. **Monitor logs** - Check for any 404 errors
4. **Test all tabs** - Verify data loads correctly

## Future Enhancements

1. **API Versioning**: Add `/api/v1/market/` for version control
2. **Rate Limiting**: Apply per-category rate limits
3. **Analytics**: Track usage by market category
4. **Documentation**: Auto-generate API docs from route structure
