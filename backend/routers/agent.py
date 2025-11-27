from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from services.agent import agent_service
from typing import Optional
import openai
import os
from datetime import datetime, timedelta
import hashlib

router = APIRouter()

# Initialize OpenAI client lazily
_client = None

def get_openai_client():
    """Get OpenAI client, initializing it if needed."""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set. Please configure it in your .env file.")
        _client = openai.OpenAI(api_key=api_key)
    return _client

# In-memory cache for AI analyses
# Structure: {cache_key: {"report": str, "timestamp": datetime}}
analysis_cache = {}
CACHE_TTL_HOURS = 24  # Cache expires after 24 hours

def get_cache_key(ticker: str, analysis_type: str) -> str:
    """Generate a unique cache key for a ticker and analysis type."""
    return f"{ticker.upper()}_{analysis_type}"

def get_cached_analysis(ticker: str, analysis_type: str) -> Optional[str]:
    """Retrieve cached analysis if it exists and is not expired."""
    cache_key = get_cache_key(ticker, analysis_type)
    if cache_key in analysis_cache:
        cached_data = analysis_cache[cache_key]
        # Check if cache is still valid
        if datetime.now() - cached_data["timestamp"] < timedelta(hours=CACHE_TTL_HOURS):
            return cached_data["report"]
        else:
            # Remove expired cache
            del analysis_cache[cache_key]
    return None

def set_cached_analysis(ticker: str, analysis_type: str, report: str):
    """Store analysis in cache with current timestamp."""
    cache_key = get_cache_key(ticker, analysis_type)
    analysis_cache[cache_key] = {
        "report": report,
        "timestamp": datetime.now()
    }

def clear_cache_for_ticker(ticker: str):
    """Clear all cached analyses for a specific ticker."""
    keys_to_delete = [key for key in analysis_cache.keys() if key.startswith(ticker.upper())]
    for key in keys_to_delete:
        del analysis_cache[key]

class ReportRequest(BaseModel):
    data_context: str
    prompt_customization: Optional[str] = ""

class CompanyAnalysisRequest(BaseModel):
    ticker: str
    company_name: str
    sector: str

@router.post("/generate_report")
async def generate_report(request: ReportRequest):
    """
    Generate a report using the AI agent.
    """
    try:
        report = agent_service.generate_report(request.data_context, request.prompt_customization)
        return {"report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze_company")
async def analyze_company(request: CompanyAnalysisRequest):
    """
    Generate a comprehensive deep dive analysis for a company.
    Covers: Industry, Business Model, Operating Drivers, Risks, Capital Structure.
    Uses caching to avoid redundant API calls.
    """
    try:
        # Check cache first
        cached_report = get_cached_analysis(request.ticker, "company_overview")
        if cached_report:
            return {"report": cached_report, "cached": True}
        
        # Ensure API key is available
        try:
            client = get_openai_client()
        except ValueError as e:
            raise HTTPException(status_code=503, detail=str(e))
        
        # Get current date for context
        current_date = datetime.now()
        current_year = current_date.year
        current_month = current_date.month
        current_quarter = (current_month - 1) // 3 + 1
        
        prompt = f"""
        Perform a comprehensive Micro Economic Deep Dive analysis for {request.company_name} ({request.ticker}) in the {request.sector} sector.
        
        CRITICAL REQUIREMENTS:
        1. **USE LATEST SEC FILINGS**: You MUST base your analysis on the most recent 10-Q (quarterly) and 10-K (annual) filings available from SEC EDGAR. Do NOT use outdated information or historical data from previous years unless explicitly comparing to current period.
        2. **CURRENT DATE CONTEXT**: Today's date is {current_date.strftime('%B %d, %Y')} (Year: {current_year}, Quarter: Q{current_quarter}). All timelines, milestones, and dates in your analysis must reflect this current date. Do NOT reference past years (e.g., 2023-2024) as if they are current or future targets.
        3. **DATE ACCURACY**: When listing milestones, targets, or timelines, ensure they are forward-looking from {current_year}. If a company mentioned targets for 2023-2024 in old filings, note that these are historical and update with current expectations from the latest filings.
        4. **Be SPECIFIC and ACTIONABLE**: Avoid generic statements. Focus on concrete risks, opportunities, and catalysts unique to this company based on the latest available information.
        
        Structure the response in Markdown with the following sections:

        ## 1. Industry Research & Competitive Position
        - Current state of the {request.sector} industry and key trends (as of {current_year})
        - {request.company_name}'s competitive positioning and market share (based on latest 10-Q/10-K)
        - Key competitors and differentiation factors
        - Industry tailwinds and headwinds

        ## 2. Business Model & Revenue Streams
        - Brief company history and evolution
        - Core business model (how they make money) - use latest financial data from most recent 10-Q/10-K
        - Revenue breakdown by segment/product/geography (if applicable) - from latest filings
        - Major customers and suppliers (if publicly known) - from latest 10-K
        - Customer concentration risks - from latest 10-K

        ## 3. Key Investment Thesis
        **Bull Case (Upside Scenarios)**:
        - Identify 3-5 SPECIFIC catalysts that could drive significant upside
        - For each catalyst: describe the opportunity, probability, timeline (must be future dates from {current_year}), and potential impact
        - Base catalysts on information from the latest 10-Q/10-K filings
        - Example: "If NRC licensing milestones are achieved by Q2 {current_year + 1}, could unlock $XXX revenue potential" (NOT 2023-2024)
        
        **Bear Case (Downside Risks)**:
        - Identify 3-5 SPECIFIC risks that could significantly impair value
        - For each risk: describe the threat, probability, timeline, and potential impact
        - Include regulatory, operational, financial, and market risks from latest 10-Q/10-K
        
        **Base Case**:
        - Most likely scenario given current information from latest filings
        - Key assumptions and what to monitor

        ## 4. Critical Milestones to Monitor
        - List 5-7 specific events/metrics to track (e.g., regulatory approvals, product launches, financial metrics)
        - For each milestone: why it matters and expected timeline (MUST be future dates from {current_year}, not past years)
        - Base milestones on the latest 10-Q/10-K filings and management guidance
        - IMPORTANT: If old filings mentioned 2023-2024 targets, note these are historical and provide current expectations

        ## 5. Valuation Context
        - Current valuation metrics vs. peers (if applicable) - use latest financial data
        - What the market is pricing in
        - Key valuation drivers

        Keep the analysis professional, data-driven, and actionable (approx. 800-1000 words).
        Focus on what makes THIS company unique, not generic industry commentary.
        REMEMBER: Always reference the most recent 10-Q and 10-K filings, and ensure all dates and timelines are current and forward-looking from {current_year}.
        """

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"You are a senior equity research analyst at a top-tier investment bank. Today's date is {current_date.strftime('%B %d, %Y')}. You MUST base your analysis on the most recent 10-Q and 10-K SEC filings available. Do NOT use outdated information. All timelines and milestones must be forward-looking from {current_year}. If you see references to past years (e.g., 2023-2024 targets), note they are historical and provide current expectations. Provide specific, actionable analysis with concrete examples. Avoid generic statements. Focus on unique company-specific risks and opportunities based on the latest available data."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )

        report_content = response.choices[0].message.content
        
        # Cache the result
        set_cached_analysis(request.ticker, "company_overview", report_content)
        
        return {"report": report_content, "cached": False}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze_operating_drivers")
async def analyze_operating_drivers(request: CompanyAnalysisRequest):
    """
    Generate sector-specific operating drivers analysis.
    Uses caching to avoid redundant API calls.
    """
    try:
        # Check cache first
        cached_report = get_cached_analysis(request.ticker, "operating_drivers")
        if cached_report:
            return {"report": cached_report, "cached": True}
        
        # Ensure API key is available
        try:
            client = get_openai_client()
        except ValueError as e:
            raise HTTPException(status_code=503, detail=str(e))
        
        prompt = f"""
        Analyze the Operating Drivers for {request.company_name} ({request.ticker}) in the {request.sector} sector.
        
        IMPORTANT: Be SPECIFIC. Provide concrete metrics, benchmarks, and actionable insights.
        
        Provide a detailed analysis in Markdown format covering:

        ## Operating Drivers Analysis

        ### Sector-Specific Metrics & KPIs
        Based on the {request.sector} sector, identify the MOST CRITICAL metrics for {request.company_name}:
        - For SaaS/Tech: ARPU, CAC, LTV, Churn Rate, Net Dollar Retention, Magic Number
        - For Retail: Comp sales, Store productivity, Inventory turns, Conversion rates
        - For Manufacturing: Capacity utilization, Yield rates, Unit costs, Order backlog
        - For Energy: Production volumes, Realized prices, Operating costs per unit, Reserve life
        - For Biotech/Healthcare: Pipeline progress, Clinical trial milestones, Regulatory timelines
        
        **For each key metric**:
        - Current performance level (if known)
        - Industry benchmarks
        - What would indicate strong vs. weak performance
        - How to track this metric (earnings calls, filings, etc.)

        ### Volume vs. Price Dynamics
        - What drives revenue growth: volume increases or pricing power?
        - Historical pricing trends in this sector
        - Competitive dynamics affecting pricing
        - Volume growth drivers and constraints

        ### Operational Leverage & Scalability
        - Fixed vs. variable cost structure
        - Operating leverage potential
        - Scalability constraints (capacity, supply chain, talent, etc.)
        - Marginal unit economics

        ### Critical Success Factors
        - What are the 3-5 operational metrics that matter most for this business?
        - What operational improvements would have the biggest impact?
        - Key operational risks to monitor

        ### Competitive Benchmarking
        - How does {request.company_name} compare to peers on key operating metrics?
        - Where do they have operational advantages/disadvantages?

        Keep the analysis data-driven and actionable (approx. 600-800 words).
        Focus on metrics investors should track quarter-to-quarter.
        """

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a senior operating metrics analyst and former CFO. Provide specific, quantitative analysis. Always include benchmarks and concrete metrics."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )

        report_content = response.choices[0].message.content
        
        # Cache the result
        set_cached_analysis(request.ticker, "operating_drivers", report_content)
        
        return {"report": report_content, "cached": False}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze_notes_disclosures")
async def analyze_notes_disclosures(request: CompanyAnalysisRequest):
    """
    Generate analysis of accounting policies, segment reporting, and risk factors.
    Uses caching to avoid redundant API calls.
    """
    try:
        # Check cache first
        cached_report = get_cached_analysis(request.ticker, "notes_disclosures")
        if cached_report:
            return {"report": cached_report, "cached": True}
        
        # Ensure API key is available
        try:
            client = get_openai_client()
        except ValueError as e:
            raise HTTPException(status_code=503, detail=str(e))
        
        prompt = f"""
        Analyze the Notes & Disclosures for {request.company_name} ({request.ticker}) in the {request.sector} sector.
        
        IMPORTANT: Focus on RED FLAGS and what to watch for in financial disclosures.
        
        Provide analysis in Markdown format covering:

        ## Notes & Disclosures Analysis

        ### Critical Accounting Policies
        - Revenue recognition methods typical for {request.sector} companies
        - What aggressive vs. conservative revenue recognition looks like
        - Depreciation/amortization policies and useful life assumptions
        - Inventory valuation (FIFO vs. LIFO) and potential impacts
        - **Red flags to watch**: Changes in accounting policies, unusual adjustments

        ### Segment Reporting
        - Expected business segments for {request.sector} companies
        - Geographic vs. product line segmentation
        - **What to analyze**: Segment profitability trends, cross-subsidization, growth rates by segment
        - **Red flags**: Declining margins in core segments, lack of disclosure

        ### Off-Balance Sheet Items & Commitments
        - Common off-balance sheet arrangements in {request.sector}
        - Operating leases and future commitments
        - Purchase obligations and take-or-pay contracts
        - **Red flags**: Large undisclosed liabilities, complex SPE structures

        ### Contingencies & Legal Risks
        - Industry-specific regulatory risks for {request.sector}
        - Common litigation areas and exposure
        - Environmental liabilities (if applicable)
        - **What to monitor**: Changes in legal reserves, new regulatory developments
        - **Specific risks for {request.company_name}**: [Identify company-specific risks]

        ### Stock-Based Compensation
        - Typical SBC as % of revenue for {request.sector}
        - Impact on dilution and true profitability
        - **Red flags**: Excessive SBC, frequent option repricing

        ### Customer & Supplier Concentration
        - Typical customer concentration in {request.sector}
        - **Concerning thresholds**: >10% from single customer, >30% from top 3
        - Supplier dependency risks
        - **What to watch**: Customer churn, contract renewals

        ### Quality of Earnings Indicators
        - Cash flow vs. earnings quality
        - Working capital trends
        - One-time items and adjustments
        - **Red flags**: Persistent gap between GAAP and non-GAAP, declining cash conversion

        Keep the analysis practical and focused on what investors should monitor (approx. 700-900 words).
        Emphasize RED FLAGS and warning signs specific to this company/sector.
        """

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a forensic accounting analyst and former SEC examiner. Focus on identifying red flags, accounting risks, and disclosure quality issues."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )

        report_content = response.choices[0].message.content
        
        # Cache the result
        set_cached_analysis(request.ticker, "notes_disclosures", report_content)
        
        return {"report": report_content, "cached": False}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze_capital_structure")
async def analyze_capital_structure(request: CompanyAnalysisRequest):
    """
    Generate detailed capital structure and financing analysis.
    Uses caching to avoid redundant API calls.
    """
    try:
        # Check cache first
        cached_report = get_cached_analysis(request.ticker, "capital_structure")
        if cached_report:
            return {"report": cached_report, "cached": True}
        
        # Ensure API key is available
        try:
            client = get_openai_client()
        except ValueError as e:
            raise HTTPException(status_code=503, detail=str(e))
        
        prompt = f"""
        Analyze the Capital Structure & Financing for {request.company_name} ({request.ticker}) in the {request.sector} sector.
        
        IMPORTANT: Focus on FINANCIAL FLEXIBILITY and RISK. Be specific about debt levels, covenants, and runway.
        
        Provide analysis in Markdown format covering:

        ## Capital Structure & Financing Analysis

        ### Current Debt Profile
        - Typical leverage ratios for {request.sector} companies (Debt/EBITDA benchmarks)
        - Expected debt maturity profile and refinancing risks
        - Interest rate exposure (fixed vs. floating)
        - **Key questions**: Is the company over/under-leveraged? Refinancing risks in next 12-24 months?

        ### Debt Covenants & Restrictions
        - Common covenant structures in {request.sector}
        - Typical maintenance covenants (leverage, coverage ratios)
        - **Red flags**: Covenant headroom <20%, frequent amendments, PIK toggle features
        - Restrictions on dividends, capex, M&A

        ### Liquidity & Financial Runway
        - Cash burn rate analysis (if applicable)
        - Liquidity sources: cash, revolver availability, FCF generation
        - **Critical question**: How many quarters of runway at current burn rate?
        - Funding needs for growth/operations
        - **Warning signs**: Declining cash, increasing payables, asset sales

        ### Equity Financing History
        - Recent equity issuances and dilution
        - Valuation at which equity was raised
        - Convertible securities and potential dilution
        - **Red flags**: Frequent dilutive raises, down rounds, PIPE deals

        ### Capital Allocation Strategy
        - Historical capital allocation: growth capex vs. maintenance capex vs. returns to shareholders
        - Typical capital intensity for {request.sector}
        - M&A strategy and track record
        - **What to evaluate**: ROIC on deployed capital, capital discipline

        ### Dividends & Buybacks
        - Dividend policy norms for {request.sector} (payout ratios)
        - Sustainability of current dividend (coverage ratios)
        - Buyback programs: opportunistic vs. systematic
        - **Red flags**: Cutting dividends, borrowing to fund buybacks

        ### Credit Profile & Market Access
        - Credit ratings and outlook (if rated)
        - Access to capital markets (investment grade vs. high yield vs. private)
        - Cost of capital trends
        - **Key question**: Can the company access capital if needed?

        ### Financing Risks & Opportunities
        - **Risks**: Refinancing wall, covenant breach risk, dilution risk
        - **Opportunities**: Deleveraging path, refinancing at lower rates, strategic M&A
        - Scenarios: What if interest rates rise? What if FCF disappoints?

        Keep the analysis strategic and forward-looking (approx. 800-1000 words).
        Focus on financial flexibility, runway, and risk management.
        """

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a senior credit analyst and former leveraged finance banker. Focus on financial risk, covenant analysis, and capital structure optimization."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )

        report_content = response.choices[0].message.content
        
        # Cache the result
        set_cached_analysis(request.ticker, "capital_structure", report_content)
        
        return {"report": report_content, "cached": False}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/clear_cache/{ticker}")
async def clear_analysis_cache(ticker: str):
    """
    Clear all cached analyses for a specific ticker.
    Useful when you want to force regeneration of analyses.
    """
    try:
        clear_cache_for_ticker(ticker)
        return {"message": f"Cache cleared for {ticker.upper()}", "ticker": ticker.upper()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cache_status/{ticker}")
async def get_cache_status(ticker: str):
    """
    Get cache status for all analysis types for a ticker.
    """
    try:
        analysis_types = ["company_overview", "operating_drivers", "notes_disclosures", "capital_structure"]
        status = {}
        
        for analysis_type in analysis_types:
            cache_key = get_cache_key(ticker, analysis_type)
            if cache_key in analysis_cache:
                cached_data = analysis_cache[cache_key]
                age = datetime.now() - cached_data["timestamp"]
                is_valid = age < timedelta(hours=CACHE_TTL_HOURS)
                status[analysis_type] = {
                    "cached": True,
                    "age_hours": age.total_seconds() / 3600,
                    "valid": is_valid
                }
            else:
                status[analysis_type] = {"cached": False}
        
        return {"ticker": ticker.upper(), "cache_status": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
