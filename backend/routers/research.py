"""
Research Intelligence Layer - Data Interpretation Service
Handles agent-based data interpretation using AI
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import openai
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import hashlib
import json

load_dotenv()

router = APIRouter()

# In-memory cache with TTL (Time To Live)
_cache = {}
CACHE_TTL_HOURS = 6  # Cache for 6 hours

def get_cache_key(view_mode: str, ticker: Optional[str], agent: str) -> str:
    """Generate a cache key for the request."""
    key_data = f"{view_mode}_{ticker or 'market'}_{agent}"
    return hashlib.md5(key_data.encode()).hexdigest()

def get_cached_data(cache_key: str) -> Optional[Dict]:
    """Get cached data if it exists and hasn't expired."""
    if cache_key in _cache:
        cached_item = _cache[cache_key]
        if datetime.now() < cached_item['expires_at']:
            return cached_item['data']
        else:
            # Expired, remove from cache
            del _cache[cache_key]
    return None

def set_cached_data(cache_key: str, data: Dict):
    """Store data in cache with expiration."""
    expires_at = datetime.now() + timedelta(hours=CACHE_TTL_HOURS)
    _cache[cache_key] = {
        'data': data,
        'expires_at': expires_at
    }

# OpenAI client setup
def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    return openai.OpenAI(api_key=api_key)


# Updated Agent Definitions
COMPANY_AGENTS = {
    "FUNDAMENTAL_AGENT": {
        "name": "Fundamental Agent",
        "focus": "Core Fundamentals (Income Statement, Balance Sheet, Cash Flow)",
        "sub_agents": {
            "INCOME_ANALYST_AGENT": "Income Analyst Agent",
            "BALANCE_ANALYST_AGENT": "Balance Analyst Agent",
            "CASHFLOW_ANALYST_AGENT": "Cashflow Analyst Agent"
        },
        "tone": "Analytical, data-driven, precise"
    },
    "TRADING_AGENT": {
        "name": "Trading Agent",
        "focus": "Trading Data (Technical Indicators, Options, Insider Trading)",
        "sub_agents": {
            "TECHNICAL_ANALYST_AGENT": "Technical Analyst Agent",
            "OPTION_ANALYST_AGENT": "Option Analyst Agent",
            "INSIDE_TRADING_ANALYST_AGENT": "Inside Trading Analyst Agent"
        },
        "tone": "Technical, market-focused, tactical"
    },
    "CSUIT_AGENT": {
        "name": "C-Suite Agent",
        "focus": "Executive Leadership (CEO, CTO, CFO Information)",
        "sub_agents": {
            "csuite": "C-Suite Analyst Agent"
        },
        "tone": "Qualitative, narrative-driven, insightful"
    },
    "MANAGEMENT_AGENT": {
        "name": "Management Agent",
        "focus": "Management Strategy (10K and 10Q Filings, MD&A)",
        "sub_agents": {
            "management": "Management Analyst Agent"
        },
        "tone": "Strategic, forward-looking, comprehensive"
    },
    "MARKET_AGENT": {
        "name": "Market Agent",
        "focus": "Market Context (S&P 500, Market Trends)",
        "sub_agents": {
            "market": "Market Analyst Agent"
        },
        "tone": "Market-focused, comparative, trend-oriented"
    },
    "BOND_AGENT": {
        "name": "Bond Agent",
        "focus": "Fixed Income Analysis (Bond and Credit Analysis)",
        "sub_agents": {
            "BOND_ANALYST_AGENT": "Bond Analyst Agent",
            "CREDIT_ANALYST_AGENT": "Credit Analyst Agent"
        },
        "tone": "Technical, rate-focused, macro-oriented"
    },
    "ECONOMICS_AGENT": {
        "name": "Economics Agent",
        "focus": "Macro Economic Indicators (CPI, Jobs, GDP)",
        "sub_agents": {
            "economics": "Economics Analyst Agent"
        },
        "tone": "Macro-economic, policy-aware, contextual"
    }
}

MARKET_AGENTS = {
    "EQUITY_AGENT": {
        "name": "Equity Agent",
        "focus": "Equity markets (S&P 500, Sector Performance, Index trends)",
        "sub_agents": {
            "sp500": "S&P 500 Index Agent"
        },
        "tone": "Market-focused, comparative, trend-oriented"
    },
    "BOND_AGENT": {
        "name": "Bond Agent",
        "focus": "Fixed income (Yield Curves, Treasury Rates, Spreads)",
        "sub_agents": {
            "treasury_yield": "Treasury Yield Agent"
        },
        "tone": "Technical, rate-focused, macro-oriented"
    },
    "ECONOMICS_AGENT": {
        "name": "Economics Agent",
        "focus": "Macro indicators (CPI, Jobs, GDP, Economic trends)",
        "sub_agents": {
            "cpi": "CPI Inflation Agent"
        },
        "tone": "Macro-economic, policy-aware, contextual"
    }
}


class InterpretRequest(BaseModel):
    bubble: Dict[str, Any]
    agent: str
    view_mode: str  # 'COMPANY' | 'MARKET'
    ticker: Optional[str] = None
    context: Optional[str] = ""


class DataBubbleResponse(BaseModel):
    bubbles: List[Dict[str, Any]]


@router.post("/interpret")
async def interpret_data(request: InterpretRequest):
    """
    Interpret data by collecting fresh data based on agent type, then generating analysis.
    Returns structured markdown with tables, analysis, and bullets.
    """
    try:
        client = get_openai_client()
        
        # Step 1: Get agent configuration
        agent_config = None
        if request.view_mode == "COMPANY":
            agent_config = COMPANY_AGENTS.get(request.agent)
        else:
            agent_config = MARKET_AGENTS.get(request.agent)
        
        if not agent_config:
            raise HTTPException(status_code=400, detail=f"Unknown agent: {request.agent}")
        
        # Step 2: Determine sub-agent based on bubble type
        bubble_type = request.bubble.get("type", "")
        sub_agent_key, sub_agent_name = determine_sub_agent(agent_config, bubble_type)
        
        # Step 3: Collect fresh data based on agent type and sub-agent
        raw_data = await collect_data_for_agent(
            request.agent,
            sub_agent_key,
            request.ticker
        )
        
        if not raw_data:
            raise HTTPException(status_code=404, detail=f"No data available for {sub_agent_key}")
        
        # Step 4: Build customized system message based on sub-agent (using collected data)
        system_message = build_system_message(agent_config, sub_agent_key, sub_agent_name)
        
        # Step 5: Build customized prompt based on sub-agent type (using collected data)
        prompt = build_interpretation_prompt_with_data(
            raw_data,
            agent_config,
            sub_agent_key,
            sub_agent_name,
            request.ticker,
            request.context,
            request.bubble  # Include original bubble for context
        )
        
        # Step 6: Generate interpretation
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": system_message
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        insight = response.choices[0].message.content
        
        return {"insight": insight, "agent": request.agent, "sub_agent": sub_agent_name, "sub_agent_key": sub_agent_key}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interpreting data: {str(e)}")


def determine_sub_agent(agent_config: Dict, bubble_type: str) -> tuple:
    """
    Determine the appropriate sub-agent based on bubble type.
    Returns (sub_agent_key, sub_agent_name) tuple.
    """
    sub_agents = agent_config.get("sub_agents", {})
    
    # Handle dict format (current structure)
    if isinstance(sub_agents, dict):
        # Map bubble types to sub-agent keys
        type_mapping = {
            "income_analyst": "INCOME_ANALYST_AGENT",
            "income": "INCOME_ANALYST_AGENT",
            "balance_analyst": "BALANCE_ANALYST_AGENT",
            "balance": "BALANCE_ANALYST_AGENT",
            "cashflow_analyst": "CASHFLOW_ANALYST_AGENT",
            "cashflow": "CASHFLOW_ANALYST_AGENT",
            "cash_flow": "CASHFLOW_ANALYST_AGENT",
            "technical_analyst": "TECHNICAL_ANALYST_AGENT",
            "technical": "TECHNICAL_ANALYST_AGENT",
            "option_analyst": "OPTION_ANALYST_AGENT",
            "options": "OPTION_ANALYST_AGENT",
            "inside_trading_analyst": "INSIDE_TRADING_ANALYST_AGENT",
            "insider": "INSIDE_TRADING_ANALYST_AGENT",
            "csuite": "csuite",
            "management": "management",
            "market": "market",
            "bond_analyst": "BOND_ANALYST_AGENT",
            "bond": "BOND_ANALYST_AGENT",
            "credit_analyst": "CREDIT_ANALYST_AGENT",
            "credit": "CREDIT_ANALYST_AGENT",
            "economics": "economics",
            "sp500": "sp500",
            "treasury": "treasury_yield",
            "yield": "treasury_yield",
            "cpi": "cpi",
            "inflation": "cpi"
        }
        
        bubble_type_lower = bubble_type.lower()
        for key, sub_key in type_mapping.items():
            if key in bubble_type_lower:
                if sub_key in sub_agents:
                    return (sub_key, sub_agents[sub_key])
        
        # Default to first sub-agent
        if sub_agents:
            first_key = list(sub_agents.keys())[0]
            return (first_key, sub_agents[first_key])
        return ("unknown", "Data Examiner")
    else:
        # Legacy list format
        type_mapping = {
            "income": "Income Examiner",
            "balance": "Balance Examiner",
            "cashflow": "Cash Flow Examiner",
            "options": "Options Examiner",
            "insider": "Insider Examiner",
            "sp500": "Index Examiner",
            "treasury": "Yield Examiner",
            "cpi": "Inflation Examiner"
        }
        
        for key, sub_agent in type_mapping.items():
            if key in bubble_type.lower():
                if sub_agent in sub_agents:
                    return (sub_agent, sub_agent)
        
        return (sub_agents[0] if sub_agents else "Data Examiner", sub_agents[0] if sub_agents else "Data Examiner")


def build_system_message(agent_config: Dict, sub_agent_key: str, sub_agent_name: str) -> str:
    """Build customized system message based on sub-agent type."""
    
    # Customized system messages for each sub-agent type
    if sub_agent_key == "INCOME_ANALYST_AGENT":
        return f"""You are an {sub_agent_name} (specialized {agent_config['name']}) specializing in income statement analysis.
Your tone is {agent_config['tone']}.
You excel at analyzing revenue trends, profitability, operating efficiency, and financial ratios.
You must output structured markdown with:
1. A markdown table summarizing key income statement metrics
2. A comprehensive analysis paragraph (200-300 words) covering revenue trends, profitability, and operating efficiency
3. 5-10 bullet points with critical insights, trends, risks, and opportunities
Always be precise, analytical, and use professional financial terminology."""
    
    elif sub_agent_key == "BALANCE_ANALYST_AGENT":
        return f"""You are a {sub_agent_name} (specialized {agent_config['name']}) specializing in balance sheet analysis.
Your tone is {agent_config['tone']}.
You excel at analyzing asset composition, liability structure, equity trends, liquidity, and financial health.
You must output structured markdown with:
1. A markdown table summarizing key balance sheet metrics
2. A comprehensive analysis paragraph (200-300 words) covering asset quality, leverage, equity, and liquidity
3. 5-10 bullet points with critical insights about financial position and health
Always be precise, analytical, and use professional financial terminology."""
    
    elif sub_agent_key == "CASHFLOW_ANALYST_AGENT":
        return f"""You are a {sub_agent_name} (specialized {agent_config['name']}) specializing in cash flow analysis.
Your tone is {agent_config['tone']}.
You excel at analyzing cash generation, operating cash flow trends, capital allocation, free cash flow, and liquidity.
You must output structured markdown with:
1. A markdown table summarizing key cash flow metrics
2. A comprehensive analysis paragraph (200-300 words) covering cash generation, operating trends, and capital allocation
3. 5-10 bullet points with critical insights about cash position and liquidity
Always be precise, analytical, and use professional financial terminology."""
    
    elif sub_agent_key == "TECHNICAL_ANALYST_AGENT":
        return f"""You are a {sub_agent_name} (specialized {agent_config['name']}) specializing in technical analysis.
Your tone is {agent_config['tone']}.
You excel at analyzing technical indicators (RSI, MACD, Moving Averages), price trends, volume patterns, and market sentiment.
You must output structured markdown with:
1. A markdown table summarizing key technical indicators
2. A comprehensive analysis paragraph (200-300 words) covering price trends, momentum, and market signals
3. 5-10 bullet points with critical insights about trading signals and market outlook
Always be precise, technical, and use professional trading terminology."""
    
    elif sub_agent_key == "OPTION_ANALYST_AGENT":
        return f"""You are a {sub_agent_name} (specialized {agent_config['name']}) specializing in options analysis.
Your tone is {agent_config['tone']}.
You excel at analyzing options chains, implied volatility, volume, open interest, and options market sentiment.
You must output structured markdown with:
1. A markdown table summarizing key options metrics
2. A comprehensive analysis paragraph (200-300 words) covering options flow, volatility, and market positioning
3. 5-10 bullet points with critical insights about options market dynamics
Always be precise, technical, and use professional options trading terminology."""
    
    elif sub_agent_key == "INSIDE_TRADING_ANALYST_AGENT":
        return f"""You are a {sub_agent_name} (specialized {agent_config['name']}) specializing in insider trading analysis.
Your tone is {agent_config['tone']}.
You excel at analyzing insider transactions, executive trading patterns, and their implications for company outlook.
You must output structured markdown with:
1. A markdown table summarizing key insider trading metrics
2. A comprehensive analysis paragraph (200-300 words) covering trading patterns and implications
3. 5-10 bullet points with critical insights about insider sentiment
Always be precise, analytical, and use professional financial terminology."""
    
    elif sub_agent_key == "BOND_ANALYST_AGENT" or sub_agent_key == "CREDIT_ANALYST_AGENT":
        return f"""You are a {sub_agent_name} (specialized {agent_config['name']}) specializing in bond and credit analysis.
Your tone is {agent_config['tone']}.
You excel at analyzing bond yields, credit spreads, credit quality, and fixed income market dynamics.
You must output structured markdown with:
1. A markdown table summarizing key bond/credit metrics
2. A comprehensive analysis paragraph (200-300 words) covering yield trends, credit quality, and market dynamics
3. 5-10 bullet points with critical insights about credit and bond markets
Always be precise, technical, and use professional fixed income terminology."""
    
    else:
        # Generic system message for other agents
        return f"""You are a {sub_agent_name} (specialized {agent_config['name']}) specializing in {agent_config['focus']}.
Your tone is {agent_config['tone']}.
You must output structured markdown with:
1. A markdown table summarizing key metrics
2. A comprehensive analysis paragraph (200-300 words)
3. 5-10 bullet points with critical insights
Always be precise, professional, and actionable."""


async def collect_data_for_agent(agent_id: str, sub_agent_key: str, ticker: Optional[str]) -> Dict[str, Any]:
    """Collect fresh data based on agent type and sub-agent."""
    try:
        if agent_id == "FUNDAMENTAL_AGENT":
            if sub_agent_key == "INCOME_ANALYST_AGENT":
                return await collect_income_statement_data(ticker) if ticker else {}
            elif sub_agent_key == "BALANCE_ANALYST_AGENT":
                return await collect_balance_sheet_data(ticker) if ticker else {}
            elif sub_agent_key == "CASHFLOW_ANALYST_AGENT":
                return await collect_cashflow_data(ticker) if ticker else {}
        
        elif agent_id == "TRADING_AGENT":
            if sub_agent_key == "TECHNICAL_ANALYST_AGENT":
                return await collect_technical_indicator_data(ticker) if ticker else {}
            elif sub_agent_key == "OPTION_ANALYST_AGENT":
                return await collect_options_chain_data(ticker) if ticker else {}
            elif sub_agent_key == "INSIDE_TRADING_ANALYST_AGENT":
                return await collect_insider_trading_data(ticker) if ticker else {}
        
        elif agent_id == "CSUIT_AGENT":
            return await collect_csuite_data(ticker) if ticker else {}
        
        elif agent_id == "MANAGEMENT_AGENT":
            return await collect_management_mda_data(ticker) if ticker else {}
        
        elif agent_id == "MARKET_AGENT":
            return await collect_market_data()
        
        elif agent_id == "BOND_AGENT":
            if sub_agent_key == "BOND_ANALYST_AGENT":
                return await collect_bond_data()
            elif sub_agent_key == "CREDIT_ANALYST_AGENT":
                return await collect_credit_data()
        
        elif agent_id == "ECONOMICS_AGENT":
            return await collect_economics_data()
        
        return {}
    except Exception as e:
        print(f"Error collecting data for agent {agent_id}/{sub_agent_key}: {e}")
        return {}


def build_interpretation_prompt_with_data(
    raw_data: Dict[str, Any],
    agent_config: Dict,
    sub_agent_key: str,
    sub_agent_name: str,
    ticker: Optional[str],
    context: str,
    original_bubble: Optional[Dict[str, Any]] = None
) -> str:
    """Build customized interpretation prompt using collected raw data."""
    
    ticker_context = f"for {ticker}" if ticker else "for the market"
    
    # Extract existing insights from original bubble if available
    existing_analysis = ""
    if original_bubble:
        existing_insights = original_bubble.get("data", {}).get("insights", {})
        if isinstance(existing_insights, dict):
            existing_analysis = existing_insights.get("analysis", "")
    
    # Build customized prompt based on sub-agent type, using raw_data
    if sub_agent_key == "INCOME_ANALYST_AGENT":
        prompt = f"""As an {sub_agent_name} (specialized {agent_config['name']}), examine, analyze, and interpret the following income statement data {ticker_context}:

**Raw Data:**
{str(raw_data)[:3000]}

"""
        if existing_analysis:
            prompt += f"**Previous Analysis Context:**\n{existing_analysis[:300]}...\n\n"
        
        if context:
            prompt += f"**Current Report Context:**\n{context[:500]}...\n\n"
        
        prompt += """**Your Task:**
1. Extract key metrics from the data (quarterly, annual, and LTM if available)
2. Identify the most important 4-6 metrics (e.g., Total Revenue, Cost of Revenue, Gross Profit, Operating Expenses, Net Income)
3. Format numbers in billions (B) with 2 decimals (e.g., "100.38B")
4. Create a markdown table with the key income statement metrics
5. Write a comprehensive analysis paragraph (200-300 words) that:
   - Analyzes revenue trends and growth patterns in detail
   - Evaluates profitability and margin trends
   - Assesses operating efficiency and cost management
   - Discusses key financial ratios and their implications
   - Compares current performance to historical trends
6. Provide 5-10 bullet points with:
   - Critical insights about revenue and profitability
   - Notable trends or significant changes
   - Risk factors or concerns
   - Opportunities or competitive strengths
   - Forward-looking implications

**Requirements:**
- Be specific and quantitative, referencing the exact data provided
- Connect insights to broader market/company context
- Use professional financial terminology
- Highlight both positive and negative trends
- If this is part of a larger analysis, reference how it fits into the narrative

Output your analysis in clean markdown format."""
    
    elif sub_agent_key == "BALANCE_ANALYST_AGENT":
        prompt = f"""As a {sub_agent_name} (specialized {agent_config['name']}), examine, analyze, and interpret the following balance sheet data {ticker_context}:

**Raw Data:**
{str(raw_data)[:3000]}

"""
        if existing_analysis:
            prompt += f"**Previous Analysis Context:**\n{existing_analysis[:300]}...\n\n"
        
        if context:
            prompt += f"**Current Report Context:**\n{context[:500]}...\n\n"
        
        prompt += """**Your Task:**
1. Extract key metrics from the data (quarterly, annual, and LTM if available)
2. Identify the most important 4-6 metrics (e.g., Total Assets, Total Liabilities, Total Equity, Cash & Equivalents, Debt)
3. Format numbers in billions (B) with 2 decimals
4. Create a markdown table with the key balance sheet metrics
5. Write a comprehensive analysis paragraph (200-300 words) that:
   - Analyzes asset composition and quality
   - Evaluates liability structure and leverage ratios
   - Assesses equity trends and shareholder value
   - Examines liquidity position and working capital
   - Discusses financial health indicators and solvency
6. Provide 5-10 bullet points with:
   - Critical insights about financial position
   - Notable trends in assets, liabilities, or equity
   - Risk factors related to leverage or liquidity
   - Strengths in financial structure
   - Implications for future financial flexibility

Output your analysis in clean markdown format."""
    
    elif sub_agent_key == "CASHFLOW_ANALYST_AGENT":
        prompt = f"""As a {sub_agent_name} (specialized {agent_config['name']}), examine, analyze, and interpret the following cash flow data {ticker_context}:

**Raw Data:**
{str(raw_data)[:3000]}

"""
        if existing_analysis:
            prompt += f"**Previous Analysis Context:**\n{existing_analysis[:300]}...\n\n"
        
        if context:
            prompt += f"**Current Report Context:**\n{context[:500]}...\n\n"
        
        prompt += """**Your Task:**
1. Extract key metrics from the data (quarterly, annual, and LTM if available)
2. Identify the most important 4-6 metrics (e.g., Operating Cash Flow, Capital Expenditures, Free Cash Flow, Debt Issuance)
3. Format numbers in billions (B) with 2 decimals (include negative signs where applicable)
4. Create a markdown table with the key cash flow metrics
5. Write a comprehensive analysis paragraph (200-300 words) that:
   - Analyzes cash generation capabilities and trends
   - Evaluates operating cash flow quality and sustainability
   - Assesses capital allocation strategy and capital expenditures
   - Examines free cash flow and its implications
   - Discusses cash position, liquidity, and financial flexibility
6. Provide 5-10 bullet points with:
   - Critical insights about cash generation
   - Notable trends in operating, investing, or financing cash flows
   - Risk factors related to cash flow sustainability
   - Strengths in cash management
   - Implications for future capital allocation

Output your analysis in clean markdown format."""
    
    elif sub_agent_key == "TECHNICAL_ANALYST_AGENT":
        prompt = f"""As a {sub_agent_name} (specialized {agent_config['name']}), examine, analyze, and interpret the following technical indicator data {ticker_context}:

**Raw Data:**
{str(raw_data)[:3000]}

"""
        if existing_analysis:
            prompt += f"**Previous Analysis Context:**\n{existing_analysis[:300]}...\n\n"
        
        if context:
            prompt += f"**Current Report Context:**\n{context[:500]}...\n\n"
        
        prompt += """**Your Task:**
1. Extract key technical indicators from the data (RSI, MACD, Moving Averages, Volume)
2. Create a markdown table with the key technical indicators
3. Write a comprehensive analysis paragraph (200-300 words) that:
   - Analyzes price trends and momentum signals
   - Evaluates technical indicator readings and their significance
   - Assesses volume patterns and market participation
   - Discusses support/resistance levels and trend direction
   - Identifies potential entry/exit signals
4. Provide 5-10 bullet points with:
   - Critical technical insights and signals
   - Notable patterns or formations
   - Risk factors or bearish signals
   - Opportunities or bullish signals
   - Trading implications and outlook

Output your analysis in clean markdown format."""
    
    elif sub_agent_key == "OPTION_ANALYST_AGENT":
        prompt = f"""As a {sub_agent_name} (specialized {agent_config['name']}), examine, analyze, and interpret the following options chain data {ticker_context}:

**Raw Data:**
{str(raw_data)[:3000]}

"""
        if existing_analysis:
            prompt += f"**Previous Analysis Context:**\n{existing_analysis[:300]}...\n\n"
        
        if context:
            prompt += f"**Current Report Context:**\n{context[:500]}...\n\n"
        
        prompt += """**Your Task:**
1. Extract key options metrics (volume, open interest, IV, put/call ratios)
2. Create a markdown table with the key options metrics
3. Write a comprehensive analysis paragraph (200-300 words) that:
   - Analyzes options flow and market positioning
   - Evaluates implied volatility levels and their significance
   - Assesses put/call ratios and market sentiment
   - Discusses unusual options activity and its implications
   - Identifies potential market expectations
4. Provide 5-10 bullet points with:
   - Critical insights about options market dynamics
   - Notable patterns in volume or open interest
   - Risk factors or bearish positioning
   - Opportunities or bullish positioning
   - Trading implications and market outlook

Output your analysis in clean markdown format."""
    
    elif sub_agent_key == "INSIDE_TRADING_ANALYST_AGENT":
        prompt = f"""As a {sub_agent_name} (specialized {agent_config['name']}), examine, analyze, and interpret the following insider trading data {ticker_context}:

**Raw Data:**
{str(raw_data)[:3000]}

"""
        if existing_analysis:
            prompt += f"**Previous Analysis Context:**\n{existing_analysis[:300]}...\n\n"
        
        if context:
            prompt += f"**Current Report Context:**\n{context[:500]}...\n\n"
        
        prompt += """**Your Task:**
1. Extract key insider trading metrics
2. Create a markdown table with the key insider trading metrics
3. Write a comprehensive analysis paragraph (200-300 words) that:
   - Analyzes insider trading patterns and trends
   - Evaluates executive trading activity and its significance
   - Assesses the balance between buys and sells
   - Discusses implications for company outlook and management confidence
   - Identifies any unusual or significant transactions
4. Provide 5-10 bullet points with:
   - Critical insights about insider sentiment
   - Notable patterns in executive trading
   - Risk factors or bearish signals
   - Opportunities or bullish signals
   - Implications for company outlook

Output your analysis in clean markdown format."""
    
    else:
        # Generic prompt for other agents
        prompt = f"""As a {sub_agent_name} (specialized {agent_config['name']}), examine, analyze, and interpret the following data {ticker_context}:

**Raw Data:**
{str(raw_data)[:3000]}

"""
        if existing_analysis:
            prompt += f"**Previous Analysis Context:**\n{existing_analysis[:300]}...\n\n"
        
        if context:
            prompt += f"**Current Report Context:**\n{context[:500]}...\n\n"
        
        prompt += """**Your Task:**
1. Extract the most important 4-6 key metrics from the data
2. Format numbers appropriately (billions with "B", millions with "M", percentages with "%")
3. Create a markdown table with the key metrics
4. Write a comprehensive analysis paragraph (200-300 words)
5. Provide 5-10 bullet points with critical insights

**Requirements:**
- Be specific and quantitative where possible
- Connect insights to broader market/company context
- Use professional terminology
- Highlight any anomalies or notable patterns
- If this is part of a larger analysis, reference how it fits into the narrative

Output your analysis in clean markdown format."""
    
    return prompt


async def process_data_with_agent(raw_data: Dict, agent_id: str, sub_agent_key: str, ticker: Optional[str] = None) -> Dict:
    """
    Process raw data through AI agent and return analyzed data bubble.
    Outputs: 200-300 words insights, 5-10 bullet points, and encoded output.
    """
    try:
        client = get_openai_client()
        agent_config = COMPANY_AGENTS.get(agent_id)
        
        if not agent_config:
            return None
        
        sub_agents = agent_config.get("sub_agents", {})
        sub_agent_name = sub_agents.get(sub_agent_key, "Data Examiner")
        
        # Build analysis prompt based on agent type
        ticker_context = f"for {ticker}" if ticker else "for the market"
        
        if sub_agent_key == "INCOME_ANALYST_AGENT":
            prompt = f"""As an {sub_agent_name} (specialized {agent_config['name']}), examine, analyze, and interpret the following income statement data {ticker_context}:

{str(raw_data)[:3000]}

Your task:
1. Extract key metrics from the data (quarterly, annual, and LTM if available)
2. Identify the most important 4-6 metrics (e.g., Total Revenue, Cost of Revenue, Gross Profit, Operating Expenses, Net Income)
3. Format numbers in billions (B) with 2 decimals (e.g., "100.38B")
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
  - "encoded_output": String containing base64-encoded JSON of the full analysis (for future use)

IMPORTANT: 
- Be thorough and analytical
- Use professional financial terminology
- Highlight both positive and negative trends
- Provide actionable insights"""
        
        elif sub_agent_key == "BALANCE_ANALYST_AGENT":
            prompt = f"""As a {sub_agent_name} (specialized {agent_config['name']}), examine, analyze, and interpret the following balance sheet data {ticker_context}:

{str(raw_data)[:3000]}

Your task:
1. Extract key metrics from the data (quarterly, annual, and LTM if available)
2. Identify the most important 4-6 metrics (e.g., Total Assets, Total Liabilities, Total Equity, Cash & Equivalents, Debt)
3. Format numbers in billions (B) with 2 decimals
4. Write a comprehensive 200-300 word analysis explaining:
   - Asset composition and quality
   - Liability structure and leverage
   - Equity trends
   - Liquidity position
   - Financial health indicators
5. Provide 5-10 bullet points highlighting critical insights

Return a JSON object with:
- data_metrics: Dictionary with key metric names (lowercase with spaces) and formatted values
- insights: Object with analysis, bullet_points, and encoded_output"""
        
        elif sub_agent_key == "CASHFLOW_ANALYST_AGENT":
            prompt = f"""As a {sub_agent_name} (specialized {agent_config['name']}), examine, analyze, and interpret the following cash flow data {ticker_context}:

{str(raw_data)[:3000]}

Your task:
1. Extract key metrics from the data (quarterly, annual, and LTM if available)
2. Identify the most important 4-6 metrics (e.g., Operating Cash Flow, Capital Expenditures, Free Cash Flow, Debt Issuance)
3. Format numbers in billions (B) with 2 decimals (include negative signs where applicable)
4. Write a comprehensive 200-300 word analysis explaining:
   - Cash generation capabilities
   - Operating cash flow trends
   - Capital allocation strategy
   - Free cash flow analysis
   - Cash position and liquidity
5. Provide 5-10 bullet points highlighting critical insights

Return a JSON object with:
- data_metrics: Dictionary with key metric names (lowercase with spaces) and formatted values
- insights: Object with analysis, bullet_points, and encoded_output"""
        
        else:
            # Generic prompt for other agents
            prompt = f"""As a {sub_agent_name} (specialized {agent_config['name']}), examine, analyze, and interpret the following data {ticker_context}:

{str(raw_data)[:3000]}

Your task:
1. Extract the most important 4-6 key metrics from the data
2. Format numbers appropriately (billions with "B", millions with "M", percentages with "%")
3. Write a comprehensive 200-300 word analysis
4. Provide 5-10 bullet points with critical insights

Return a JSON object with:
- data_metrics: Dictionary with key metric names (lowercase with spaces) and formatted values
- insights: Object with:
  - "analysis": String containing 200-300 words of comprehensive analysis
  - "bullet_points": Array of 5-10 bullet point strings
  - "encoded_output": String containing base64-encoded JSON of the full analysis"""
        
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
            response_format={"type": "json_object"}
        )
        
        import json
        import base64
        analyzed = json.loads(response.choices[0].message.content)
        
        # Encode the full analysis if not already encoded
        insights_data = analyzed.get("insights", {})
        if isinstance(insights_data, dict) and "encoded_output" not in insights_data:
            # Create encoded output
            encoded_data = {
                "analysis": insights_data.get("analysis", ""),
                "bullet_points": insights_data.get("bullet_points", []),
                "timestamp": datetime.now().isoformat(),
                "agent": sub_agent_key,
                "ticker": ticker or "MARKET"
            }
            encoded_output = base64.b64encode(json.dumps(encoded_data).encode()).decode()
            insights_data["encoded_output"] = encoded_output
        
        # Determine title based on agent type
        title_map = {
            "INCOME_ANALYST_AGENT": "INCOME STATEMENT",
            "BALANCE_ANALYST_AGENT": "BALANCE SHEET",
            "CASHFLOW_ANALYST_AGENT": "CASH FLOW",
            "TECHNICAL_ANALYST_AGENT": "TECHNICAL ANALYSIS",
            "OPTION_ANALYST_AGENT": "OPTIONS ANALYSIS",
            "INSIDE_TRADING_ANALYST_AGENT": "INSIDER TRADING",
            "csuite": "C-SUITE EXECUTIVES",
            "management": "MANAGEMENT DISCUSSION",
            "market": "MARKET ANALYSIS",
            "BOND_ANALYST_AGENT": "BOND ANALYSIS",
            "CREDIT_ANALYST_AGENT": "CREDIT ANALYSIS",
            "economics": "ECONOMICS ANALYSIS"
        }
        title = title_map.get(sub_agent_key, sub_agent_key.replace("_", " "))
        
        # Create data bubble with new format
        bubble_id = f"{sub_agent_key}-{ticker or 'market'}-{datetime.now().timestamp()}"
        
        bubble = {
            "id": bubble_id,
            "type": sub_agent_key,
            "category": "FINANCIAL" if "ANALYST" in sub_agent_key else "DATA",
            "title": title,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "data_metrics": analyzed.get("data_metrics", {}),
                "insights": insights_data
            }
        }
        
        return bubble
        
    except Exception as e:
        print(f"Error processing data with agent: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_icon_for_type(data_type: str) -> str:
    """Get icon emoji for data type."""
    icon_map = {
        "income_statement": "📊",
        "balance_sheet": "⚖️",
        "cash_flow": "📊",  # Bar chart icon like Income Statement per image
        "institutional_holdings": "🏦",
        "options_data": "📈",
        "insider_trading": "👤",
        "10k_filing": "📝",
        "sp500": "📈",
        "treasury_yield": "💵",
        "cpi": "📊"
    }
    return icon_map.get(data_type, "📊")


@router.get("/company-data/{ticker}")
async def get_company_data(ticker: str, agent: str = Query(..., description="Agent ID")):
    """
    Fetch company data bubbles for the given ticker and agent.
    Data is collected, processed through AI agent, and returned as data bubbles.
    Uses caching to prevent frequent API calls.
    """
    try:
        # Log the ticker being used
        print(f"[RESEARCH] Fetching company data for ticker: {ticker}, agent: {agent}")
        
        # Check cache first
        cache_key = get_cache_key("COMPANY", ticker, agent)
        cached_result = get_cached_data(cache_key)
        if cached_result:
            print(f"[RESEARCH] Returning cached data for {ticker} - {agent}")
            return cached_result
        
        print(f"[RESEARCH] Cache miss - fetching fresh data for {ticker}")
        bubbles = []
        
        if agent == "FUNDAMENTAL_AGENT":
            # Process all three sub-agents
            print(f"[RESEARCH] FUNDAMENTAL_AGENT: Processing all sub-agents for {ticker}")
            
            # INCOME_ANALYST_AGENT
            try:
                raw_data = await collect_income_statement_data(ticker)
                if raw_data:
                    bubble = await process_data_with_agent(
                        raw_data,
                        "FUNDAMENTAL_AGENT",
                        "INCOME_ANALYST_AGENT",
                        ticker
                    )
                    if bubble:
                        bubbles.append(bubble)
            except Exception as e:
                print(f"Error processing income statement: {e}")
            
            # BALANCE_ANALYST_AGENT
            try:
                raw_data = await collect_balance_sheet_data(ticker)
                if raw_data:
                    bubble = await process_data_with_agent(
                        raw_data,
                        "FUNDAMENTAL_AGENT",
                        "BALANCE_ANALYST_AGENT",
                        ticker
                    )
                    if bubble:
                        bubbles.append(bubble)
            except Exception as e:
                print(f"Error processing balance sheet: {e}")
            
            # CASHFLOW_ANALYST_AGENT
            try:
                raw_data = await collect_cashflow_data(ticker)
                if raw_data:
                    bubble = await process_data_with_agent(
                        raw_data,
                        "FUNDAMENTAL_AGENT",
                        "CASHFLOW_ANALYST_AGENT",
                        ticker
                    )
                    if bubble:
                        bubbles.append(bubble)
            except Exception as e:
                print(f"Error processing cash flow: {e}")
        
        elif agent == "TRADING_AGENT":
            # Process all three sub-agents
            print(f"[RESEARCH] TRADING_AGENT: Processing all sub-agents for {ticker}")
            
            # TECHNICAL_ANALYST_AGENT
            try:
                raw_data = await collect_technical_indicator_data(ticker)
                if raw_data:
                    bubble = await process_data_with_agent(
                        raw_data,
                        "TRADING_AGENT",
                        "TECHNICAL_ANALYST_AGENT",
                        ticker
                    )
                    if bubble:
                        bubbles.append(bubble)
            except Exception as e:
                print(f"Error processing technical indicators: {e}")
            
            # OPTION_ANALYST_AGENT
            try:
                raw_data = await collect_options_chain_data(ticker)
                if raw_data:
                    bubble = await process_data_with_agent(
                        raw_data,
                        "TRADING_AGENT",
                        "OPTION_ANALYST_AGENT",
                        ticker
                    )
                    if bubble:
                        bubbles.append(bubble)
            except Exception as e:
                print(f"Error processing options chain: {e}")
            
            # INSIDE_TRADING_ANALYST_AGENT
            try:
                raw_data = await collect_insider_trading_data(ticker)
                if raw_data:
                    bubble = await process_data_with_agent(
                        raw_data,
                        "TRADING_AGENT",
                        "INSIDE_TRADING_ANALYST_AGENT",
                        ticker
                    )
                    if bubble:
                        bubbles.append(bubble)
            except Exception as e:
                print(f"Error processing insider trading: {e}")
        
        elif agent == "CSUIT_AGENT":
            try:
                raw_data = await collect_csuite_data(ticker)
                if raw_data:
                    bubble = await process_data_with_agent(
                        raw_data,
                        "CSUIT_AGENT",
                        "csuite",
                        ticker
                    )
                    if bubble:
                        bubbles.append(bubble)
            except Exception as e:
                print(f"Error processing C-Suite data: {e}")
        
        elif agent == "MANAGEMENT_AGENT":
            try:
                raw_data = await collect_management_mda_data(ticker)
                if raw_data:
                    bubble = await process_data_with_agent(
                        raw_data,
                        "MANAGEMENT_AGENT",
                        "management",
                        ticker
                    )
                    if bubble:
                        bubbles.append(bubble)
            except Exception as e:
                print(f"Error processing management MDA data: {e}")
        
        elif agent == "MARKET_AGENT":
            try:
                raw_data = await collect_market_data()
                if raw_data:
                    bubble = await process_data_with_agent(
                        raw_data,
                        "MARKET_AGENT",
                        "market",
                        ticker
                    )
                    if bubble:
                        bubbles.append(bubble)
            except Exception as e:
                print(f"Error processing market data: {e}")
        
        elif agent == "BOND_AGENT":
            # Process both sub-agents
            print(f"[RESEARCH] BOND_AGENT: Processing all sub-agents for {ticker}")
            
            # BOND_ANALYST_AGENT
            try:
                raw_data = await collect_bond_data()
                if raw_data:
                    bubble = await process_data_with_agent(
                        raw_data,
                        "BOND_AGENT",
                        "BOND_ANALYST_AGENT",
                        ticker
                    )
                    if bubble:
                        bubbles.append(bubble)
            except Exception as e:
                print(f"Error processing bond data: {e}")
            
            # CREDIT_ANALYST_AGENT
            try:
                raw_data = await collect_credit_data()
                if raw_data:
                    bubble = await process_data_with_agent(
                        raw_data,
                        "BOND_AGENT",
                        "CREDIT_ANALYST_AGENT",
                        ticker
                    )
                    if bubble:
                        bubbles.append(bubble)
            except Exception as e:
                print(f"Error processing credit data: {e}")
        
        elif agent == "ECONOMICS_AGENT":
            try:
                raw_data = await collect_economics_data()
                if raw_data:
                    bubble = await process_data_with_agent(
                        raw_data,
                        "ECONOMICS_AGENT",
                        "economics",
                        ticker
                    )
                    if bubble:
                        bubbles.append(bubble)
            except Exception as e:
                print(f"Error processing economics data: {e}")
        
        result = {"bubbles": bubbles}
        
        # Cache the result
        set_cached_data(cache_key, result)
        
        print(f"[RESEARCH] Returning {len(bubbles)} bubbles for {ticker} - {agent}")
        return result
            
    except Exception as e:
        print(f"Error in get_company_data: {e}")
        import traceback
        traceback.print_exc()
        return {"bubbles": []}


async def process_market_data_with_agent(raw_data: Dict, agent_id: str, sub_agent_key: str) -> Dict:
    """
    Process raw market data through AI agent and return analyzed data bubble.
    """
    try:
        client = get_openai_client()
        agent_config = MARKET_AGENTS.get(agent_id)
        
        if not agent_config:
            return None
        
        sub_agents = agent_config.get("sub_agents", {})
        sub_agent_name = sub_agents.get(sub_agent_key, "Data Examiner")
        
        # Build analysis prompt
        prompt = f"""As a {sub_agent_name} (specialized {agent_config['name']}), examine, analyze, and interpret the following market data:

{str(raw_data)[:2000]}

Extract and summarize the key metrics in a structured format. Focus on:
1. Key market metrics and their values
2. Notable trends or changes
3. Important relationships or patterns
4. Market implications

Return a JSON object with:
- title: A descriptive title
- category: Data source (e.g., "FRED", "YAHOO FINANCE")
- key_metrics: Dictionary of key metric names and formatted values
- insights: List of 2-3 key insights

Format numbers appropriately (percentages, basis points, etc.)."""
        
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
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        
        import json
        analyzed = json.loads(response.choices[0].message.content)
        
        # Create data bubble
        bubble = {
            "id": f"{sub_agent_key}-{datetime.now().timestamp()}",
            "type": sub_agent_key,
            "category": analyzed.get("category", "MARKET"),
            "icon": get_icon_for_type(sub_agent_key),
            "title": analyzed.get("title", f"{sub_agent_name.upper()}"),
            "subtitle": "GLOBAL MARKET",
            "timestamp": datetime.now().isoformat(),
            "data": analyzed.get("key_metrics", {}),
            "insights": analyzed.get("insights", [])
        }
        
        return bubble
        
    except Exception as e:
        print(f"Error processing market data with agent: {e}")
        return None


@router.get("/market-data")
async def get_market_data(agent: str = Query(..., description="Agent ID")):
    """
    Fetch global market data bubbles for the given agent.
    Data is fetched, processed through AI agent, and returned as data bubbles.
    Uses caching to prevent frequent API calls.
    """
    try:
        # Check cache first
        cache_key = get_cache_key("MARKET", None, agent)
        cached_result = get_cached_data(cache_key)
        if cached_result:
            print(f"Returning cached market data for {agent}")
            return cached_result
        
        import yfinance as yf
        from pandas_datareader import data as web
        import os
        from datetime import datetime, timedelta
        
        bubbles = []
        
        if agent == "MARKET_AGENT":
            # Market Agent - Fetch S&P 500 data (same as EQUITY_AGENT for now)
            try:
                raw_data = await collect_market_data()
                if raw_data:
                    bubble = await process_data_with_agent(
                        raw_data,
                        "MARKET_AGENT",
                        "market",
                        None  # No ticker for market data
                    )
                    if bubble:
                        bubbles.append(bubble)
            except Exception as e:
                print(f"Error processing market data: {e}")
        
        elif agent == "EQUITY_AGENT":
            # S&P 500 Agent - Fetch S&P 500 data
            try:
                sp500 = yf.Ticker("^GSPC")
                info = sp500.info
                history = sp500.history(period="1mo")
                
                if not history.empty:
                    current_price = float(history['Close'].iloc[-1])
                    prev_close = float(history['Close'].iloc[-2]) if len(history) > 1 else current_price
                    change = current_price - prev_close
                    change_pct = (change / prev_close * 100) if prev_close > 0 else 0
                    
                    # Get additional metrics
                    pe_ratio = info.get('trailingPE', 0)
                    market_cap = info.get('marketCap', 0)
                    
                    sp500_data = {
                        "type": "sp500",
                        "data": {
                            "current_price": current_price,
                            "previous_close": prev_close,
                            "change": change,
                            "change_percent": change_pct,
                            "pe_ratio": pe_ratio,
                            "market_cap": market_cap,
                            "volume": int(history['Volume'].iloc[-1]) if 'Volume' in history.columns else 0
                        }
                    }
                    
                    bubble = await process_market_data_with_agent(
                        sp500_data,
                        "EQUITY_AGENT",
                        "sp500"
                    )
                    if bubble:
                        bubbles.append(bubble)
            except Exception as e:
                print(f"Error fetching S&P 500 data: {e}")
        
        elif agent == "BOND_AGENT":
            # Treasury Yield Agent - Fetch Treasury yield data
            try:
                fred_api_key = os.getenv('FRED_API_KEY')
                if fred_api_key:
                    # Fetch 10-Year Treasury Yield
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=365)
                    
                    df = web.DataReader('DGS10', 'fred', start=start_date, end=end_date, api_key=fred_api_key)
                    df = df.dropna()
                    
                    if not df.empty:
                        latest_value = float(df.iloc[-1, 0])
                        prev_value = float(df.iloc[-2, 0]) if len(df) > 1 else latest_value
                        change_bps = (latest_value - prev_value) * 100  # Convert to basis points
                        
                        # Also fetch 2-year and 30-year for context
                        df_2y = web.DataReader('DGS2', 'fred', start=start_date, end=end_date, api_key=fred_api_key)
                        df_30y = web.DataReader('DGS30', 'fred', start=start_date, end=end_date, api_key=fred_api_key)
                        
                        yield_2y = float(df_2y.iloc[-1, 0]) if not df_2y.empty else None
                        yield_30y = float(df_30y.iloc[-1, 0]) if not df_30y.empty else None
                        
                        treasury_data = {
                            "type": "treasury_yield",
                            "data": {
                                "10y_yield": latest_value,
                                "2y_yield": yield_2y,
                                "30y_yield": yield_30y,
                                "change_bps": change_bps,
                                "2s10s_spread": (latest_value - yield_2y) if yield_2y else None,
                                "10s30s_spread": (yield_30y - latest_value) if yield_30y else None
                            }
                        }
                        
                        bubble = await process_market_data_with_agent(
                            treasury_data,
                            "BOND_AGENT",
                            "treasury_yield"
                        )
                        if bubble:
                            bubbles.append(bubble)
            except Exception as e:
                print(f"Error fetching Treasury yield data: {e}")
        
        elif agent == "ECONOMICS_AGENT":
            # CPI Agent - Fetch CPI data
            try:
                fred_api_key = os.getenv('FRED_API_KEY')
                if fred_api_key:
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=365*2)  # 2 years for YoY calculation
                    
                    df = web.DataReader('CPIAUCSL', 'fred', start=start_date, end=end_date, api_key=fred_api_key)
                    df = df.dropna()
                    
                    if not df.empty and len(df) > 12:  # Need at least 12 months for YoY
                        latest_value = float(df.iloc[-1, 0])
                        year_ago_value = float(df.iloc[-13, 0]) if len(df) > 12 else latest_value
                        yoy_change = ((latest_value - year_ago_value) / year_ago_value * 100) if year_ago_value > 0 else 0
                        
                        # Month-over-month change
                        prev_month_value = float(df.iloc[-2, 0]) if len(df) > 1 else latest_value
                        mom_change = ((latest_value - prev_month_value) / prev_month_value * 100) if prev_month_value > 0 else 0
                        
                        cpi_data = {
                            "type": "cpi",
                            "data": {
                                "current_cpi": latest_value,
                                "year_ago_cpi": year_ago_value,
                                "yoy_change_percent": yoy_change,
                                "mom_change_percent": mom_change,
                                "latest_date": df.index[-1].strftime('%Y-%m-%d')
                            }
                        }
                        
                        bubble = await process_market_data_with_agent(
                            cpi_data,
                            "ECONOMICS_AGENT",
                            "cpi"
                        )
                        if bubble:
                            bubbles.append(bubble)
            except Exception as e:
                print(f"Error fetching CPI data: {e}")
        
        result = {"bubbles": bubbles}
        
        # Cache the result
        set_cached_data(cache_key, result)
        
        return result
        
    except Exception as e:
        print(f"Error in get_market_data: {e}")
        return {"bubbles": []}


def format_billions(value: float) -> str:
    """Format a number in billions."""
    if value == 0:
        return "0.00B"
    billions = value / 1_000_000_000
    return f"{billions:.2f}B"


# ============================================================================
# DATA COLLECTION FUNCTIONS
# ============================================================================

async def collect_income_statement_data(ticker: str) -> Dict[str, Any]:
    """Collect income statement data (quarterly and annual) from Yahoo Finance."""
    try:
        from routers.internal import get_micro_data
        micro_data = await get_micro_data(ticker)
        
        return {
            "quarterly": micro_data.get('financials', {}).get('quarterly', {}),
            "annual": micro_data.get('financials', {}).get('annual', {}),
            "ltm": micro_data.get('financials', {}).get('ltm', {})
        }
    except Exception as e:
        print(f"Error collecting income statement data for {ticker}: {e}")
        return {}


async def collect_balance_sheet_data(ticker: str) -> Dict[str, Any]:
    """Collect balance sheet data (quarterly and annual) from Yahoo Finance."""
    try:
        from routers.internal import get_micro_data
        micro_data = await get_micro_data(ticker)
        
        return {
            "quarterly": micro_data.get('balance_sheet', {}).get('quarterly', {}),
            "annual": micro_data.get('balance_sheet', {}).get('annual', {}),
            "ltm": micro_data.get('balance_sheet', {}).get('ltm', {})
        }
    except Exception as e:
        print(f"Error collecting balance sheet data for {ticker}: {e}")
        return {}


async def collect_cashflow_data(ticker: str) -> Dict[str, Any]:
    """Collect cash flow data (quarterly and annual) from Yahoo Finance."""
    try:
        from routers.internal import get_micro_data
        micro_data = await get_micro_data(ticker)
        
        return {
            "quarterly": micro_data.get('cashflow', {}).get('quarterly', {}),
            "annual": micro_data.get('cashflow', {}).get('annual', {}),
            "ltm": micro_data.get('cashflow', {}).get('ltm', {})
        }
    except Exception as e:
        print(f"Error collecting cashflow data for {ticker}: {e}")
        return {}


async def collect_technical_indicator_data(ticker: str) -> Dict[str, Any]:
    """Collect technical indicator data (RSI, MACD, Moving Averages, Volume) from Yahoo Finance."""
    try:
        import yfinance as yf
        import pandas as pd
        import numpy as np
        
        stock = yf.Ticker(ticker)
        history = stock.history(period="1y")
        
        if history.empty:
            return {}
        
        # Calculate RSI (Relative Strength Index)
        delta = history['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Calculate MACD
        exp1 = history['Close'].ewm(span=12, adjust=False).mean()
        exp2 = history['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        
        # Moving Averages
        ma_50 = history['Close'].rolling(window=50).mean()
        ma_200 = history['Close'].rolling(window=200).mean()
        
        # Volume indicators
        avg_volume = history['Volume'].rolling(window=20).mean()
        volume_ratio = history['Volume'].iloc[-1] / avg_volume.iloc[-1] if not avg_volume.empty else 1
        
        return {
            "rsi": float(rsi.iloc[-1]) if not rsi.empty else None,
            "macd": float(macd.iloc[-1]) if not macd.empty else None,
            "macd_signal": float(signal.iloc[-1]) if not signal.empty else None,
            "ma_50": float(ma_50.iloc[-1]) if not ma_50.empty else None,
            "ma_200": float(ma_200.iloc[-1]) if not ma_200.empty else None,
            "current_price": float(history['Close'].iloc[-1]),
            "volume_ratio": float(volume_ratio),
            "volume": int(history['Volume'].iloc[-1])
        }
    except Exception as e:
        print(f"Error collecting technical indicator data for {ticker}: {e}")
        return {}


async def collect_options_chain_data(ticker: str) -> Dict[str, Any]:
    """Collect options chain data (calls, puts, expiration dates, strike prices, IV, etc.) from Yahoo Finance."""
    try:
        import yfinance as yf
        import pandas as pd
        
        stock = yf.Ticker(ticker)
        options_dates = stock.options
        
        if not options_dates or len(options_dates) == 0:
            return {}
        
        # Get options for nearest expiration (weekly) and next monthly expiration
        nearest_date = options_dates[0]
        monthly_dates = [d for d in options_dates if len(d) == 10]  # YYYY-MM-DD format
        
        options_data = {
            "available_dates": list(options_dates[:10]),  # First 10 expiration dates
            "nearest_expiration": nearest_date,
            "chains": {}
        }
        
        # Get chain for nearest expiration
        try:
            chain = stock.option_chain(nearest_date)
            
            # Process calls
            calls = chain.calls if not chain.calls.empty else pd.DataFrame()
            # Process puts
            puts = chain.puts if not chain.puts.empty else pd.DataFrame()
            
            options_data["chains"][nearest_date] = {
                "calls": {
                    "count": len(calls),
                    "total_volume": int(calls['volume'].sum()) if 'volume' in calls.columns else 0,
                    "total_open_interest": int(calls['openInterest'].sum()) if 'openInterest' in calls.columns else 0,
                    "avg_iv": float(calls['impliedVolatility'].mean()) if 'impliedVolatility' in calls.columns else None,
                    "sample": calls.head(5).to_dict('records') if len(calls) > 0 else []
                },
                "puts": {
                    "count": len(puts),
                    "total_volume": int(puts['volume'].sum()) if 'volume' in puts.columns else 0,
                    "total_open_interest": int(puts['openInterest'].sum()) if 'openInterest' in puts.columns else 0,
                    "avg_iv": float(puts['impliedVolatility'].mean()) if 'impliedVolatility' in puts.columns else None,
                    "sample": puts.head(5).to_dict('records') if len(puts) > 0 else []
                }
            }
        except Exception as e:
            print(f"Error fetching options chain for {nearest_date}: {e}")
        
        return options_data
    except Exception as e:
        print(f"Error collecting options chain data for {ticker}: {e}")
        return {}


async def collect_insider_trading_data(ticker: str) -> Dict[str, Any]:
    """Collect insider trading data from SEC EDGAR."""
    try:
        from services.edgar_service import edgar_service
        
        # Get insider transactions from SEC EDGAR
        # Note: This is a placeholder - actual implementation depends on edgar_service API
        submissions = edgar_service.get_company_submissions(ticker)
        
        if "error" in submissions:
            return {}
        
        # Mock data structure - to be replaced with actual SEC EDGAR data
        return {
            "total_transactions": 0,
            "recent_transactions": [],
            "note": "SEC EDGAR insider trading data collection - to be implemented"
        }
    except Exception as e:
        print(f"Error collecting insider trading data for {ticker}: {e}")
        return {}


async def collect_csuite_data(ticker: str) -> Dict[str, Any]:
    """Collect C-Suite executive data (mock data for now)."""
    # Mock data - to be developed later
    return {
        "ceo": {
            "name": "Mock CEO",
            "title": "Chief Executive Officer",
            "tenure": "5 years"
        },
        "cto": {
            "name": "Mock CTO",
            "title": "Chief Technology Officer",
            "tenure": "3 years"
        },
        "cfo": {
            "name": "Mock CFO",
            "title": "Chief Financial Officer",
            "tenure": "4 years"
        },
        "note": "C-Suite data collection - to be developed"
    }


async def collect_management_mda_data(ticker: str) -> Dict[str, Any]:
    """Collect Management Discussion & Analysis from latest 10-K and 10-Q filings."""
    try:
        from services.edgar_service import edgar_service
        
        submissions = edgar_service.get_company_submissions(ticker)
        if "error" in submissions:
            return {}
        
        filings = submissions.get("filings", {}).get("recent", {})
        forms = filings.get("form", [])
        dates = filings.get("filingDate", [])
        accession_numbers = filings.get("accessionNumber", [])
        primary_docs = filings.get("primaryDocument", [])
        
        mda_data = {
            "10k": None,
            "10q": None
        }
        
        # Find latest 10-K
        for i, form in enumerate(forms):
            if form == "10-K":
                cik = submissions.get("cik", "")
                accession = accession_numbers[i].replace("-", "")
                filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{primary_docs[i]}"
                
                mda_data["10k"] = {
                    "form": form,
                    "filing_date": dates[i],
                    "url": filing_url,
                    "accession_number": accession_numbers[i],
                    "note": "MD&A extraction - to be implemented"
                }
                break
        
        # Find latest 10-Q
        for i, form in enumerate(forms):
            if form == "10-Q":
                cik = submissions.get("cik", "")
                accession = accession_numbers[i].replace("-", "")
                filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{primary_docs[i]}"
                
                mda_data["10q"] = {
                    "form": form,
                    "filing_date": dates[i],
                    "url": filing_url,
                    "accession_number": accession_numbers[i],
                    "note": "MD&A extraction - to be implemented"
                }
                break
        
        return mda_data
    except Exception as e:
        print(f"Error collecting management MDA data for {ticker}: {e}")
        return {}


async def collect_market_data() -> Dict[str, Any]:
    """Collect S&P 500 market data from Yahoo Finance."""
    try:
        import yfinance as yf
        
        sp500 = yf.Ticker("^GSPC")
        info = sp500.info
        history = sp500.history(period="1mo")
        
        if history.empty:
            return {}
        
        current_price = float(history['Close'].iloc[-1])
        prev_close = float(history['Close'].iloc[-2]) if len(history) > 1 else current_price
        change = current_price - prev_close
        change_pct = (change / prev_close * 100) if prev_close > 0 else 0
        
        return {
            "current_price": current_price,
            "previous_close": prev_close,
            "change": change,
            "change_percent": change_pct,
            "pe_ratio": info.get('trailingPE', None),
            "market_cap": info.get('marketCap', None),
            "volume": int(history['Volume'].iloc[-1]) if 'Volume' in history.columns else 0
        }
    except Exception as e:
        print(f"Error collecting market data: {e}")
        return {}


async def collect_bond_data() -> Dict[str, Any]:
    """Collect bond analysis data (mock data for now)."""
    # Mock data - to be developed later
    return {
        "note": "Bond analyst data collection - to be developed"
    }


async def collect_credit_data() -> Dict[str, Any]:
    """Collect credit analysis data (mock data for now)."""
    # Mock data - to be developed later
    return {
        "note": "Credit analyst data collection - to be developed"
    }


async def collect_economics_data() -> Dict[str, Any]:
    """Collect economics data (mock data for now)."""
    # Mock data - to be developed later
    return {
        "note": "Economics data collection - to be developed"
    }
