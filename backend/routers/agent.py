from fastapi import APIRouter, HTTPException, Body, Depends
from pydantic import BaseModel
from services.agent import agent_service
from services.edgar_service import edgar_service
from typing import Optional
import openai
import os
from datetime import datetime, timedelta
import hashlib
from routers.auth import get_current_user
import models

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

@router.get("/10k/{ticker}")
async def get_10k_chunks(ticker: str):
    """
    Fetch the latest 10-K filing for a ticker.
    Returns the full 10-K document text without AI processing.
    """
    try:
        full_content = edgar_service.get_latest_10k_full(ticker)
        if not full_content:
            raise HTTPException(
                status_code=404,
                detail=f"Could not fetch 10-K filing for {ticker}. The company may not have filed a 10-K, or there was an error retrieving it."
            )
        return {"content": full_content, "ticker": ticker.upper()}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching 10-K for {ticker}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze_company")
async def analyze_company(
    request: CompanyAnalysisRequest,
    current_user: models.User = Depends(get_current_user)
):
    """
    Generate a comprehensive forensic business analysis based on the latest 10-K filing.
    Uses the latest 10-K from SEC EDGAR and generates a detailed forensic analysis.
    Uses caching to avoid redundant API calls.
    
    Requires user to have paid for Research access.
    """
    # Check if user has paid
    if not hasattr(current_user, 'has_paid') or not current_user.has_paid:
        raise HTTPException(
            status_code=403,
            detail="Payment required. Please verify your payment to access Company Overview & Industry Analysis generation."
        )
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
        
        # Fetch the latest 10-K content from SEC (chunked)
        print(f"Fetching latest 10-K for {request.ticker}...")
        ten_k_chunks = edgar_service.get_latest_10k_content(request.ticker)
        
        if not ten_k_chunks or not isinstance(ten_k_chunks, dict):
            raise HTTPException(
                status_code=404, 
                detail=f"Could not fetch 10-K filing for {request.ticker}. The company may not have filed a 10-K, or there was an error retrieving it."
            )
        
        # Calculate total content length
        total_length = sum(len(chunk) for chunk in ten_k_chunks.values() if chunk)
        print(f"Successfully fetched 10-K chunks (total: {total_length} characters)")
        print(f"Chunks found: {list(ten_k_chunks.keys())}")
        
        # Get current date for context
        current_date = datetime.now()
        current_year = current_date.year
        
        # Build the prompt with chunked content
        chunk_a = ten_k_chunks.get("chunk_a", "Not available")
        chunk_b = ten_k_chunks.get("chunk_b", "Not available")
        chunk_c1 = ten_k_chunks.get("chunk_c1", "Not available")
        chunk_c2 = ten_k_chunks.get("chunk_c2", "Not available")
        chunk_d = ten_k_chunks.get("chunk_d", "Not available")
        chunk_e = ten_k_chunks.get("chunk_e", "Not available")
        
        prompt = f"""
        You are a forensic business analyst and financial strategist.
        Your job is to dissect the company's 10-K with zero mercy and extract insights that matter to investors, operators, and competitors.

        Analyze the 10-K chunks I provide for {request.company_name} ({request.ticker}) in the {request.sector} sector and produce a comprehensive breakdown with the following structure:

        ## 1. Executive Snapshot

        What the company actually does (in one punchy paragraph)

        Its core business model

        Primary revenue streams & cost drivers

        ## 2. Financial Health Check

        Summaries + sharp interpretation:

        Revenue, margins, FCF trends (3–5 year direction)

        Liquidity & leverage analysis

        Cash runway & debt risk

        Any accounting red flags or weird footnotes

        ## 3. Competitive Position

        Core moats (if any)

        Market structure (fragmented? consolidated? growing?)

        Key competitors & differentiators

        Switching costs & barriers to entry

        ## 4. Risks They Didn't Intend to Highlight

        (Read between the lines)
        Identify:

        Hidden operational fragilities

        Dependence on key customers/suppliers

        Lawsuits/regulatory exposure

        Any "dangerous optimism" in management tone

        Risks that are mentioned but downplayed

        ## 5. Strategic Outlook & Catalysts

        Long-term opportunities

        Realistic near-term growth levers

        Technology tailwinds/headwinds

        M&A viability

        Signals of strategic pivots

        ## 6. Quality of Management

        Evaluate based on:

        Transparency (or lack thereof)

        Capital allocation discipline

        KPI alignment

        Compensation incentives

        Insider holdings & behavior (if disclosed)

        ## 7. Valuation Considerations (If Enough Data Available)

        What metrics the market should use

        Whether current fundamentals support potential multiples

        Whether business model deserves premium/discount

        ## 8. "If I Were the CEO" — Actionable Recommendations

        Give 3–5 bold, pragmatic moves that would most improve:

        Growth

        Efficiency

        Cash generation

        Competitive resilience

        ## 9. Final Verdict

        Summarize in one line:
        "This is a (great / average / risky / doomed) business because…"

        **Tone & Style Requirements:**

        Be direct and analytical

        Use numbers wherever possible

        Call out BS, hype, or soft language

        Highlight contradictions in the filing

        Provide insights, not summaries

        **10-K Content Chunks:**
        (Today's date: {current_date.strftime('%B %d, %Y')})

        === CHUNK A: Item 1. Business ===
        {chunk_a}

        === CHUNK B: Item 1A. Risk Factors ===
        {chunk_b}

        === CHUNK C1: Item 7. MD&A ===
        {chunk_c1}

        === CHUNK C2: Item 7A. Market Risk ===
        {chunk_c2}

        === CHUNK D: Item 8. Financial Statements ===
        {chunk_d}

        === CHUNK E: Items 10, 11, 12, 13 (Governance, Compensation, Ownership) ===
        {chunk_e}
        """

        system_message = """You are a forensic business analyst and financial strategist.
Your job is to dissect company 10-K filings with zero mercy and extract insights that matter to investors, operators, and competitors.

You are direct and analytical. You use numbers wherever possible. You call out BS, hype, or soft language. You highlight contradictions in filings. You provide insights, not summaries.

Today's date is {current_date}. Base your analysis strictly on the 10-K content provided. Be specific, use concrete examples from the filing, and avoid generic statements.""".format(current_date=current_date.strftime('%B %d, %Y'))

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )

        report_content = response.choices[0].message.content
        
        # Cache the result
        set_cached_analysis(request.ticker, "company_overview", report_content)
        
        return {"report": report_content, "cached": False}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in analyze_company: {e}")
        import traceback
        traceback.print_exc()
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
    Generate comprehensive cash flow analysis based on financial statements.
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
        
        # Fetch company financial data to include cash flow statements
        cashflow_data = ""
        try:
            import requests
            import json
            micro_response = requests.get(f"http://localhost:8000/api/internal/micro/{request.ticker}", timeout=10)
            if micro_response.status_code == 200:
                micro_data = micro_response.json()
                cashflow_quarterly = micro_data.get("cashflow", {}).get("quarterly", {})
                if cashflow_quarterly:
                    cashflow_data = f"\n\n## Raw Cash Flow Data (Quarterly)\n\n```json\n{json.dumps(cashflow_quarterly, indent=2, default=str)}\n```\n\nAnalyze this quarterly cash flow statement data in detail.\n\n"
        except Exception as e:
            print(f"Warning: Could not fetch cash flow data: {e}")
            cashflow_data = f"\n\n**Note:** Cash flow data could not be retrieved automatically. Please analyze based on available information, latest 10-Q and 10-K filings from SEC EDGAR, and general sector knowledge. Focus on the cash flow statement structure and typical patterns for {request.sector} companies.\n\n"
        
        prompt = f"""
        You are an elite Financial Analyst AI whose sole job is to produce a complete, professional financial analysis report based on the raw financial data provided for {request.company_name} ({request.ticker}) in the {request.sector} sector.

        When provided with numbers (even if messy, incomplete, or unformatted), you must transform them into a polished, structured report with deep analysis, insights, and interpretation.

        {cashflow_data}

        Your reports must always include the following sections:

        ## 1. Executive Summary
        - A concise but powerful overview of what's happening in the business
        - Identify key trends, strengths, risks, and the one big takeaway a CFO or investor must understand.

        ## 2. Operating Cash Flow Analysis
        - For every OCF line item provided, explain what it means, interpret the numbers, and explain the logic behind its movements.
        - Identify operational drivers, working capital behavior, and quality of cash flow.
        - Use tables when helpful.

        ## 3. Investing Cash Flow Analysis
        - Break down CapEx, PPE purchases/sales, acquisitions, and all other investing items.
        - Explain whether investment levels are sustainable and what phase the business is in (growth, maintenance, expansion).
        - Highlight major drains or strategic investments.

        ## 4. Financing Cash Flow Analysis
        - Analyze debt issuance/repayment, equity issuance/buybacks, dividends, and other financing flows.
        - Interpret the company's capital allocation strategy and leverage levels.
        - Identify financial risks, liquidity exposure, and sustainability of financing behavior.

        ## 5. Free Cash Flow & Liquidity Assessment
        - Explain FCF trends, cash burn or generation, liquidity position, and runway.
        - Identify whether the company can self-fund growth or relies heavily on external capital.
        - Flag interest burden issues or cash cycle risks.

        ## 6. Integrated Interpretation (The Real Story)
        - Synthesize all three cash flow sections into one narrative.
        - Explain the true economic story: what type of business this is, what's driving performance, what's improving, what's deteriorating, and what outsiders might miss.
        - This section should be bold, insightful, and strategic.

        ## 7. Forward-Looking Considerations
        - Provide forward-looking insights: risks, opportunities, strategic concerns, potential inflection points, and what will happen if current trends continue.
        - This is not forecasting; it is high-level strategic foresight.

        ## 8. Appendix (Optional)
        - Include tables, reconstructed metrics, ratios, and line-item summaries if helpful.

        **Tone Requirements:**
        - Direct, practical, sharp, and intelligent.
        - Occasional clever humor is encouraged.
        - Absolutely no fluff or generic textbook explanations.
        - Speak with the confidence of a senior financial analyst presenting to a board of directors.
        - Always tell the truth bluntly — never sugar-coat.

        **Data Handling Rules:**
        - Parse messy or incomplete data without complaint.
        - If something is missing, analyze what is available.
        - Never simply restate the numbers — always extract meaning.
        - Always deliver insights, reasoning, and implications, not just calculations.

        Your ultimate mission is to transform raw numbers from cash flow Statement (Quarterly) in Financial Statements of Company Basic into real understanding and produce a polished, high-impact financial analysis report every time.
        """

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an elite Financial Analyst AI whose sole job is to produce complete, professional financial analysis reports. You transform raw financial data into polished, structured reports with deep analysis, insights, and interpretation. You are direct, practical, sharp, and intelligent. You speak with the confidence of a senior financial analyst presenting to a board of directors. You always tell the truth bluntly and never sugar-coat. You never simply restate numbers—you always extract meaning and deliver insights, reasoning, and implications."},
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
