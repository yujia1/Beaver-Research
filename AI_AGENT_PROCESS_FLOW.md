# AI Agent Process Flow - Research Intelligence Layer

## Overview
This document explains the complete AI agent processing flow in `backend/routers/research.py`, from API request to returning analyzed data bubbles.

---

## High-Level Flow Diagram

```
Frontend Request
    ↓
API Endpoint (get_company_data / get_market_data)
    ↓
Cache Check (6-hour TTL)
    ↓
[If Cache Hit] → Return Cached Bubbles
[If Cache Miss] → Continue
    ↓
Data Collection Phase
    ↓
AI Processing Phase (process_data_with_agent)
    ↓
Bubble Creation
    ↓
Cache Result
    ↓
Return to Frontend
```

---

## Detailed Process Flow

### 1. **API Request Entry Point**

#### Company Mode: `GET /api/research/company-data/{ticker}?agent={agent}`
- **Location**: `@router.get("/company-data/{ticker}")` (line 531)
- **Parameters**:
  - `ticker`: Stock symbol (e.g., "TSLA")
  - `agent`: Agent ID (e.g., "FUNDAMENTAL_AGENT")

#### Market Mode: `GET /api/research/market-data?agent={agent}`
- **Location**: `@router.get("/market-data")` (line 832)
- **Parameters**:
  - `agent`: Agent ID (e.g., "EQUITY_AGENT")

---

### 2. **Cache Check (First Layer)**

```python
cache_key = get_cache_key("COMPANY", ticker, agent)
cached_result = get_cached_data(cache_key)
if cached_result:
    return cached_result  # Return immediately, skip processing
```

**Cache Key Generation**:
- Format: `{view_mode}_{ticker}_{agent}`
- Example: `COMPANY_TSLA_FUNDAMENTAL_AGENT`
- Hashed using MD5 for consistent key length

**Cache TTL**: 6 hours (configurable via `CACHE_TTL_HOURS`)

---

### 3. **Agent Selection & Data Collection**

Based on the `agent` parameter, the system:

#### A. **Identifies Agent Type**
- Looks up agent configuration from `COMPANY_AGENTS` or `MARKET_AGENTS` dictionary
- Each agent has:
  - `name`: Human-readable name
  - `focus`: What the agent specializes in
  - `sub_agents`: Dictionary of sub-agent IDs and names
  - `tone`: Writing style/tone for AI prompts

#### B. **Calls Appropriate Data Collection Function**

**For FUNDAMENTAL_AGENT** (processes all 3 sub-agents):
```python
# 1. Income Statement
raw_data = await collect_income_statement_data(ticker)
# Returns: {quarterly: {...}, annual: {...}, ltm: {...}}

# 2. Balance Sheet
raw_data = await collect_balance_sheet_data(ticker)
# Returns: {quarterly: {...}, annual: {...}, ltm: {...}}

# 3. Cash Flow
raw_data = await collect_cashflow_data(ticker)
# Returns: {quarterly: {...}, annual: {...}, ltm: {...}}
```

**For TRADING_AGENT** (processes all 3 sub-agents):
```python
# 1. Technical Indicators
raw_data = await collect_technical_indicator_data(ticker)
# Returns: {rsi: 65.5, macd: 2.3, ma_50: 250.0, ...}

# 2. Options Chain
raw_data = await collect_options_chain_data(ticker)
# Returns: {available_dates: [...], chains: {...}}

# 3. Insider Trading
raw_data = await collect_insider_trading_data(ticker)
# Returns: {total_transactions: 10, recent_transactions: [...]}
```

**For Other Agents**:
- `CSUIT_AGENT` → `collect_csuite_data(ticker)`
- `MANAGEMENT_AGENT` → `collect_management_mda_data(ticker)`
- `MARKET_AGENT` → `collect_market_data()`
- `BOND_AGENT` → `collect_bond_data()` + `collect_credit_data()`
- `ECONOMICS_AGENT` → `collect_economics_data()`

---

### 4. **AI Processing Phase: `process_data_with_agent()`**

**Location**: Line 326

#### Step 4.1: Get Agent Configuration
```python
agent_config = COMPANY_AGENTS.get(agent_id)
sub_agent_name = sub_agents.get(sub_agent_key, "Data Examiner")
```

#### Step 4.2: Build Specialized Prompt

The prompt is customized based on `sub_agent_key`:

**For INCOME_ANALYST_AGENT**:
```python
prompt = f"""As an Income Analyst Agent, examine, analyze, and interpret the following income statement data for {ticker}:

{str(raw_data)[:3000]}

Your task:
1. Extract key metrics (quarterly, annual, LTM)
2. Identify 4-6 most important metrics
3. Format numbers in billions (B) with 2 decimals
4. Write 200-300 word analysis covering:
   - Revenue trends and growth patterns
   - Profitability analysis
   - Operating efficiency
   - Key financial ratios
5. Provide 5-10 bullet points with critical insights

Return JSON with:
- data_metrics: Dictionary of key metrics
- insights: {analysis, bullet_points, encoded_output}
"""
```

**For BALANCE_ANALYST_AGENT**:
- Similar structure but focuses on:
  - Asset composition and quality
  - Liability structure and leverage
  - Equity trends
  - Liquidity position

**For CASHFLOW_ANALYST_AGENT**:
- Focuses on:
  - Cash generation capabilities
  - Operating cash flow trends
  - Capital allocation strategy
  - Free cash flow analysis

**For Other Agents**:
- Uses generic prompt template
- Adapts to agent's focus area

#### Step 4.3: Call OpenAI API

```python
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "system",
            "content": f"You are a {sub_agent_name} specializing in {agent_config['focus']}. Your tone is {agent_config['tone']}. Always return valid JSON."
        },
        {
            "role": "user",
            "content": prompt
        }
    ],
    temperature=0.7,
    max_tokens=2000,
    response_format={"type": "json_object"}  # Forces JSON output
)
```

**Key Parameters**:
- **Model**: `gpt-4o` (OpenAI's latest model)
- **Temperature**: `0.7` (balanced creativity/consistency)
- **Max Tokens**: `2000` (allows for comprehensive analysis)
- **Response Format**: `json_object` (ensures structured output)

#### Step 4.4: Parse AI Response

```python
analyzed = json.loads(response.choices[0].message.content)
# Expected structure:
# {
#   "data_metrics": {
#     "total revenue": "100.38B",
#     "cost of revenue": "79.38B",
#     ...
#   },
#   "insights": {
#     "analysis": "200-300 word comprehensive analysis...",
#     "bullet_points": ["Point 1", "Point 2", ...],
#     "encoded_output": null  # Will be generated
#   }
# }
```

#### Step 4.5: Encode Output

```python
insights_data = analyzed.get("insights", {})
if "encoded_output" not in insights_data:
    encoded_data = {
        "analysis": insights_data.get("analysis", ""),
        "bullet_points": insights_data.get("bullet_points", []),
        "timestamp": datetime.now().isoformat(),
        "agent": sub_agent_key,
        "ticker": ticker or "MARKET"
    }
    encoded_output = base64.b64encode(json.dumps(encoded_data).encode()).decode()
    insights_data["encoded_output"] = encoded_output
```

**Purpose**: Base64 encoding allows the full analysis to be stored compactly and decoded later if needed.

#### Step 4.6: Create Data Bubble

```python
bubble = {
    "id": f"{sub_agent_key}-{ticker}-{timestamp}",
    "type": sub_agent_key,  # e.g., "INCOME_ANALYST_AGENT"
    "category": "FINANCIAL" if "ANALYST" in sub_agent_key else "DATA",
    "title": "INCOME STATEMENT",  # Mapped from title_map
    "timestamp": datetime.now().isoformat(),
    "data": {
        "data_metrics": analyzed.get("data_metrics", {}),
        "insights": insights_data  # Contains analysis, bullet_points, encoded_output
    }
}
```

---

### 5. **Bubble Aggregation**

For agents with multiple sub-agents (e.g., `FUNDAMENTAL_AGENT`), the system:
1. Processes each sub-agent sequentially
2. Collects all bubbles into a list
3. Continues even if one sub-agent fails (error handling)

```python
bubbles = []
# Process INCOME_ANALYST_AGENT
bubble = await process_data_with_agent(...)
if bubble:
    bubbles.append(bubble)

# Process BALANCE_ANALYST_AGENT
bubble = await process_data_with_agent(...)
if bubble:
    bubbles.append(bubble)

# Process CASHFLOW_ANALYST_AGENT
bubble = await process_data_with_agent(...)
if bubble:
    bubbles.append(bubble)
```

---

### 6. **Cache & Return**

```python
result = {"bubbles": bubbles}
set_cached_data(cache_key, result)  # Cache for 6 hours
return result
```

---

## Agent Hierarchy

### Company Mode Agents

```
FUNDAMENTAL_AGENT
├── INCOME_ANALYST_AGENT
├── BALANCE_ANALYST_AGENT
└── CASHFLOW_ANALYST_AGENT

TRADING_AGENT
├── TECHNICAL_ANALYST_AGENT
├── OPTION_ANALYST_AGENT
└── INSIDE_TRADING_ANALYST_AGENT

CSUIT_AGENT
└── csuite (sub-agent)

MANAGEMENT_AGENT
└── management (sub-agent)

MARKET_AGENT
└── market (sub-agent)

BOND_AGENT
├── BOND_ANALYST_AGENT
└── CREDIT_ANALYST_AGENT

ECONOMICS_AGENT
└── economics (sub-agent)
```

### Market Mode Agents

```
EQUITY_AGENT
└── sp500 (sub-agent)

BOND_AGENT
└── treasury_yield (sub-agent)

ECONOMICS_AGENT
└── cpi (sub-agent)
```

---

## Data Collection Functions

### Financial Data (Yahoo Finance)
- `collect_income_statement_data()`: Quarterly, annual, LTM income statements
- `collect_balance_sheet_data()`: Quarterly, annual, LTM balance sheets
- `collect_cashflow_data()`: Quarterly, annual, LTM cash flow statements

### Trading Data (Yahoo Finance)
- `collect_technical_indicator_data()`: Calculates RSI, MACD, Moving Averages (50, 200), Volume ratios
- `collect_options_chain_data()`: Options chain with calls/puts, expiration dates, IV, volume, open interest

### SEC EDGAR Data
- `collect_insider_trading_data()`: Insider trading transactions (placeholder)
- `collect_management_mda_data()`: Latest 10-K and 10-Q filings with MD&A URLs

### Market Data (Yahoo Finance)
- `collect_market_data()`: S&P 500 data (price, change, PE ratio, market cap, volume)

### Mock Data (To Be Developed)
- `collect_csuite_data()`: C-Suite executive information
- `collect_bond_data()`: Bond analysis data
- `collect_credit_data()`: Credit analysis data
- `collect_economics_data()`: Economics indicators

---

## AI Prompt Structure

### System Message
```
You are a {sub_agent_name} specializing in {agent_config['focus']}. 
Your tone is {agent_config['tone']}. 
Always return valid JSON.
```

### User Message (Example for Income Statement)
```
As an Income Analyst Agent, examine, analyze, and interpret the following income statement data for TSLA:

{raw_data}

Your task:
1. Extract key metrics from the data (quarterly, annual, and LTM if available)
2. Identify the most important 4-6 metrics
3. Format numbers in billions (B) with 2 decimals
4. Write a comprehensive 200-300 word analysis explaining:
   - Revenue trends and growth patterns
   - Profitability analysis
   - Operating efficiency
   - Key financial ratios and their implications
5. Provide 5-10 bullet points highlighting:
   - Critical insights
   - Notable trends or changes
   - Risk factors or concerns
   - Opportunities or strengths

Return a JSON object with:
- data_metrics: Dictionary with key metric names (lowercase with spaces) and formatted values
- insights: Object with:
  - "analysis": String containing 200-300 words of comprehensive analysis
  - "bullet_points": Array of 5-10 bullet point strings
  - "encoded_output": String containing base64-encoded JSON of the full analysis
```

---

## Output Format

### Data Bubble Structure

```json
{
  "id": "INCOME_ANALYST_AGENT-TSLA-1234567890.123",
  "type": "INCOME_ANALYST_AGENT",
  "category": "FINANCIAL",
  "title": "INCOME STATEMENT",
  "timestamp": "2025-01-15T16:29:43.123456",
  "data": {
    "data_metrics": {
      "total revenue": "100.38B",
      "cost of revenue": "79.38B",
      "gross profit": "21.46B",
      "operating expense": "9.02B"
    },
    "insights": {
      "analysis": "Tesla's revenue has shown strong growth over the past year, driven primarily by increased vehicle deliveries and expansion into new markets. The company's gross profit margin has improved significantly, indicating better operational efficiency...",
      "bullet_points": [
        "Revenue increased 25% YoY, driven by Model Y and Model 3 sales",
        "Gross margin improved to 18.5% from 15.2% in previous year",
        "Operating expenses increased 12% but remained well-controlled",
        "Strong cash position supports continued expansion plans"
      ],
      "encoded_output": "eyJhbmFseXNpcyI6IlRlc2xhJ3MgcmV2ZW51ZSBoYXMgc2hvd24gLi4uIn0="
    }
  }
}
```

---

## Error Handling

### Data Collection Errors
- Each collection function has try/except blocks
- Returns empty dictionary `{}` on error
- Errors are logged but don't stop processing

### AI Processing Errors
- `process_data_with_agent()` returns `None` on error
- Errors are logged with full traceback
- Processing continues for other sub-agents

### Endpoint Errors
- Returns `{"bubbles": []}` on critical errors
- Full error traceback is logged for debugging

---

## Performance Optimizations

1. **Caching**: 6-hour TTL prevents redundant API calls
2. **Parallel Processing**: Sub-agents could be processed in parallel (currently sequential)
3. **Data Truncation**: Raw data is limited to 3000 characters in prompts to stay within token limits
4. **Error Isolation**: One sub-agent failure doesn't stop others

---

## Key Design Decisions

1. **Agent-Based Architecture**: Each agent has specialized knowledge and tone
2. **Sub-Agent Pattern**: Main agents delegate to specialized sub-agents
3. **Structured Output**: JSON format ensures consistent bubble structure
4. **Encoded Output**: Base64 encoding allows compact storage of full analysis
5. **Comprehensive Analysis**: 200-300 words + 5-10 bullet points provide depth
6. **Cache-First Strategy**: Reduces API costs and improves response time

---

## Future Enhancements

1. **Parallel Processing**: Process sub-agents concurrently using `asyncio.gather()`
2. **Streaming Responses**: Stream AI responses as they're generated
3. **Incremental Updates**: Update bubbles as they're processed
4. **Error Recovery**: Retry failed AI calls with exponential backoff
5. **Data Validation**: Validate AI response structure before creating bubbles
6. **Metrics Tracking**: Track AI processing time and success rates

