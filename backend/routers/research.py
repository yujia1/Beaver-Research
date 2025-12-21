"""
Research Intelligence Layer - Data Interpretation Service
Handles agent-based data interpretation using AI
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from routers.auth import verify_premium_access
import models
from pydantic import BaseModel
from typing import Optional, Dict, Any
import openai
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import hashlib
import json
import base64

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



from services.research_engine import ResearchEngine, COMPANY_AGENTS, MARKET_AGENTS
from routers.research_helpers import (
    build_fundamental_agent_system_message,
    build_fundamental_agent_interpretation_prompt
)


class InterpretRequest(BaseModel):
    bubble: Dict[str, Any] = {}
    agent: str
    view_mode: str  # 'COMPANY' | 'MARKET'
    ticker: Optional[str] = None
    context: Optional[str] = ""

# Initialize Engine
engine = ResearchEngine()

# Helpers (moved collection logic here or import it)
# For this refactor, we need to keep collect_data_for_agent available
# We will import it or keep it if it was local.
# Looking at original file, collect_data_for_agent was not shown in the snippet but assumed to exist.
# We will assume it's defined later in the file and keep it, but use engine for processing.

@router.post("/process")
async def process_data_agent(
    request: InterpretRequest,
    data_agent: str = Query(..., alias="data-agent", description="The agent to use for data processing"),
    current_user: models.User = Depends(verify_premium_access)
):
    """
    Process data by collecting fresh data based on agent type, then generating analysis.
    Returns structured markdown with tables, analysis, and bullets.
    """
    try:
        print(f"[PROCESS 1.1] process_data_agent: Starting with data_agent={data_agent}")
        
        # Step 1: Collect Data (Keeping this logic in router/helper for now as data fetching layer)
        # Note: In a full refactor, data fetching should also be a service.
        # We need to find where collect_data_for_agent is defined.
        # Assuming it's in this file or imported.
        
        # Re-using the prompt logic determination which moved to engine, 
        # but we need to fetch data first.
        
        # Quick check on agent type to pass to collection
        agent_id = data_agent
        agent_config = None
        if request.view_mode == "COMPANY":
            agent_config = COMPANY_AGENTS.get(agent_id)
        else:
            agent_config = MARKET_AGENTS.get(agent_id)
            
        if not agent_config:
             raise HTTPException(status_code=400, detail=f"Unknown agent: {agent_id}")

        bubble_type = request.bubble.get("type", "")
        # Use engine helper to get sub agent key for data collection
        sub_agent_key, sub_agent_name = engine.determine_sub_agent(agent_config, bubble_type)
        
        print(f"[PROCESS 1.3] Collecting data for {sub_agent_key}")
        
        # We need 'collect_data_for_agent' to be available. 
        # I will define a wrapper lambda to pass to the engine if engine handles the flow,
        # OR handle collection here and pass data to engine.
        # The Engine.process_data method I wrote expects a callback or we can change it to take data.
        # Let's use the callback approach or just collect here.
        
        raw_data = await collect_data_for_agent(agent_id, sub_agent_key, request.ticker)
        
        if not raw_data:
            raise HTTPException(status_code=404, detail="No data available")
            
        # Step 2: Use Engine to process
        # We can bypass the engine.process_data wrapper if we prefer to just call the AI generation directly
        # or use the wrapper. The wrapper does the determination again.
        # Let's just use the lower level engine methods to construct the prompt and call AI
        # to match the previous flow exactly but with cleaner code.
        
        # Actually, let's use the engine's process_data if we can pass the data collector.
        # Helper:
        async def collector_wrapper(a, s, t): return raw_data
        
        result = await engine.process_data(
            agent_id=agent_id,
            view_mode=request.view_mode,
            ticker=request.ticker,
            bubble=request.bubble,
            context=request.context,
            collect_data_fn=collector_wrapper
        )
        
        return result

    except Exception as e:
        print(f"[ERROR] process_data_agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing data: {str(e)}")
    





















async def collect_data_for_agent(agent_id: str, sub_agent_key: str, ticker: Optional[str]) -> Dict[str, Any]:
    """Collect fresh data based on agent type and sub-agent."""
    try:
        if agent_id == "FUNDAMENTAL_AGENT":
            # Collect all three financial statements for merged analysis
            if sub_agent_key == "FUNDAMENTAL_AGENT":
                income_data = await collect_income_statement_data(ticker) if ticker else {}
                balance_data = await collect_balance_sheet_data(ticker) if ticker else {}
                cashflow_data = await collect_cashflow_data(ticker) if ticker else {}
                
                # Combine all three statements
                return {
                    "income_statement": income_data,
                    "balance_sheet": balance_data,
                    "cash_flow": cashflow_data
                }
        
        elif agent_id == "TRADING_AGENT":
            if sub_agent_key == "OPTION_ANALYST_AGENT":
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


# ============================================================================
# AGENT-SPECIFIC INTERPRETATION PROMPT BUILDERS
# ============================================================================




async def process_data_with_agent(raw_data: Dict, agent_id: str, sub_agent_key: str, ticker: Optional[str] = None) -> Dict:
    """
    Process raw data through AI agent and return analyzed data bubble.
    For financial statements (Income, Balance, Cash Flow), processes quarterly and annual data separately.
    Outputs: 200-300 words insights, 5-10 bullet points, and encoded output.
    """
    try:
        client = get_openai_client()
        agent_config = COMPANY_AGENTS.get(agent_id)
        
        if not agent_config:
            return None
        
        sub_agents = agent_config.get("sub_agents", {})
        sub_agent_name = sub_agents.get(sub_agent_key, "Data Examiner")
        
        ticker_context = f"for {ticker}" if ticker else "for the market"
        
        # Handle financial statements with quarterly and annual data separately
        # Legacy special handling disabled to use generic engine logic
        if False and sub_agent_key in ["INCOME_ANALYST_AGENT", "BALANCE_ANALYST_AGENT", "CASHFLOW_ANALYST_AGENT"]:
             pass
            # Former call to process_financial_statement_data
        
        # For other agents, use the original single processing
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
        import re
        
        # Robust JSON parsing with error handling
        try:
            analyzed = json.loads(response.choices[0].message.content)
        except json.JSONDecodeError as e:
            print(f"JSON decode error for {sub_agent_name}: {e}")
            print(f"Raw response content: {response.choices[0].message.content[:500]}...")
            
            # Attempt to extract JSON from markdown code blocks if present
            content = response.choices[0].message.content
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                try:
                    analyzed = json.loads(json_match.group(1))
                    print(f"Successfully extracted JSON from markdown block")
                except json.JSONDecodeError:
                    pass
            
            # If still failing, try to find any JSON object in the response
            if 'analyzed' not in locals():
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    try:
                        analyzed = json.loads(json_match.group(0))
                        print(f"Successfully extracted JSON object from response")
                    except json.JSONDecodeError:
                        pass
            
            # Final fallback: return a structured error response
            if 'analyzed' not in locals():
                analyzed = {
                    "insights": {
                        "analysis": f"Error: Unable to parse response from {sub_agent_name}. The AI returned malformed JSON.",
                        "bullet_points": [
                            "JSON parsing failed",
                            "Please try again or contact support"
                        ]
                    },
                    "error": str(e)
                }
        
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


@router.get("/financial-analysis/{ticker}")
async def get_financial_analysis(ticker: str, period: str = "annual"):
    """Fetch and analyze comprehensive financial statements for a ticker."""
    try:
        print(f"[FINANCIAL_ANALYSIS] Fetching financial analysis for {ticker}, period: {period}")
        
        # Collect all three financial statements
        income_data = await collect_income_statement_data(ticker)
        balance_data = await collect_balance_sheet_data(ticker)
        cashflow_data = await collect_cashflow_data(ticker)
        
        # Combine all three statements
        combined_data = {
            "income_statement": income_data,
            "balance_sheet": balance_data,
            "cash_flow": cashflow_data
        }
        
        print(f"[FINANCIAL_ANALYSIS] Data collected, building prompt...")
        
        # Get agent config
        agent_config = COMPANY_AGENTS.get("FUNDAMENTAL_AGENT", {})
        sub_agent_name = "Fundamental Agent"
        
        # Build interpretation prompt
        prompt = build_fundamental_agent_interpretation_prompt(
            combined_data,
            agent_config,
            sub_agent_name,
            ticker,
            f"{period} financial analysis",
            None
        )
        
        print(f"[FINANCIAL_ANALYSIS] Calling AI for analysis...")
        
        # Call OpenAI API
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": build_fundamental_agent_system_message(agent_config, sub_agent_name)},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        analysis_text = response.choices[0].message.content
        
        print(f"[FINANCIAL_ANALYSIS] AI analysis complete, length: {len(analysis_text)}")
        
        # Extract bullet points from analysis (look for lines starting with - or •)
        bullet_points = []
        for line in analysis_text.split('\n'):
            line = line.strip()
            if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                bullet_points.append(line.lstrip('-•* '))
        
        # If no bullet points found, create some from the analysis
        if not bullet_points:
            bullet_points = [
                "Comprehensive financial analysis completed",
                "Review all three statements for complete picture",
                f"Analysis based on {period} data"
            ]
        
        # Create encoded output
        encoded_output = base64.b64encode(json.dumps({
            "analysis": analysis_text,
            "bullet_points": bullet_points[:10],  # Limit to 10
            "period": period,
            "agent": "FUNDAMENTAL_AGENT",
            "ticker": ticker,
            "timestamp": datetime.now().isoformat()
        }).encode()).decode()
        
        return {
            "success": True,
            "data": {
                "analysis": analysis_text,
                "bullet_points": bullet_points[:10],
                "encoded_output": encoded_output,
                "period": period
            }
        }
        
    except Exception as e:
        print(f"[FINANCIAL_ANALYSIS] Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/company-data/{ticker}")
async def get_company_data(
    ticker: str, 
    agent: str = Query(..., description="Agent ID"),
    refresh: bool = Query(False, description="Force refresh and bypass cache")
):
    """
    Fetch company data bubbles for the given ticker and agent.
    Data is collected, processed through AI agent, and returned as data bubbles.
    Uses caching to prevent frequent API calls.
    """
    try:
        # Log the ticker being used
        print(f"[RESEARCH] Fetching company data for ticker: {ticker}, agent: {agent}, refresh: {refresh}")
        
        # Check cache first (unless refresh is requested)
        cache_key = get_cache_key("COMPANY", ticker, agent)
        if refresh:
            print(f"[RESEARCH] Refresh requested - clearing cache for {ticker} - {agent}")
            if cache_key in _cache:
                del _cache[cache_key]
        else:
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
                print(f"[MAIN 1.1] get_company_data: Processing INCOME_ANALYST_AGENT for {ticker}")
                raw_data = await collect_income_statement_data(ticker)
                print(f"[MAIN 1.2] get_company_data: collect_income_statement_data returned, keys: {list(raw_data.keys()) if raw_data else 'None'}")
                if raw_data:
                    print(f"[MAIN 1.3] get_company_data: Calling process_data_with_agent for INCOME_ANALYST_AGENT")
                    bubble = await process_data_with_agent(
                        raw_data,
                        "FUNDAMENTAL_AGENT",
                        "INCOME_ANALYST_AGENT",
                        ticker
                    )
                    print(f"[MAIN 1.4] get_company_data: process_data_with_agent returned, bubble: {bubble is not None}")
                    if bubble:
                        print(f"[MAIN 1.5] get_company_data: Adding INCOME_ANALYST_AGENT bubble to results")
                        bubbles.append(bubble)
                    else:
                        print(f"[MAIN 1.6] get_company_data: INCOME_ANALYST_AGENT bubble is None, skipping")
                else:
                    print(f"[MAIN 1.7] get_company_data: INCOME_ANALYST_AGENT raw_data is empty, skipping")
            except Exception as e:
                print(f"[ERROR] get_company_data: Error processing income statement: {e}")
                import traceback
                traceback.print_exc()
            
            # BALANCE_ANALYST_AGENT
            try:
                print(f"[MAIN 2.1] get_company_data: Processing BALANCE_ANALYST_AGENT for {ticker}")
                raw_data = await collect_balance_sheet_data(ticker)
                print(f"[MAIN 2.2] get_company_data: collect_balance_sheet_data returned, keys: {list(raw_data.keys()) if raw_data else 'None'}")
                if raw_data:
                    print(f"[MAIN 2.3] get_company_data: Calling process_data_with_agent for BALANCE_ANALYST_AGENT")
                    bubble = await process_data_with_agent(
                        raw_data,
                        "FUNDAMENTAL_AGENT",
                        "BALANCE_ANALYST_AGENT",
                        ticker
                    )
                    print(f"[MAIN 2.4] get_company_data: process_data_with_agent returned, bubble: {bubble is not None}")
                    if bubble:
                        print(f"[MAIN 2.5] get_company_data: Adding BALANCE_ANALYST_AGENT bubble to results")
                        print(f"  - bubble title: {bubble.get('title')}")
                        print(f"  - bubble data keys: {list(bubble.get('data', {}).keys())}")
                        bubbles.append(bubble)
                    else:
                        print(f"[MAIN 2.6] get_company_data: BALANCE_ANALYST_AGENT bubble is None, skipping")
                else:
                    print(f"[MAIN 2.7] get_company_data: BALANCE_ANALYST_AGENT raw_data is empty, skipping")
            except Exception as e:
                print(f"[ERROR] get_company_data: Error processing balance sheet: {e}")
                import traceback
                traceback.print_exc()
            
            # CASHFLOW_ANALYST_AGENT
            try:
                print(f"[MAIN 3.1] get_company_data: Processing CASHFLOW_ANALYST_AGENT for {ticker}")
                raw_data = await collect_cashflow_data(ticker)
                print(f"[MAIN 3.2] get_company_data: collect_cashflow_data returned, keys: {list(raw_data.keys()) if raw_data else 'None'}")
                if raw_data:
                    print(f"[MAIN 3.3] get_company_data: Calling process_data_with_agent for CASHFLOW_ANALYST_AGENT")
                    bubble = await process_data_with_agent(
                        raw_data,
                        "FUNDAMENTAL_AGENT",
                        "CASHFLOW_ANALYST_AGENT",
                        ticker
                    )
                    print(f"[MAIN 3.4] get_company_data: process_data_with_agent returned, bubble: {bubble is not None}")
                    if bubble:
                        print(f"[MAIN 3.5] get_company_data: Adding CASHFLOW_ANALYST_AGENT bubble to results")
                        print(f"  - bubble title: {bubble.get('title')}")
                        print(f"  - bubble data keys: {list(bubble.get('data', {}).keys())}")
                        bubbles.append(bubble)
                    else:
                        print(f"[MAIN 3.6] get_company_data: CASHFLOW_ANALYST_AGENT bubble is None, skipping")
                else:
                    print(f"[MAIN 3.7] get_company_data: CASHFLOW_ANALYST_AGENT raw_data is empty, skipping")
            except Exception as e:
                print(f"[ERROR] get_company_data: Error processing cash flow: {e}")
                import traceback
                traceback.print_exc()
        
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
        
        # Final Summary Log
        print(f"[SUMMARY] ========================================")
        print(f"[SUMMARY] get_company_data: Final Results for {ticker} - {agent}")
        print(f"[SUMMARY] Total bubbles: {len(bubbles)}")
        for i, bubble in enumerate(bubbles):
            print(f"[SUMMARY] Bubble {i+1}:")
            print(f"  - type: {bubble.get('type')}")
            print(f"  - title: {bubble.get('title')}")
            print(f"  - data keys: {list(bubble.get('data', {}).keys())}")
            if 'Annually' in bubble.get('data', {}):
                ann_data = bubble.get('data', {}).get('Annually', {})
                ann_metrics = ann_data.get('data_metrics', {})
                print(f"  - ✓ Annually: data_metrics count={len(ann_metrics)}, keys={list(ann_metrics.keys())[:5]}")
            else:
                print(f"  - ✗ Annually: MISSING")
            if 'Quarterly' in bubble.get('data', {}):
                qtr_data = bubble.get('data', {}).get('Quarterly', {})
                qtr_metrics = qtr_data.get('data_metrics', {})
                print(f"  - ✓ Quarterly: data_metrics count={len(qtr_metrics)}, keys={list(qtr_metrics.keys())[:5]}")
            else:
                print(f"  - ✗ Quarterly: MISSING")
        print(f"[SUMMARY] ========================================")
        
        # Cache the result
        set_cached_data(cache_key, result)
        
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
async def get_market_data(
    agent: str = Query(..., description="Agent ID"),
    refresh: bool = Query(False, description="Force refresh and bypass cache")
):
    """
    Fetch global market data bubbles for the given agent.
    Data is fetched, processed through AI agent, and returned as data bubbles.
    Uses caching to prevent frequent API calls.
    """
    try:
        # Check cache first (unless refresh is requested)
        cache_key = get_cache_key("MARKET", None, agent)
        if refresh:
            print(f"[RESEARCH] Refresh requested - clearing cache for MARKET - {agent}")
            if cache_key in _cache:
                del _cache[cache_key]
        else:
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


# ============================================================================
# DATA COLLECTION FUNCTIONS
# ============================================================================

async def collect_income_statement_data(ticker: str) -> Dict[str, Any]:
    """Collect income statement data (quarterly and annual) from Yahoo Finance."""
    try:
        import pandas as pd
        print(f"[STEP 1.1] collect_income_statement_data: Starting for ticker {ticker}")
        from routers.internal import get_micro_data
        
        print(f"[STEP 1.2] collect_income_statement_data: Calling get_micro_data({ticker})")
        micro_data = await get_micro_data(ticker)
        print(f"[STEP 1.3] collect_income_statement_data: get_micro_data returned, keys: {list(micro_data.keys())}")
        
        print(f"[STEP 1.4] collect_income_statement_data: Extracting financials")
        financials = micro_data.get('financials', {})
        quarterly = financials.get('quarterly', {})
        annual = financials.get('annual', {})
        ltm = financials.get('ltm', {})
        
        # Convert dictionaries to pandas DataFrames and print
        def dict_to_dataframe(data_dict: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
            """Convert {metric: {date: value}} to DataFrame with metrics as rows and dates as columns."""
            if not data_dict:
                return pd.DataFrame()
            
            # Collect all unique dates
            all_dates = set()
            for metric_data in data_dict.values():
                if isinstance(metric_data, dict):
                    all_dates.update(metric_data.keys())
            
            if not all_dates:
                return pd.DataFrame()
            
            # Create DataFrame
            df_data = {}
            for metric, date_values in data_dict.items():
                if isinstance(date_values, dict):
                    df_data[metric] = {date: date_values.get(date) for date in all_dates}
            
            df = pd.DataFrame(df_data).T  # Transpose so metrics are rows, dates are columns
            return df
        
        # Convert and print quarterly data
        if quarterly:
            print(f"\n[STEP 1.5] collect_income_statement_data: QUARTERLY Income Statement (as DataFrame):")
            quarterly_df = dict_to_dataframe(quarterly)
            if not quarterly_df.empty:
                print(quarterly_df.to_string())
            else:
                print("  (Empty DataFrame)")
        
        # Convert and print annual data
        if annual:
            print(f"\n[STEP 1.6] collect_income_statement_data: ANNUAL Income Statement (as DataFrame):")
            annual_df = dict_to_dataframe(annual)
            if not annual_df.empty:
                print(annual_df.to_string())
            else:
                print("  (Empty DataFrame)")
        
        # Convert and print LTM data
        if ltm:
            print(f"\n[STEP 1.7] collect_income_statement_data: LTM Income Statement (as DataFrame):")
            ltm_df = pd.DataFrame([ltm]).T  # LTM is {metric: value}, convert to single-column DataFrame
            if not ltm_df.empty:
                print(ltm_df.to_string())
            else:
                print("  (Empty DataFrame)")
        
        print(f"\n[STEP 1.8] collect_income_statement_data: NOTE: LTM (Last Twelve Months) is a current snapshot that could be quarterly or annual. It is collected but not processed separately.")
        
        result = {
            "quarterly": quarterly,
            "annual": annual,
            "ltm": ltm  # LTM is collected but not processed separately - it's a current snapshot
        }
        
        print(f"[STEP 1.9] collect_income_statement_data: Returning result with keys: {list(result.keys())}")
        return result
    except Exception as e:
        print(f"[ERROR] collect_income_statement_data: {e}")
        import traceback
        traceback.print_exc()
        return {}


async def collect_balance_sheet_data(ticker: str) -> Dict[str, Any]:
    """Collect balance sheet data (quarterly and annual) from Yahoo Finance."""
    try:
        import pandas as pd
        print(f"[STEP 2.1] collect_balance_sheet_data: Starting for ticker {ticker}")
        from routers.internal import get_micro_data
        
        print(f"[STEP 2.2] collect_balance_sheet_data: Calling get_micro_data({ticker})")
        micro_data = await get_micro_data(ticker)
        print(f"[STEP 2.3] collect_balance_sheet_data: get_micro_data returned, keys: {list(micro_data.keys())}")
        
        print(f"[STEP 2.4] collect_balance_sheet_data: Extracting balance_sheet")
        balance_sheet = micro_data.get('balance_sheet', {})
        quarterly = balance_sheet.get('quarterly', {})
        annual = balance_sheet.get('annual', {})
        ltm = balance_sheet.get('ltm', {})
        
        # Convert dictionaries to pandas DataFrames and print
        def dict_to_dataframe(data_dict: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
            """Convert {metric: {date: value}} to DataFrame with metrics as rows and dates as columns."""
            if not data_dict:
                return pd.DataFrame()
            
            # Collect all unique dates
            all_dates = set()
            for metric_data in data_dict.values():
                if isinstance(metric_data, dict):
                    all_dates.update(metric_data.keys())
            
            if not all_dates:
                return pd.DataFrame()
            
            # Create DataFrame
            df_data = {}
            for metric, date_values in data_dict.items():
                if isinstance(date_values, dict):
                    df_data[metric] = {date: date_values.get(date) for date in all_dates}
            
            df = pd.DataFrame(df_data).T  # Transpose so metrics are rows, dates are columns
            return df
        
        # Convert and print quarterly data
        if quarterly:
            print(f"\n[STEP 2.5] collect_balance_sheet_data: QUARTERLY Balance Sheet (as DataFrame):")
            quarterly_df = dict_to_dataframe(quarterly)
            if not quarterly_df.empty:
                print(quarterly_df.to_string())
            else:
                print("  (Empty DataFrame)")
        
        # Convert and print annual data
        if annual:
            print(f"\n[STEP 2.6] collect_balance_sheet_data: ANNUAL Balance Sheet (as DataFrame):")
            annual_df = dict_to_dataframe(annual)
            if not annual_df.empty:
                print(annual_df.to_string())
            else:
                print("  (Empty DataFrame)")
        
        # Convert and print LTM data
        if ltm:
            print(f"\n[STEP 2.7] collect_balance_sheet_data: LTM Balance Sheet (as DataFrame):")
            ltm_df = pd.DataFrame([ltm]).T  # LTM is {metric: value}, convert to single-column DataFrame
            if not ltm_df.empty:
                print(ltm_df.to_string())
            else:
                print("  (Empty DataFrame)")
        
        print(f"\n[STEP 2.8] collect_balance_sheet_data: NOTE: LTM (Last Twelve Months) is a current snapshot that could be quarterly or annual. It is collected but not processed separately.")
        
        result = {
            "quarterly": quarterly,
            "annual": annual,
            "ltm": ltm  # LTM is collected but not processed separately - it's a current snapshot
        }
        
        print(f"[STEP 2.9] collect_balance_sheet_data: Returning result with keys: {list(result.keys())}")
        return result
    except Exception as e:
        print(f"[ERROR] collect_balance_sheet_data: {e}")
        import traceback
        traceback.print_exc()
        return {}


async def collect_cashflow_data(ticker: str) -> Dict[str, Any]:
    """Collect cash flow data (quarterly and annual) from Yahoo Finance."""
    try:
        import pandas as pd
        print(f"[STEP 3.1] collect_cashflow_data: Starting for ticker {ticker}")
        from routers.internal import get_micro_data
        
        print(f"[STEP 3.2] collect_cashflow_data: Calling get_micro_data({ticker})")
        micro_data = await get_micro_data(ticker)
        print(f"[STEP 3.3] collect_cashflow_data: get_micro_data returned, keys: {list(micro_data.keys())}")
        
        print(f"[STEP 3.4] collect_cashflow_data: Extracting cashflow")
        cashflow = micro_data.get('cashflow', {})
        quarterly = cashflow.get('quarterly', {})
        annual = cashflow.get('annual', {})
        ltm = cashflow.get('ltm', {})
        
        # Convert dictionaries to pandas DataFrames and print
        def dict_to_dataframe(data_dict: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
            """Convert {metric: {date: value}} to DataFrame with metrics as rows and dates as columns."""
            if not data_dict:
                return pd.DataFrame()
            
            # Collect all unique dates
            all_dates = set()
            for metric_data in data_dict.values():
                if isinstance(metric_data, dict):
                    all_dates.update(metric_data.keys())
            
            if not all_dates:
                return pd.DataFrame()
            
            # Create DataFrame
            df_data = {}
            for metric, date_values in data_dict.items():
                if isinstance(date_values, dict):
                    df_data[metric] = {date: date_values.get(date) for date in all_dates}
            
            df = pd.DataFrame(df_data).T  # Transpose so metrics are rows, dates are columns
            return df
        
        # Convert and print quarterly data
        if quarterly:
            print(f"\n[STEP 3.5] collect_cashflow_data: QUARTERLY Cash Flow (as DataFrame):")
            quarterly_df = dict_to_dataframe(quarterly)
            if not quarterly_df.empty:
                print(quarterly_df.to_string())
            else:
                print("  (Empty DataFrame)")
        
        # Convert and print annual data
        if annual:
            print(f"\n[STEP 3.6] collect_cashflow_data: ANNUAL Cash Flow (as DataFrame):")
            annual_df = dict_to_dataframe(annual)
            if not annual_df.empty:
                print(annual_df.to_string())
            else:
                print("  (Empty DataFrame)")
        
        # Convert and print LTM data
        if ltm:
            print(f"\n[STEP 3.7] collect_cashflow_data: LTM Cash Flow (as DataFrame):")
            ltm_df = pd.DataFrame([ltm]).T  # LTM is {metric: value}, convert to single-column DataFrame
            if not ltm_df.empty:
                print(ltm_df.to_string())
            else:
                print("  (Empty DataFrame)")
        
        print(f"\n[STEP 3.8] collect_cashflow_data: NOTE: LTM (Last Twelve Months) is a current snapshot that could be quarterly or annual. It is collected but not processed separately.")
        
        result = {
            "quarterly": quarterly,
            "annual": annual,
            "ltm": ltm  # LTM is collected but not processed separately - it's a current snapshot
        }
        
        print(f"[STEP 3.9] collect_cashflow_data: Returning result with keys: {list(result.keys())}")
        return result
    except Exception as e:
        print(f"[ERROR] collect_cashflow_data: {e}")
        import traceback
        traceback.print_exc()
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
