"""
Screener Calculator Service

Calculates all screening metrics and trends from financial statement data.
Implements the 4 screening strategies:
1. Cash Flow Sustainability
2. Balance Sheet Stress and Leverage
3. Working Capital Anomalies
4. Valuation Dislocation
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import statistics

logger = logging.getLogger(__name__)

# Import peer comparison service (lazy import to avoid circular dependencies)
try:
    from services.market.peer_comparison import (
        fetch_stock_peers,
        compare_capitalized_costs_to_peers,
        compare_dso_to_peers,
        compare_ev_ebitda_to_peers
    )
    PEER_COMPARISON_AVAILABLE = True
except ImportError:
    logger.warning("Peer comparison service not available")
    PEER_COMPARISON_AVAILABLE = False


@dataclass
class TrendResult:
    """Result of trend analysis"""
    values: List[float]  # Historical values (oldest to newest)
    years: List[int]  # Fiscal years
    slope: float  # Linear regression slope
    direction: str  # "improving", "declining", "stable"
    latest_value: float  # Most recent value


@dataclass
class MetricResult:
    """Result of a single metric calculation"""
    name: str
    latest_value: Optional[float]
    trend: Optional[TrendResult]
    is_red_flag: bool
    red_flag_reason: Optional[str]
    component_values: Optional[Dict[str, float]] = None  # For storing underlying values (e.g., FCF, Revenue)


@dataclass
class CashFlowYearData:
    """Yearly cash flow data for detailed table"""
    year: int
    fcf: float
    dividends_buybacks: float
    revenue: float
    fcf_to_dividends_buybacks: Optional[float]
    fcf_to_revenue: Optional[float]
    is_red_flag: bool
    red_flag_reason: Optional[str]
@dataclass
class BalanceSheetYearData:
    """Yearly balance sheet data for detailed table"""
    year: int
    net_debt: float
    ebitda: float
    capitalized_costs: float
    revenue: float
    net_debt_to_ebitda: Optional[float]
    capitalized_costs_to_revenue: Optional[float]
    is_red_flag: bool
    red_flag_reason: Optional[str]

@dataclass
class WorkingCapitalYearData:
    """Yearly working capital data for detailed table"""
    year: int
    dso: float
    receivables: float
    revenue: float
    ar_growth: Optional[float]
    revenue_growth: Optional[float]
    is_red_flag: bool
    red_flag_reason: Optional[str]

@dataclass
class ValuationYearData:
    """Yearly valuation data for detailed table"""
    year: int
    ev_to_revenue: Optional[float]
    ev_to_ebitda: Optional[float]
    enterprise_value: float
    revenue: float
    ebitda: float
    is_red_flag: bool
    red_flag_reason: Optional[str]


# ============================================================================
# Helper Functions
# ============================================================================

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is 0"""
    if denominator == 0 or denominator is None:
        return default
    return numerator / denominator


def calculate_linear_regression(x: List[float], y: List[float]) -> float:
    """
    Calculate slope of linear regression line
    
    Args:
        x: Independent variable (e.g., years as 0, 1, 2, 3, 4)
        y: Dependent variable (e.g., metric values)
    
    Returns:
        Slope of the regression line
    """
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    
    n = len(x)
    x_mean = statistics.mean(x)
    y_mean = statistics.mean(y)
    
    numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
    
    if denominator == 0:
        return 0.0
    
    return numerator / denominator


def analyze_trend(values: List[float], years: List[int]) -> TrendResult:
    """
    Analyze trend of metric values over time
    
    Args:
        values: Metric values (oldest to newest)
        years: Fiscal years corresponding to values
    
    Returns:
        TrendResult with slope and direction
    """
    if not values or len(values) < 2:
        return TrendResult(
            values=values,
            years=years,
            slope=0.0,
            direction="insufficient_data",
            latest_value=values[-1] if values else 0.0
        )
    
    # Use index as x-axis (0, 1, 2, 3, 4)
    x = list(range(len(values)))
    slope = calculate_linear_regression(x, values)
    
    # Determine direction based on slope
    if abs(slope) < 0.01:  # Threshold for "stable"
        direction = "stable"
    elif slope > 0:
        direction = "improving"
    else:
        direction = "declining"
    
    return TrendResult(
        values=values,
        years=years,
        slope=slope,
        direction=direction,
        latest_value=values[-1]
    )


# ============================================================================
# 1. Cash Flow Sustainability Metrics
# ============================================================================

def calculate_fcf_to_dividends_buybacks_ratio(
    cash_flow_data: List[Dict]
) -> MetricResult:
    """
    Calculate FCF / (Dividends + Buybacks) ratio with 5-year trend
    
    Red Flag: Ratio < 100% (1.0)
    """
    values = []
    years = []
    latest_fcf = None
    latest_dividends_buybacks = None
    
    for statement in reversed(cash_flow_data):  # Oldest to newest
        fcf = statement.get("freeCashFlow", 0) or 0
        dividends_paid = abs(statement.get("dividendsPaid", 0) or 0)
        buybacks = abs(statement.get("commonStockRepurchased", 0) or 0)
        
        total_returns = dividends_paid + buybacks
        
        if total_returns > 0:
            ratio = fcf / total_returns
            values.append(ratio)
            years.append(statement.get("calendarYear") or statement.get("date", "")[:4])
            # Store latest values
            latest_fcf = fcf
            latest_dividends_buybacks = total_returns
    
    if not values:
        return MetricResult(
            name="FCF to Dividends/Buybacks",
            latest_value=None,
            trend=None,
            is_red_flag=False,
            red_flag_reason=None,
            component_values=None
        )
    
    trend = analyze_trend(values, years)
    latest_value = trend.latest_value
    
    # Red flag if latest value < 1.0 (100%)
    is_red_flag = latest_value < 1.0
    red_flag_reason = f"FCF/Dividends+Buybacks = {latest_value:.2f} < 1.0" if is_red_flag else None
    
    return MetricResult(
        name="FCF to Dividends/Buybacks",
        latest_value=latest_value,
        trend=trend,
        is_red_flag=is_red_flag,
        red_flag_reason=red_flag_reason,
        component_values={
            "fcf": latest_fcf,
            "dividends_buybacks": latest_dividends_buybacks
        }
    )


def calculate_fcf_to_revenue_ratio(
    cash_flow_data: List[Dict],
    income_data: List[Dict]
) -> MetricResult:
    """
    Calculate FCF / Revenue ratio with 5-year trend
    
    Red Flag: Declining trend or persistent negativity despite revenue growth
    """
    values = []
    years = []
    latest_fcf = None
    latest_revenue = None
    
    # Match cash flow and income statements by year
    for cf_statement in reversed(cash_flow_data):
        year = cf_statement.get("calendarYear") or cf_statement.get("date", "")[:4]
        
        # Find matching income statement
        income_statement = next(
            (inc for inc in income_data if (inc.get("calendarYear") or inc.get("date", "")[:4]) == year),
            None
        )
        
        if income_statement:
            fcf = cf_statement.get("freeCashFlow", 0) or 0
            revenue = income_statement.get("revenue", 0) or 0
            
            if revenue > 0:
                ratio = fcf / revenue
                values.append(ratio)
                years.append(year)
                # Store latest values
                latest_fcf = fcf
                latest_revenue = revenue
    
    if not values:
        return MetricResult(
            name="FCF to Revenue",
            latest_value=None,
            trend=None,
            is_red_flag=False,
            red_flag_reason=None,
            component_values=None
        )
    
    trend = analyze_trend(values, years)
    latest_value = trend.latest_value
    
    # Red flag if declining trend or persistent negativity
    is_red_flag = (trend.direction == "declining" and trend.slope < -0.01) or latest_value < 0
    red_flag_reason = None
    if is_red_flag:
        if latest_value < 0:
            red_flag_reason = f"Negative FCF/Revenue = {latest_value:.2%}"
        else:
            red_flag_reason = f"Declining FCF/Revenue trend (slope: {trend.slope:.4f})"
    
    return MetricResult(
        name="FCF to Revenue",
        latest_value=latest_value,
        trend=trend,
        is_red_flag=is_red_flag,
        red_flag_reason=red_flag_reason,
        component_values={
            "fcf": latest_fcf,
            "revenue": latest_revenue
        }
    )


def calculate_cash_flow_yearly_breakdown(
    cash_flow_data: List[Dict],
    income_data: List[Dict]
) -> List[CashFlowYearData]:
    """
    Calculate yearly cash flow breakdown for detailed table view
    Returns data for each year with FCF, Dividends/Buybacks, Revenue, and ratios
    """
    yearly_data = []
    
    for cf_statement in reversed(cash_flow_data):  # Oldest to newest
        year = cf_statement.get("calendarYear") or cf_statement.get("date", "")[:4]
        
        # Get FCF and return components
        fcf = cf_statement.get("freeCashFlow", 0) or 0
        dividends_paid = abs(cf_statement.get("dividendsPaid", 0) or 0)
        buybacks = abs(cf_statement.get("commonStockRepurchased", 0) or 0)
        dividends_buybacks = dividends_paid + buybacks
        
        # Get corresponding income statement for revenue
        income_statement = next(
            (inc for inc in income_data if (inc.get("calendarYear") or inc.get("date", "")[:4]) == year),
            None
        )
        
        revenue = 0
        if income_statement:
            revenue = income_statement.get("revenue", 0) or 0
        
        # Calculate ratios
        fcf_to_div_buybacks = None
        if dividends_buybacks > 0:
            fcf_to_div_buybacks = fcf / dividends_buybacks
        
        fcf_to_rev = None
        if revenue > 0:
            fcf_to_rev = fcf / revenue
        
        # Determine red flags
        is_red_flag = False
        red_flag_reason = None
        
        # Red flag if FCF/Dividends+Buybacks < 1.0 or FCF/Revenue declining significantly
        if fcf_to_div_buybacks is not None and fcf_to_div_buybacks < 1.0:
            is_red_flag = True
            red_flag_reason = f"FCF/Div+Buybacks = {fcf_to_div_buybacks:.2f} < 1.0"
        elif fcf_to_rev is not None and fcf_to_rev < 0:
            is_red_flag = True
            red_flag_reason = f"Negative FCF/Revenue = {fcf_to_rev:.2%}"
        
        yearly_data.append(CashFlowYearData(
            year=int(year) if str(year).isdigit() else 0,
            fcf=fcf,
            dividends_buybacks=dividends_buybacks,
            revenue=revenue,
            fcf_to_dividends_buybacks=fcf_to_div_buybacks,
            fcf_to_revenue=fcf_to_rev,
            is_red_flag=is_red_flag,
            red_flag_reason=red_flag_reason
        ))
    
    return yearly_data



# ============================================================================
# 2. Balance Sheet Stress and Leverage Metrics
# ============================================================================


def calculate_balance_sheet_yearly_breakdown(
    balance_sheet_data: List[Dict],
    income_data: List[Dict],
    cash_flow_data: List[Dict]
) -> List[BalanceSheetYearData]:
    """
    Calculate yearly balance sheet breakdown for detailed table view
    """
    yearly_data = []
    
    for bs_statement in reversed(balance_sheet_data):
        year = bs_statement.get("calendarYear") or bs_statement.get("date", "")[:4]
        
        # Find matching income and cash flow statements
        income_statement = next(
            (inc for inc in income_data if (inc.get("calendarYear") or inc.get("date", "")[:4]) == year),
            None
        )
        cf_statement = next(
            (cf for cf in cash_flow_data if (cf.get("calendarYear") or cf.get("date", "")[:4]) == year),
            None
        )
        
        # Initialize values
        net_debt = 0
        ebitda = 0
        capitalized_costs = 0
        revenue = 0
        net_debt_to_ebitda = None
        cap_costs_to_rev = None
        
        # --- Net Debt / EBITDA ---
        if income_statement and cf_statement:
            # Net Debt
            long_term_debt = bs_statement.get("longTermDebt", 0) or 0
            short_term_debt = bs_statement.get("shortTermDebt", 0) or 0
            cash = bs_statement.get("cashAndCashEquivalents", 0) or 0
            net_debt = long_term_debt + short_term_debt - cash
            
            # EBITDA
            net_income = income_statement.get("netIncome", 0) or 0
            interest_expense = income_statement.get("interestExpense", 0) or 0
            tax_expense = income_statement.get("incomeTaxExpense", 0) or 0
            depreciation = cf_statement.get("depreciationAndAmortization", 0) or 0
            ebitda = net_income + interest_expense + tax_expense + depreciation
            
            if ebitda > 0:
                net_debt_to_ebitda = net_debt / ebitda
        
        # --- Capitalized Costs / Revenue ---
        if income_statement:
            revenue = income_statement.get("revenue", 0) or 0
            
            if cf_statement:
                capitalized_costs += abs(cf_statement.get("capitalizedContractCosts", 0) or 0)
                capitalized_costs += abs(cf_statement.get("capitalizedSoftware", 0) or 0)
                capitalized_costs += abs(cf_statement.get("deferredContractCosts", 0) or 0)
                
                # Acquisitions/Investments that might be capitalized costs
                acquisitions = cf_statement.get("acquisitionsNet", 0) or 0
                if acquisitions < 0:
                    capitalized_costs += abs(acquisitions)
                
                other_investing = cf_statement.get("otherInvestingActivites", 0) or 0
                if other_investing < 0:
                     capitalized_costs += abs(other_investing)
            
            if revenue > 0:
                cap_costs_to_rev = capitalized_costs / revenue

        # --- Red Flags ---
        is_red_flag = False
        reasons = []
        
        if net_debt_to_ebitda is not None and net_debt_to_ebitda > 4.0:
            is_red_flag = True
            reasons.append(f"Net Debt/EBITDA > 4.0x")
            
        if cap_costs_to_rev is not None and cap_costs_to_rev > 0.15: 
            is_red_flag = True
            reasons.append(f"Cap Costs/Rev > 15%")
        
        yearly_data.append(BalanceSheetYearData(
            year=int(year) if str(year).isdigit() else 0,
            net_debt=net_debt,
            ebitda=ebitda,
            capitalized_costs=capitalized_costs,
            revenue=revenue,
            net_debt_to_ebitda=net_debt_to_ebitda,
            capitalized_costs_to_revenue=cap_costs_to_rev,
            is_red_flag=is_red_flag,
            red_flag_reason="; ".join(reasons) if reasons else None
        ))
        
    return yearly_data


def calculate_working_capital_yearly_breakdown(
    income_data: List[Dict],
    balance_sheet_data: List[Dict]
) -> List[WorkingCapitalYearData]:
    """Calculate yearly working capital breakdown"""
    yearly_data = []
    
    inc_map = {d.get("calendarYear") or d.get("date", "")[:4]: d for d in income_data}
    bs_map = {d.get("calendarYear") or d.get("date", "")[:4]: d for d in balance_sheet_data}
    
    # Sort years Oldest -> Newest
    all_years = sorted(list(set(inc_map.keys()) | set(bs_map.keys())))
    
    for i, year in enumerate(all_years):
        if not year.isdigit(): continue
            
        inc = inc_map.get(year)
        bs = bs_map.get(year)
        
        revenue = (inc.get("revenue", 0) or 0) if inc else 0
        receivables = (bs.get("netReceivables", 0) or bs.get("accountsReceivable", 0) or 0) if bs else 0
        
        dso = (receivables / revenue * 365) if revenue > 0 else 0
        
        # Growth requires previous year
        prev_year = all_years[i-1] if i > 0 else None
        
        ar_growth = None
        rev_growth = None
        is_red_flag = False
        reasons = []
        
        if prev_year:
            inc_prev = inc_map.get(prev_year)
            bs_prev = bs_map.get(prev_year)
            
            if inc_prev and bs_prev:
                rev_prev = (inc_prev.get("revenue", 0) or 0)
                ar_prev = (bs_prev.get("netReceivables", 0) or bs_prev.get("accountsReceivable", 0) or 0)
                
                rev_growth = ((revenue - rev_prev) / rev_prev) if rev_prev != 0 else 0
                ar_growth = ((receivables - ar_prev) / ar_prev) if ar_prev != 0 else 0
                
                # Check for Channel Stuffing
                dso_prev = (ar_prev / rev_prev * 365) if rev_prev > 0 else 0
                dso_rising = dso > dso_prev + 2
                
                if (rev_growth < ar_growth) and dso_rising:
                    is_red_flag = True
                    reasons.append(f"Channel Stuffing Risk")

        yearly_data.append(WorkingCapitalYearData(
            year=int(year),
            dso=dso,
            receivables=receivables,
            revenue=revenue,
            ar_growth=ar_growth,
            revenue_growth=rev_growth,
            is_red_flag=is_red_flag,
            red_flag_reason="; ".join(reasons) if reasons else None
        ))
        
    return yearly_data


def calculate_valuation_yearly_breakdown(
    income_data: List[Dict],
    balance_sheet_data: List[Dict],
    cash_flow_data: List[Dict],
    current_price: Optional[float]
) -> List[ValuationYearData]:
    """Calculate yearly valuation breakdown (using current price proxy)"""
    yearly_data = []
    
    bs_map = {d.get("calendarYear") or d.get("date", "")[:4]: d for d in balance_sheet_data}
    cf_map = {d.get("calendarYear") or d.get("date", "")[:4]: d for d in cash_flow_data}
    
    # Browse income data (Newest -> Oldest), define sort is Oldest -> Newest
    # Let's verify income_data sort order. Assuming FMP API returns Newest -> Oldest.
    # Reversed -> Oldest -> Newest.
    
    for inc in reversed(income_data):
        year = inc.get("calendarYear") or inc.get("date", "")[:4]
        if not str(year).isdigit(): continue
            
        bs = bs_map.get(year)
        cf = cf_map.get(year)
        
        revenue = inc.get("revenue", 0) or 0
        
        ebitda = 0
        if cf:
             net_income = inc.get("netIncome", 0) or 0
             interest = inc.get("interestExpense", 0) or 0
             tax = inc.get("incomeTaxExpense", 0) or 0
             dep = cf.get("depreciationAndAmortization", 0) or 0
             ebitda = net_income + interest + tax + dep
             
        enterprise_value = 0
        ev_to_revenue = None
        ev_to_ebitda = None
        
        if bs and current_price:
            shares = inc.get("weightedAverageShsOut", 0) or 0
            market_cap = current_price * shares
            
            total_debt = (bs.get("totalDebt", 0) or 
                         ((bs.get("longTermDebt", 0) or 0) + (bs.get("shortTermDebt", 0) or 0)))
            cash = bs.get("cashAndCashEquivalents", 0) or 0
            
            enterprise_value = market_cap + total_debt - cash
            
            if revenue > 0:
                ev_to_revenue = enterprise_value / revenue
            
            if ebitda > 0:
                ev_to_ebitda = enterprise_value / ebitda
        
        is_red_flag = False
        
        yearly_data.append(ValuationYearData(
            year=int(year),
            ev_to_revenue=ev_to_revenue,
            ev_to_ebitda=ev_to_ebitda,
            enterprise_value=enterprise_value,
            revenue=revenue,
            ebitda=ebitda,
            is_red_flag=is_red_flag,
            red_flag_reason=None
        ))
        
    return yearly_data


def calculate_net_debt_to_ebitda(
    balance_sheet_data: List[Dict],
    income_data: List[Dict],
    cash_flow_data: List[Dict]
) -> MetricResult:
    """
    Calculate Net Debt / EBITDA ratio with 5-year trend
    
    Net Debt = Long-Term Debt + Short-Term Debt - Cash
    EBITDA = Net Income + Interest + Tax + D&A
    
    Red Flag: Ratio > 4.0x - 6.0x
    """
    values = []
    years = []
    latest_net_debt = None
    latest_ebitda = None
    
    for bs_statement in reversed(balance_sheet_data):
        year = bs_statement.get("calendarYear") or bs_statement.get("date", "")[:4]
        
        # Find matching income and cash flow statements
        income_statement = next(
            (inc for inc in income_data if (inc.get("calendarYear") or inc.get("date", "")[:4]) == year),
            None
        )
        cf_statement = next(
            (cf for cf in cash_flow_data if (cf.get("calendarYear") or cf.get("date", "")[:4]) == year),
            None
        )
        
        if income_statement and cf_statement:
            # Calculate Net Debt
            long_term_debt = bs_statement.get("longTermDebt", 0) or 0
            short_term_debt = bs_statement.get("shortTermDebt", 0) or 0
            cash = bs_statement.get("cashAndCashEquivalents", 0) or 0
            net_debt = long_term_debt + short_term_debt - cash
            
            # Calculate EBITDA
            net_income = income_statement.get("netIncome", 0) or 0
            interest_expense = income_statement.get("interestExpense", 0) or 0
            tax_expense = income_statement.get("incomeTaxExpense", 0) or 0
            depreciation_amortization = cf_statement.get("depreciationAndAmortization", 0) or 0
            
            ebitda = net_income + interest_expense + tax_expense + depreciation_amortization
            
            if ebitda > 0:
                ratio = net_debt / ebitda
                values.append(ratio)
                years.append(year)
                # Store latest values
                latest_net_debt = net_debt
                latest_ebitda = ebitda
    
    if not values:
        return MetricResult(
            name="Net Debt to EBITDA",
            latest_value=None,
            trend=None,
            is_red_flag=False,
            red_flag_reason=None,
            component_values=None
        )
    
    trend = analyze_trend(values, years)
    latest_value = trend.latest_value
    
    # Red flag if > 4.0x (conservative threshold)
    is_red_flag = latest_value > 4.0
    red_flag_reason = f"Net Debt/EBITDA = {latest_value:.2f}x > 4.0x" if is_red_flag else None
    
    return MetricResult(
        name="Net Debt to EBITDA",
        latest_value=latest_value,
        trend=trend,
        is_red_flag=is_red_flag,
        red_flag_reason=red_flag_reason,
        component_values={
            "net_debt": latest_net_debt,
            "ebitda": latest_ebitda
        }
    )


def calculate_capitalized_costs_to_revenue(
    cash_flow_data: List[Dict],
    balance_sheet_data: List[Dict],
    income_data: List[Dict],
    ticker: Optional[str] = None
) -> MetricResult:
    """
    Calculate Capitalized Costs / Revenue ratio with 5-year trend
    
    Capitalized Costs from:
    1. Cash Flow Statement: capitalizedContractCosts, capitalizedSoftware, etc.
    2. Balance Sheet: deferredCosts, intangibleAssets (fallback)
    
    Red Flag: Ratio > 2x-3x peer average (for now, flag if > 0.15 or 15%)
    """
    values = []
    years = []
    latest_capitalized_costs = None
    latest_revenue = None
    
    for cf_statement in reversed(cash_flow_data):
        year = cf_statement.get("calendarYear") or cf_statement.get("date", "")[:4]
        
        # Find matching balance sheet and income statement
        bs_statement = next(
            (bs for bs in balance_sheet_data if (bs.get("calendarYear") or bs.get("date", "")[:4]) == year),
            None
        )
        income_statement = next(
            (inc for inc in income_data if (inc.get("calendarYear") or inc.get("date", "")[:4]) == year),
            None
        )
        
        if income_statement:
            revenue = income_statement.get("revenue", 0) or 0
            
            # Try to get capitalized costs from cash flow statement (Investing Activities)
            # Look for negative values indicating cash outflows for capitalization
            capitalized_costs = 0
            
            # Option 1: Direct capitalization fields
            capitalized_costs += abs(cf_statement.get("capitalizedContractCosts", 0) or 0)
            capitalized_costs += abs(cf_statement.get("capitalizedSoftware", 0) or 0)
            capitalized_costs += abs(cf_statement.get("deferredContractCosts", 0) or 0)
            
            # Option 2: Acquisitions and other investing activities (check for negative values)
            acquisitions = cf_statement.get("acquisitionsNet", 0) or 0
            if acquisitions < 0:  # Negative means cash outflow
                capitalized_costs += abs(acquisitions)
            
            other_investing = cf_statement.get("otherInvestingActivites", 0) or 0
            if other_investing < 0:  # Negative means cash outflow
                capitalized_costs += abs(other_investing)
            
            # If no data in cash flow, try balance sheet (year-over-year change)
            if capitalized_costs == 0 and bs_statement:
                # Look for bloating in intangibles or other non-current assets
                intangibles = bs_statement.get("intangibleAssets", 0) or 0
                other_non_current = bs_statement.get("otherNonCurrentAssets", 0) or 0
                capitalized_costs = intangibles + other_non_current

            
            if revenue > 0 and capitalized_costs > 0:
                ratio = capitalized_costs / revenue
                values.append(ratio)
                years.append(year)
                # Store latest values
                latest_capitalized_costs = capitalized_costs
                latest_revenue = revenue
    
    if not values:
        return MetricResult(
            name="Capitalized Costs to Revenue",
            latest_value=None,
            trend=None,
            is_red_flag=False,
            red_flag_reason=None,
            component_values=None
        )
    
    trend = analyze_trend(values, years)
    latest_value = trend.latest_value
    
    # Red flag: Compare to peers if ticker provided
    is_red_flag = False
    red_flag_reason = None
    
    if ticker and PEER_COMPARISON_AVAILABLE and latest_value is not None:
        try:
            peer_result = compare_capitalized_costs_to_peers(ticker, latest_value)
            is_red_flag = peer_result.get("is_red_flag", False)
            red_flag_reason = peer_result.get("reason")
        except Exception as e:
            logger.warning(f"Peer comparison failed for {ticker} Capitalized Costs: {e}")
    
    return MetricResult(
        name="Capitalized Costs to Revenue",
        latest_value=latest_value,
        trend=trend,
        is_red_flag=is_red_flag,
        red_flag_reason=red_flag_reason,
        component_values={
            "capitalized_costs": latest_capitalized_costs,
            "revenue": latest_revenue
        }
    )


# ============================================================================
# 3. Working Capital Anomalies Metrics
# ============================================================================

def calculate_days_sales_outstanding(
    balance_sheet_data: List[Dict],
    income_data: List[Dict],
    ticker: Optional[str] = None
) -> MetricResult:
    """
    Calculate DSO (Days Sales Outstanding) with 5-year trend
    
    DSO = (Accounts Receivable / Revenue) × 365
    
    Red Flag: Significant deviation from industry mean (requires peer comparison)
    For now, flag if DSO > 90 days or < 20 days (anomalies)
    """
    values = []
    years = []
    latest_ar = None
    latest_revenue = None
    
    for bs_statement in reversed(balance_sheet_data):
        year = bs_statement.get("calendarYear") or bs_statement.get("date", "")[:4]
        
        # Find matching income statement
        income_statement = next(
            (inc for inc in income_data if (inc.get("calendarYear") or inc.get("date", "")[:4]) == year),
            None
        )
        
        if income_statement:
            accounts_receivable = bs_statement.get("netReceivables", 0) or bs_statement.get("accountsReceivable", 0) or 0
            revenue = income_statement.get("revenue", 0) or 0
            
            if revenue > 0:
                dso = (accounts_receivable / revenue) * 365
                values.append(dso)
                years.append(year)
                # Store latest values
                latest_ar = accounts_receivable
                latest_revenue = revenue
    
    if not values:
        return MetricResult(
            name="Days Sales Outstanding",
            latest_value=None,
            trend=None,
            is_red_flag=False,
            red_flag_reason=None,
            component_values=None
        )
    
    trend = analyze_trend(values, years)
    latest_value = trend.latest_value
    
    # Red flag: Compare to peers if ticker provided
    is_red_flag = False
    red_flag_reason = None
    
    if ticker and PEER_COMPARISON_AVAILABLE and latest_value is not None:
        try:
            peer_result = compare_dso_to_peers(ticker, latest_value)
            is_red_flag = peer_result.get("is_red_flag", False)
            red_flag_reason = peer_result.get("reason")
        except Exception as e:
            logger.warning(f"Peer comparison failed for {ticker} DSO: {e}")
    
    return MetricResult(
        name="Days Sales Outstanding",
        latest_value=latest_value,
        trend=trend,
        is_red_flag=is_red_flag,
        red_flag_reason=red_flag_reason,
        component_values={
            "accounts_receivable": latest_ar,
            "revenue": latest_revenue
        }
    )


# ============================================================================
# 4. Valuation Dislocation Metrics
# ============================================================================

def calculate_ev_to_ebitda(
    income_data: List[Dict],
    balance_sheet_data: List[Dict],
    cash_flow_data: List[Dict],
    current_price: float,
) -> MetricResult:
    """
    Calculate EV / EBITDA ratio with 5-year trend
    
    Enterprise Value = Market Cap + Total Debt - Cash
    Market Cap = Share Price × Weighted Average Shares Outstanding
    
    Args:
        current_price: Current stock price for market cap calculation
    
    Note: Requires peer comparison for red flag determination
    """
    values = []
    years = []
    latest_ev = None
    latest_ebitda = None
    
    for income_statement in reversed(income_data):
        year = income_statement.get("calendarYear") or income_statement.get("date", "")[:4]
        
        # Find matching balance sheet and cash flow
        bs_statement = next(
            (bs for bs in balance_sheet_data if (bs.get("calendarYear") or bs.get("date", "")[:4]) == year),
            None
        )
        cf_statement = next(
            (cf for cf in cash_flow_data if (cf.get("calendarYear") or cf.get("date", "")[:4]) == year),
            None
        )
        
        if bs_statement and cf_statement:
            # Calculate Market Cap
            shares_outstanding = income_statement.get("weightedAverageShsOut", 0) or 0
            market_cap = current_price * shares_outstanding
            
            # Calculate Enterprise Value
            total_debt = (bs_statement.get("longTermDebt", 0) or 0) + (bs_statement.get("shortTermDebt", 0) or 0)
            cash = bs_statement.get("cashAndCashEquivalents", 0) or 0
            enterprise_value = market_cap + total_debt - cash
            
            # Calculate EBITDA
            net_income = income_statement.get("netIncome", 0) or 0
            interest_expense = income_statement.get("interestExpense", 0) or 0
            tax_expense = income_statement.get("incomeTaxExpense", 0) or 0
            depreciation_amortization = cf_statement.get("depreciationAndAmortization", 0) or 0
            ebitda = net_income + interest_expense + tax_expense + depreciation_amortization
            
            if ebitda > 0:
                ev_ebitda = enterprise_value / ebitda
                values.append(ev_ebitda)
                years.append(year)
                # Store latest values
                latest_ev = enterprise_value
                latest_ebitda = ebitda
    
    if not values:
        return MetricResult(
            name="EV to EBITDA",
            latest_value=None,
            trend=None,
            is_red_flag=False,
            red_flag_reason=None,
            component_values=None
        )
    
    trend = analyze_trend(values, years)
    latest_value = trend.latest_value
    
    # Red flag requires peer comparison
    # Compare multiples against stable, large-cap peers to identify valuation bubbles
    # Example: If peer avg is 15x and stock is 30x, that's a red flag
    is_red_flag = False  # Disabled until peer comparison implemented
    red_flag_reason = None
    
    return MetricResult(
        name="EV to EBITDA",
        latest_value=latest_value,
        trend=trend,
        is_red_flag=is_red_flag,
        red_flag_reason=red_flag_reason,
        component_values={
            "enterprise_value": latest_ev,
            "ebitda": latest_ebitda
        }
    )


def calculate_ev_to_revenue(
    income_data: List[Dict],
    balance_sheet_data: List[Dict],
    current_price: float,
    ticker: Optional[str] = None
) -> MetricResult:
    """
    Calculate EV / Revenue ratio with 5-year trend
    
    Enterprise Value = Market Cap + Total Debt - Cash
    Market Cap = Share Price × Weighted Average Shares Outstanding
    
    Args:
        current_price: Current stock price for market cap calculation
    
    Note: Requires peer comparison for red flag determination
    Example: Kyndryl trading at 1x when peers are 0.5x despite worse margins
    """
    values = []
    years = []
    latest_ev = None
    latest_revenue = None
    
    for income_statement in reversed(income_data):
        year = income_statement.get("calendarYear") or income_statement.get("date", "")[:4]
        
        # Find matching balance sheet
        bs_statement = next(
            (bs for bs in balance_sheet_data if (bs.get("calendarYear") or bs.get("date", "")[:4]) == year),
            None
        )
        
        if bs_statement:
            # Calculate Market Cap
            shares_outstanding = income_statement.get("weightedAverageShsOut", 0) or 0
            market_cap = current_price * shares_outstanding
            
            # Calculate Enterprise Value
            total_debt = (bs_statement.get("totalDebt", 0) or 
                         ((bs_statement.get("longTermDebt", 0) or 0) + (bs_statement.get("shortTermDebt", 0) or 0)))
            cash = bs_statement.get("cashAndCashEquivalents", 0) or 0
            enterprise_value = market_cap + total_debt - cash
            
            # Get Revenue
            revenue = income_statement.get("revenue", 0) or 0
            
            if revenue > 0:
                ev_revenue = enterprise_value / revenue
                values.append(ev_revenue)
                years.append(year)
                # Store latest values
                latest_ev = enterprise_value
                latest_revenue = revenue
    
    if not values:
        return MetricResult(
            name="EV to Revenue",
            latest_value=None,
            trend=None,
            is_red_flag=False,
            red_flag_reason=None,
            component_values=None
        )
    
    trend = analyze_trend(values, years)
    latest_value = trend.latest_value
    
    # Red flag: Compare to peers if ticker provided
    is_red_flag = False
    red_flag_reason = None
    
    if ticker and PEER_COMPARISON_AVAILABLE and latest_value is not None:
        try:
            # Note: Using EV/EBITDA comparison function as proxy for EV/Revenue
            # You may want to create a separate compare_ev_revenue_to_peers function
            peer_result = compare_ev_ebitda_to_peers(ticker, latest_value)
            is_red_flag = peer_result.get("is_red_flag", False)
            red_flag_reason = peer_result.get("reason")
        except Exception as e:
            logger.warning(f"Peer comparison failed for {ticker} EV/Revenue: {e}")
    
    return MetricResult(
        name="EV to Revenue",
        latest_value=latest_value,
        trend=trend,
        is_red_flag=is_red_flag,
        red_flag_reason=red_flag_reason,
        component_values={
            "enterprise_value": latest_ev,
            "revenue": latest_revenue
        }
    )


def calculate_channel_stuffing_risk(
    income_data: List[Dict],
    balance_sheet_data: List[Dict]
) -> MetricResult:
    """
    Detect Channel Stuffing Risk
    
    Logic:
    1. Calculate Revenue Growth vs Accounts Receivable Growth
    2. Check if DSO is rising
    
    Red Flag: (Rev Growth < AR Growth) AND (DSO rising)
    """
    # Requires at least 2 years of data for growth calculation
    if len(income_data) < 2 or len(balance_sheet_data) < 2:
        return MetricResult(
            name="Channel Stuffing Risk",
            latest_value=None,
            trend=None,
            is_red_flag=False,
            red_flag_reason="Insufficient data for growth calculation"
        )
        
    # Get latest 2 years (data is sorted newest to oldest in lists usually, but we need to match by year)
    # Helper to map year -> data
    def get_data_by_year(data_list):
        return {d.get("calendarYear") or d.get("date", "")[:4]: d for d in data_list}
        
    inc_map = get_data_by_year(income_data)
    bs_map = get_data_by_year(balance_sheet_data)
    
    # Find common years
    common_years = sorted(list(set(inc_map.keys()) & set(bs_map.keys())), reverse=True) # Newest first
    
    if len(common_years) < 2:
         return MetricResult(
            name="Channel Stuffing Risk",
            latest_value=None,
            trend=None,
            is_red_flag=False,
            red_flag_reason="Insufficient common years data"
        )
    
    latest_year = common_years[0]
    prev_year = common_years[1]
    
    # Calculate Growth
    inc_curr = inc_map[latest_year]
    inc_prev = inc_map[prev_year]
    bs_curr = bs_map[latest_year]
    bs_prev = bs_map[prev_year]
    
    rev_curr = inc_curr.get("revenue", 0) or 0
    rev_prev = inc_prev.get("revenue", 0) or 0
    
    ar_curr = bs_curr.get("netReceivables", 0) or bs_curr.get("accountsReceivable", 0) or 0
    ar_prev = bs_prev.get("netReceivables", 0) or bs_prev.get("accountsReceivable", 0) or 0
    
    rev_growth = ((rev_curr - rev_prev) / rev_prev) if rev_prev != 0 else 0
    ar_growth = ((ar_curr - ar_prev) / ar_prev) if ar_prev != 0 else 0
    
    # Check DSO Trend using existing data processing
    # We can recalculate DSO for strictness or assume we want just the last 2 years direction
    dso_curr = (ar_curr / rev_curr * 365) if rev_curr != 0 else 0
    dso_prev = (ar_prev / rev_prev * 365) if rev_prev != 0 else 0
    dso_rising = dso_curr > dso_prev + 2  # slight buffer
    
    # Logic: Rev Growth < AR Growth AND DSO Rising
    is_red_flag = (rev_growth < ar_growth) and dso_rising
    
    red_flag_reason = None
    if is_red_flag:
        red_flag_reason = (
            f"Possible Channel Stuffing: AR Growth ({ar_growth:.1%}) > Rev Growth ({rev_growth:.1%}) "
            f"and DSO rising ({dso_prev:.1f} -> {dso_curr:.1f} days)"
        )
        
    return MetricResult(
        name="Channel Stuffing Risk",
        latest_value=ar_growth - rev_growth, # Value is the spread
        trend=None, # Not a simple trend metric
        is_red_flag=is_red_flag,
        red_flag_reason=red_flag_reason,
        component_values={
            "ar_growth": ar_growth,
            "revenue_growth": rev_growth,
            "dso_current": dso_curr,
            "dso_previous": dso_prev,
            "ar_current": ar_curr,
            "ar_previous": ar_prev,
            "revenue_current": rev_curr,
            "revenue_previous": rev_prev
        }
    )


# ============================================================================
# Main Calculator Function
# ============================================================================

def calculate_all_metrics(
    income_data: List[Dict],
    cash_flow_data: List[Dict],
    balance_sheet_data: List[Dict],
    current_price: float = None,
    ticker: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate all screening metrics from financial statements
    
    Args:
        income_data: List of income statements (5 years)
        cash_flow_data: List of cash flow statements (5 years)
        balance_sheet_data: List of balance sheets (5 years)
        current_price: Current stock price (optional, for EV calculation)
        ticker: Stock ticker (optional, enables peer comparison for red flags)
    
    Returns:
        Dictionary with metrics and yearly breakdown data
    """
    metrics = {}
    
    # 1. Cash Flow Sustainability
    metrics["fcf_to_dividends_buybacks"] = calculate_fcf_to_dividends_buybacks_ratio(cash_flow_data)
    metrics["fcf_to_revenue"] = calculate_fcf_to_revenue_ratio(cash_flow_data, income_data)
    
    # Cash Flow Yearly Breakdown (for restructured table)
    cash_flow_yearly_breakdown = calculate_cash_flow_yearly_breakdown(cash_flow_data, income_data)
    
    # 2. Balance Sheet Stress
    metrics["net_debt_to_ebitda"] = calculate_net_debt_to_ebitda(balance_sheet_data, income_data, cash_flow_data)
    metrics["capitalized_costs_to_revenue"] = calculate_capitalized_costs_to_revenue(
        cash_flow_data, balance_sheet_data, income_data, ticker=ticker
    )
    
    # 3. Working Capital Anomalies
    metrics["days_sales_outstanding"] = calculate_days_sales_outstanding(balance_sheet_data, income_data, ticker=ticker)
    metrics["channel_stuffing_risk"] = calculate_channel_stuffing_risk(income_data, balance_sheet_data)
    
    # 4. Valuation Dislocation (requires current price)
    if current_price:
        metrics["ev_to_revenue"] = calculate_ev_to_revenue(
            income_data, balance_sheet_data, current_price, ticker=ticker
        )
        metrics["ev_to_ebitda"] = calculate_ev_to_ebitda(
            income_data, balance_sheet_data, cash_flow_data, current_price
        )
    
    # Calculate Balance Sheet Yearly Breakdown
    balance_sheet_yearly_breakdown = calculate_balance_sheet_yearly_breakdown(
        balance_sheet_data,
        income_data,
        cash_flow_data
    )
    

    # Calculate Working Capital Yearly Breakdown
    working_capital_yearly_breakdown = calculate_working_capital_yearly_breakdown(
        income_data,
        balance_sheet_data
    )
    
    # Calculate Valuation Yearly Breakdown
    valuation_yearly_breakdown = calculate_valuation_yearly_breakdown(
        income_data,
        balance_sheet_data,
        cash_flow_data,
        current_price
    )
    
    return {
        "metrics": metrics,
        "cash_flow_yearly_breakdown": [
            {
                "year": data.year,
                "fcf": data.fcf,
                "dividends_buybacks": data.dividends_buybacks,
                "revenue": data.revenue,
                "fcf_to_dividends_buybacks": data.fcf_to_dividends_buybacks,
                "fcf_to_revenue": data.fcf_to_revenue,
                "is_red_flag": data.is_red_flag,
                "red_flag_reason": data.red_flag_reason
            }
            for data in cash_flow_yearly_breakdown
        ],
        "balance_sheet_yearly_breakdown": [
            {
                "year": data.year,
                "net_debt": data.net_debt,
                "ebitda": data.ebitda,
                "capitalized_costs": data.capitalized_costs,
                "revenue": data.revenue,
                "net_debt_to_ebitda": data.net_debt_to_ebitda,
                "capitalized_costs_to_revenue": data.capitalized_costs_to_revenue,
                "is_red_flag": data.is_red_flag,
                "red_flag_reason": data.red_flag_reason
            }
            for data in balance_sheet_yearly_breakdown
        ],
        "working_capital_yearly_breakdown": [
            {
                "year": data.year,
                "dso": data.dso,
                "receivables": data.receivables,
                "revenue": data.revenue,
                "ar_growth": data.ar_growth,
                "revenue_growth": data.revenue_growth,
                "is_red_flag": data.is_red_flag,
                "red_flag_reason": data.red_flag_reason
            }
            for data in working_capital_yearly_breakdown
        ],
        "valuation_yearly_breakdown": [
            {
                "year": data.year,
                "ev_to_revenue": data.ev_to_revenue,
                "ev_to_ebitda": data.ev_to_ebitda,
                "enterprise_value": data.enterprise_value,
                "revenue": data.revenue,
                "ebitda": data.ebitda,
                "is_red_flag": data.is_red_flag,
                "red_flag_reason": data.red_flag_reason
            }
            for data in valuation_yearly_breakdown
        ]
    }


def check_red_flags(metrics: Dict[str, MetricResult]) -> Dict[str, Any]:
    """
    Check which metrics are red flags
    
    Returns:
        Dictionary with red flag summary
    """
    red_flags = []
    strategies_flagged = []
    
    for metric_key, metric in metrics.items():
        if metric.is_red_flag:
            red_flags.append({
                "metric": metric.name,
                "value": metric.latest_value,
                "reason": metric.red_flag_reason
            })
            
            # Map to strategy
            if metric_key in ["fcf_to_dividends_buybacks", "fcf_to_revenue"]:
                if "Cash Flow Sustainability" not in strategies_flagged:
                    strategies_flagged.append("Cash Flow Sustainability")
            elif metric_key in ["net_debt_to_ebitda", "capitalized_costs_to_revenue"]:
                if "Balance Sheet Stress" not in strategies_flagged:
                    strategies_flagged.append("Balance Sheet Stress")
            elif metric_key == "days_sales_outstanding":
                if "Working Capital Anomalies" not in strategies_flagged:
                    strategies_flagged.append("Working Capital Anomalies")
            elif metric_key == "channel_stuffing_risk":
                if "Working Capital Anomalies" not in strategies_flagged:
                     strategies_flagged.append("Working Capital Anomalies")
            elif metric_key == "ev_to_ebitda":
                if "Valuation Dislocation" not in strategies_flagged:
                    strategies_flagged.append("Valuation Dislocation")
    
    return {
        "has_red_flags": len(red_flags) > 0,
        "red_flag_count": len(red_flags),
        "red_flags": red_flags,
        "strategies_flagged": strategies_flagged
    }
