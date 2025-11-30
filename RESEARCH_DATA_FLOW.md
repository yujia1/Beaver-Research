# Research Agent Data Flow Documentation

## Overview
This document explains how data flows from the backend through AI agents to the frontend in the Research Intelligence Layer.

---

## 1. Frontend Request Flow

### Entry Point: `ResearchEditView.vue`

**Location**: `frontend/src/components/ResearchEditView.vue`

**Function**: `fetchDataBubbles()` (lines 475-567)

### Request Flow:

```
User Action (Mode Switch / Agent Change / Ticker Search)
    ↓
fetchDataBubbles() called
    ↓
Check Frontend Cache (dailyCache.js)
    ↓
If cached → Return cached data
If not cached → Make API request
```

### API Endpoints Called:

**Company Mode:**
```
GET /api/research/company-data/{ticker}?agent={activeAgent}
Example: GET /api/research/company-data/TSLA?agent=FUNDAMENTAL_AGENT
```

**Market Mode:**
```
GET /api/research/market-data?agent={activeAgent}
Example: GET /api/research/market-data?agent=EQUITY_AGENT
```

### Frontend Cache Strategy:
- **Cache Key Format**: 
  - Company: `research_company_{ticker}_{agent}`
  - Market: `research_market_{agent}`
- **Cache Duration**: 24 hours (daily cache)
- **Storage**: localStorage via `dailyCache.js`

---

## 2. Backend Processing Flow

### Entry Point: `backend/routers/research.py`

### Company Data Flow (`get_company_data`):

```
GET /api/research/company-data/{ticker}?agent={agent}
    ↓
Check Backend Cache (6-hour TTL)
    ↓
If cached → Return cached bubbles
If not cached → Fetch raw data
    ↓
Based on agent type:
    ├─ FUNDAMENTAL_AGENT → Fetch financial statements
    ├─ TRADING_AGENT → Fetch institutional holdings & options
    ├─ EXECUTIVE_AGENT → Fetch insider trading data
    └─ MANAGEMENT_AGENT → Fetch 10K filings
    ↓
For each data type, call process_data_with_agent()
    ↓
AI Agent processes raw data → Returns structured bubble
    ↓
Collect all bubbles → Cache result → Return to frontend
```

### Market Data Flow (`get_market_data`):

```
GET /api/research/market-data?agent={agent}
    ↓
Check Backend Cache (6-hour TTL)
    ↓
If cached → Return cached bubbles
If not cached → Fetch raw market data
    ↓
Based on agent type:
    ├─ EQUITY_AGENT → Fetch S&P 500 data (yfinance)
    ├─ BOND_AGENT → Fetch Treasury yields (FRED API)
    └─ ECONOMICS_AGENT → Fetch CPI data (FRED API)
    ↓
For each data type, call process_market_data_with_agent()
    ↓
AI Agent processes raw data → Returns structured bubble
    ↓
Collect all bubbles → Cache result → Return to frontend
```

---

## 3. AI Agent Processing

### Function: `process_data_with_agent()`

**Location**: `backend/routers/research.py` (lines 300-417)

### Processing Steps:

#### Step 1: Get Agent Configuration
```python
agent_config = COMPANY_AGENTS.get(agent_id)
sub_agent_name = sub_agents.get(sub_agent_key, "Data Examiner")
```

#### Step 2: Build AI Prompt
The prompt is customized based on the statement type:

**For Income Statement:**
```python
metrics_instruction = """
Extract exactly these 4 key metrics:
- "TOTAL REVENUE": Look for "Total Revenue" or "Revenue"
- "COST OF REVENUE": Look for "Cost Of Revenue"
- "GROSS PROFIT": Look for "Gross Profit"
- "OPERATING EXPE...": Look for "Operating Expense"
Title: "YAHOO FINANCE: INCOME STATEMENT"
Category: "FINANCIAL"
"""
```

**For Balance Sheet:**
```python
metrics_instruction = """
Extract exactly these 4 key metrics:
- "TOTAL ASSETS"
- "TOTAL LIABILITIES"
- "TOTAL EQUITY"
- "CASH & EQUIVAL..."
Title: "YAHOO FINANCE: BALANCE SHEET"
Category: "FINANCIAL"
"""
```

**For Cash Flow:**
```python
metrics_instruction = """
Extract exactly these 4 key metrics:
- "OPERATING CAS..."
- "CAPITAL EXPENDI..."
- "FREE CASH FLOW"
- "ISSUANCE OF DE..."
Title: "YAHOO FINANCE: CASH FLOW"
Category: "FINANCIAL"
"""
```

#### Step 3: Call OpenAI API
```python
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "system",
            "content": f"You are a {sub_agent_name} specializing in {agent_config['focus']}..."
        },
        {
            "role": "user",
            "content": prompt
        }
    ],
    temperature=0.7,
    max_tokens=1000,
    response_format={"type": "json_object"}
)
```

#### Step 4: Parse AI Response
```python
analyzed = json.loads(response.choices[0].message.content)
# Returns:
# {
#   "title": "YAHOO FINANCE: INCOME STATEMENT",
#   "category": "FINANCIAL",
#   "key_metrics": {
#     "TOTAL REVENUE": "307.39B",
#     "COST OF REVENUE": "137.95B",
#     "GROSS PROFIT": "169.44B",
#     "OPERATING EXPE...": "119.20B"
#   },
#   "insights": [...]
# }
```

#### Step 5: Create Data Bubble
```python
bubble = {
    "id": f"{sub_agent_key}-{ticker}-{timestamp}",
    "type": sub_agent_key,  # e.g., "income_statement"
    "category": "FINANCIAL",
    "icon": get_icon_for_type(sub_agent_key),  # e.g., "📊"
    "title": "YAHOO FINANCE: INCOME STATEMENT",
    "subtitle": ticker,  # e.g., "TSLA"
    "timestamp": datetime.now().isoformat(),
    "data": analyzed.get("key_metrics", {}),  # The 4 metrics
    "insights": analyzed.get("insights", [])
}
```

---

## 4. Data Structure

### Request Structure (Frontend → Backend):

**Company Mode:**
```json
GET /api/research/company-data/TSLA?agent=FUNDAMENTAL_AGENT
```

**Market Mode:**
```json
GET /api/research/market-data?agent=EQUITY_AGENT
```

### Response Structure (Backend → Frontend):

```json
{
  "bubbles": [
    {
      "id": "income_statement-TSLA-1234567890.123",
      "type": "income_statement",
      "category": "FINANCIAL",
      "icon": "📊",
      "title": "YAHOO FINANCE: INCOME STATEMENT",
      "subtitle": "TSLA",
      "timestamp": "2025-01-15T16:29:43.123456",
      "data": {
        "TOTAL REVENUE": "307.39B",
        "COST OF REVENUE": "137.95B",
        "GROSS PROFIT": "169.44B",
        "OPERATING EXPE...": "119.20B"
      },
      "insights": [
        "Revenue increased 15% YoY",
        "Operating margin improved to 35%"
      ]
    },
    {
      "id": "balance_sheet-TSLA-1234567890.456",
      "type": "balance_sheet",
      "category": "FINANCIAL",
      "icon": "⚖️",
      "title": "YAHOO FINANCE: BALANCE SHEET",
      "subtitle": "TSLA",
      "timestamp": "2025-01-15T16:29:43.456789",
      "data": {
        "TOTAL ASSETS": "422.31B",
        "TOTAL LIABILITIES": "101.40B",
        "TOTAL EQUITY": "320.91B",
        "CASH & EQUIVAL...": "125.10B"
      },
      "insights": []
    },
    {
      "id": "cash_flow-TSLA-1234567890.789",
      "type": "cash_flow",
      "category": "FINANCIAL",
      "icon": "📊",
      "title": "YAHOO FINANCE: CASH FLOW",
      "subtitle": "TSLA",
      "timestamp": "2025-01-15T16:29:43.789012",
      "data": {
        "OPERATING CAS...": "95.20B",
        "CAPITAL EXPENDI...": "-35.80B",
        "FREE CASH FLOW": "59.40B",
        "ISSUANCE OF DE...": "0.00B"
      },
      "insights": []
    }
  ]
}
```

---

## 5. Frontend Display Flow

### Data Reception:

```javascript
// In fetchDataBubbles()
const data = await response.json()
const bubbles = data.bubbles || []

// Convert timestamp strings to Date objects
bubbles.forEach(bubble => {
  if (bubble.timestamp && typeof bubble.timestamp === 'string') {
    bubble.timestamp = new Date(bubble.timestamp)
  }
})

// Store in reactive state
dataBubbles.value = bubbles

// Cache for future use
setDailyCache(cacheKey, bubbles)
```

### Filtering (for Company Mode):

```javascript
// filteredBubbles computed property
const filteredBubbles = computed(() => {
  if (props.viewMode === 'MARKET') {
    return dataBubbles.value  // Already filtered by backend
  }
  
  // Filter by agent focus
  const agent = availableAgents.value.find(a => a.id === props.activeAgent)
  return dataBubbles.value.filter(bubble => {
    return agent.focus.some(focus => 
      bubble.type.toLowerCase().includes(focus) || 
      bubble.category.toLowerCase().includes(focus)
    )
  })
})
```

### Rendering:

```vue
<div
  v-for="bubble in filteredBubbles"
  :key="bubble.id"
  class="data-bubble"
>
  <div class="bubble-header">
    <div class="bubble-icon">{{ bubble.icon }}</div>
    <div class="bubble-meta">
      <span class="bubble-category-badge">{{ bubble.category }}</span>
      <span class="bubble-time">{{ formatTime(bubble.timestamp) }}</span>
    </div>
  </div>
  <div class="bubble-title">{{ bubble.title }}</div>
  <div class="bubble-subtitle">{{ bubble.subtitle }}</div>
  <div class="bubble-data">
    <div
      v-for="(value, key) in bubble.data"
      :key="key"
      class="bubble-data-item"
    >
      <span class="data-label">{{ key }}</span>
      <span class="data-value">{{ formatValue(value) }}</span>
    </div>
  </div>
</div>
```

---

## 6. Caching Strategy

### Frontend Cache:
- **Location**: `frontend/src/utils/dailyCache.js`
- **Duration**: 24 hours
- **Key Format**: `research_company_{ticker}_{agent}` or `research_market_{agent}`
- **Storage**: localStorage

### Backend Cache:
- **Location**: In-memory dictionary `_cache` in `research.py`
- **Duration**: 6 hours (CACHE_TTL_HOURS)
- **Key Format**: MD5 hash of `{view_mode}_{ticker}_{agent}`
- **Structure**:
  ```python
  {
    'data': {...},
    'expires_at': datetime
  }
  ```

---

## 7. Data Sources

### Company Mode Data Sources:

| Agent | Sub-Agent | Data Source | Function |
|-------|-----------|-------------|----------|
| FUNDAMENTAL_AGENT | Income Statement | Yahoo Finance | `get_micro_data(ticker)['financials']['ltm']` |
| FUNDAMENTAL_AGENT | Balance Sheet | Yahoo Finance | `get_micro_data(ticker)['balance_sheet']['ltm']` |
| FUNDAMENTAL_AGENT | Cash Flow | Yahoo Finance | `get_micro_data(ticker)['cashflow']['ltm']` |
| TRADING_AGENT | Institutional Holdings | Yahoo Finance | `yf.Ticker(ticker).institutional_holders` |
| TRADING_AGENT | Options Data | Yahoo Finance | `yf.Ticker(ticker).option_chain()` |
| EXECUTIVE_AGENT | Insider Trading | Yahoo Finance | `yf.Ticker(ticker).insider_transactions` |
| MANAGEMENT_AGENT | 10K Filing | SEC EDGAR | `edgar_service.get_company_submissions(ticker)` |

### Market Mode Data Sources:

| Agent | Sub-Agent | Data Source | Function |
|-------|-----------|-------------|----------|
| EQUITY_AGENT | S&P 500 | Yahoo Finance | `yf.Ticker("^GSPC")` |
| BOND_AGENT | Treasury Yield | FRED API | `web.DataReader('DGS10', 'fred', ...)` |
| ECONOMICS_AGENT | CPI | FRED API | `web.DataReader('CPIAUCSL', 'fred', ...)` |

---

## 8. Error Handling

### Frontend:
- If API call fails → `dataBubbles.value = []`
- If cache miss → Make API request
- If timestamp parsing fails → Use original string

### Backend:
- If cache hit → Return immediately
- If data fetch fails → Log error, return `{"bubbles": []}`
- If AI processing fails → Log error, return `None` (bubble not added)
- If agent not found → Return empty bubbles array

---

## 9. Performance Optimizations

1. **Dual-Layer Caching**: Frontend (24h) + Backend (6h)
2. **Conditional Fetching**: Only fetch when mode/agent/ticker changes
3. **Batch Processing**: Process all sub-agents in one request
4. **Lazy Loading**: Data fetched on-demand, not pre-loaded

---

## 10. Future Improvements

Potential areas for enhancement:
1. **Streaming Responses**: Stream AI responses as they're generated
2. **Incremental Updates**: Update bubbles as they're processed
3. **Error Recovery**: Retry failed AI calls with exponential backoff
4. **Data Validation**: Validate AI response structure before creating bubbles
5. **Metrics Tracking**: Track AI processing time and success rates

