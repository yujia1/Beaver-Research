"""
Research Engine Service
Handles agent-based data interpretation using AI
Separated from router logic for better maintainability and scalability.
"""
from typing import Dict, Any, Optional
import openai
import os
import hashlib
import json
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Updated Agent Definitions
COMPANY_AGENTS = {
    "FUNDAMENTAL_AGENT": {
        "name": "Fundamental Agent",
        "focus": "Core Fundamentals (Comprehensive Financial Statements)",
        "sub_agents": {},
        "tone": "Direct, sharp, practical, and unsentimental"
    },
    "TRADING_AGENT": {
        "name": "Trading Agent",
        "focus": "Trading Data (Options, Insider Trading)",
        "sub_agents": {
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

class ResearchEngine:
    """
    Engine to handle data interpretation using OpenAI agents.
    """
    
    def __init__(self):
        self.client = self._get_openai_client()

    def _get_openai_client(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        return openai.OpenAI(api_key=api_key)

    def determine_sub_agent(self, agent_config: Dict, bubble_type: str) -> tuple:
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

    def clean_json_response(self, content: str) -> str:
        """
        Clean and extract JSON from AI response.
        Handles markdown code blocks, unclosed strings, and other common issues.
        Uses proper brace matching to find the complete outermost JSON object.
        """
        if not content:
            return ""
        
        content = content.strip()
        print(f"[CLEAN JSON] Starting cleanup. Original length: {len(content)}")
        
        # Remove markdown code blocks
        if "```" in content:
            print(f"[CLEAN JSON] Found markdown code blocks, extracting JSON...")
            parts = content.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("json"):
                    content = part[4:].strip()
                    break
                elif part.startswith("{"):
                    content = part.strip()
                    break
        
        # Find the first opening brace
        first_brace = content.find("{")
        if first_brace < 0:
            print(f"[CLEAN JSON] WARNING: No opening brace found!")
            return ""
        
        # Use simple stack for brace matching
        stack = []
        last_brace = -1
        in_string = False
        escape = False
        
        for i, char in enumerate(content[first_brace:], start=first_brace):
            if escape:
                escape = False
                continue
            
            if char == '\\':
                escape = True
                continue
            
            if char == '"' and not escape:
                in_string = not in_string
                continue
                
            if not in_string:
                if char == '{':
                    stack.append(i)
                elif char == '}':
                    if stack:
                        stack.pop()
                        if not stack:
                            last_brace = i
                            break
                            
        if last_brace != -1:
            content = content[first_brace:last_brace+1]
        else:
             # Fallback: find last closing brace
            last_brace = content.rfind("}")
            if last_brace > first_brace:
                content = content[first_brace:last_brace+1]
        
        # Cleanup
        content = re.sub(r',\s*}', '}', content)
        content = re.sub(r',\s*]', ']', content)
        
        return content

    def build_agent_system_message(self, sub_agent_key: str, agent_config: Dict, sub_agent_name: str) -> str:
        """Route to agent-specific system message builder."""
        # For brevity, reusing the generic fallback mostly, or specific ones if critical
        # Importing specific builders here would be ideal, or defining them as methods
        
        # Simplified for clarity - in full implementation, all specific builders from research.py should be moved here
        base_message = f"""You are a {sub_agent_name} (specialized {agent_config['name']}) specializing in {agent_config['focus']}.
Your tone is {agent_config['tone']}.
You must output structured markdown with:
1. A markdown table summarizing key metrics
2. A comprehensive analysis paragraph (200-300 words)
3. 5-10 bullet points with critical insights
Always be precise, professional, and actionable."""

        return base_message

    def build_agent_interpretation_prompt(self, sub_agent_key: str, raw_data: Any, agent_config: Dict, sub_agent_name: str, ticker: Optional[str], context: str, bubble: Dict) -> str:
        """Build the analysis prompt."""
        data_str = str(raw_data)[:15000] # Truncate to avoid context limits
        
        return f"""
Analyze the following data for {ticker if ticker else 'the market'}:

DATA:
{data_str}

CONTEXT:
{context}

BUBBLE CONTEXT:
{str(bubble)}

Provide a detailed {sub_agent_name} analysis following your system instructions.
"""

    async def process_data(self, agent_id: str, view_mode: str, ticker: str, bubble: Dict, context: str, collect_data_fn) -> Dict:
        """
        Main processing method.
        """
        print(f"[ENGINE] Processing for {agent_id} ({view_mode})")
        
        agent_config = None
        if view_mode == "COMPANY":
            agent_config = COMPANY_AGENTS.get(agent_id)
        else:
            agent_config = MARKET_AGENTS.get(agent_id)
        
        if not agent_config:
            raise ValueError(f"Unknown agent: {agent_id}")
            
        bubble_type = bubble.get("type", "")
        sub_agent_key, sub_agent_name = self.determine_sub_agent(agent_config, bubble_type)
        
        # Collect data
        # We pass the collection function to decouple data fetching from analysis logic
        raw_data = await collect_data_fn(agent_id, sub_agent_key, ticker)
        
        if not raw_data:
             raise ValueError(f"No data available for {sub_agent_key}")
             
        # Build messages
        system_msg = self.build_agent_system_message(sub_agent_key, agent_config, sub_agent_name)
        user_msg = self.build_agent_interpretation_prompt(sub_agent_key, raw_data, agent_config, sub_agent_name, ticker, context, bubble)
        
        # Call AI
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        insight = response.choices[0].message.content
        
        return {
            "insight": insight,
            "agent": agent_id,
            "sub_agent": sub_agent_name,
            "sub_agent_key": sub_agent_key
        }

