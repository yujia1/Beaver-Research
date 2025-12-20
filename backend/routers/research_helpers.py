from typing import Dict, Any, Optional
import json

def build_fundamental_agent_system_message(agent_config: Dict[str, Any], agent_name: str) -> str:
    """Build system message for fundamental agent."""
    return f"""You are {agent_name}, a financial analysis expert specializing in fundamental analysis.

Your role is to analyze financial data and provide clear, actionable insights for investors.

Focus on:
- Financial health and performance metrics
- Trends and patterns in the data
- Strengths and potential risks
- Investment implications

Provide structured, professional analysis that is easy to understand."""

def build_fundamental_agent_interpretation_prompt(
    data: Dict[str, Any],
    agent_config: Dict[str, Any],
    agent_name: str,
    ticker: str,
    context: str,
    additional_context: Optional[str] = None
) -> str:
    """Build a prompt for fundamental agent interpretation."""
    prompt = f"""Analyze the following financial data for {ticker}.

Context: {context}

Financial Data:
{json.dumps(data, indent=2)}

Please provide a comprehensive analysis including:
1. Key financial metrics and their significance
2. Trends and patterns observed
3. Strengths and weaknesses
4. Investment implications

Format your response with clear sections and bullet points where appropriate."""

    if additional_context:
        prompt += f"\n\nAdditional Context: {additional_context}"
    
    return prompt
