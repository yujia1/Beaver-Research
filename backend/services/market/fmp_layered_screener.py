"""
Layered Screener using FMP `key-metrics` and financial statements.

Implements 4 layers:
 - Layer 1: Survival Filter (hard elimination)
 - Layer 2: Economic Reality (earnings quality)
 - Layer 3: Structural Health
 - Layer 4: Valuation & Decision Rules

Each layer returns both:
  - `checks`  : latest-value summary items
  - `yearly`  : per-fiscal-year breakdown rows (newest → oldest)
  - `notes`   : human-readable red-flag strings

Exposes `run_layered_screener(symbol, limit=5, period='FY')`.
"""
import logging
from typing import Dict, Any, List, Optional

from .fmp_financial_service import (
    fetch_key_metrics,
    fetch_income_statement,
    fetch_cash_flow_statement,
    fetch_balance_sheet,
    fetch_stock_quote,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe(x) -> Optional[float]:
    try:
        return float(x) if x is not None else None
    except Exception:
        return None


def _pct_str(x: Optional[float], decimals: int = 2) -> Optional[str]:
    """Format a decimal fraction as percentage string, e.g. 0.45 → '45.00%'"""
    if x is None:
        return None
    return f"{x * 100:.{decimals}f}%"


def _fmt_currency(x: Optional[float]) -> Optional[str]:
    if x is None:
        return None
    abs_x = abs(x)
    if abs_x >= 1e9:
        return f"${x / 1e9:.2f}B"
    if abs_x >= 1e6:
        return f"${x / 1e6:.2f}M"
    if abs_x >= 1e3:
        return f"${x / 1e3:.2f}K"
    return f"${x:.2f}"


def _year_from_row(row: dict) -> Optional[str]:
    """Extract calendar year or calendarYear from a statement row."""
    return str(row.get("calendarYear") or row.get("date", "")[:4] or "")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_layered_screener(symbol: str, limit: int = 5, period: str = "FY") -> Dict[str, Any]:
    """
    Run the 4-layer screener for a single ticker using FMP endpoints.

    Returns a structured result with per-layer checks, yearly breakdown, and action.
    """
    symbol = symbol.upper()

    key_metrics = fetch_key_metrics(symbol, limit=limit, period=period)
    income      = fetch_income_statement(symbol, years=limit)
    cashflow    = fetch_cash_flow_statement(symbol, years=limit)
    balance     = fetch_balance_sheet(symbol, years=limit)
    quote       = fetch_stock_quote(symbol)

    # Most-recent row for single-point checks
    km = key_metrics[0] if key_metrics else {}

    # Align all lists to the shortest available length
    n = min(len(key_metrics), len(income), len(cashflow), len(balance), limit)

    # =========================================================================
    # Layer 1 — Survival Filter
    # =========================================================================
    survival_checks = []
    survival_fail_reasons = []
    survival_yearly = []

    for i in range(n):
        km_row  = key_metrics[i]
        inc_row = income[i]
        bs_row  = balance[i]
        cf_row  = cashflow[i]
        year    = _year_from_row(km_row) or _year_from_row(inc_row)

        current_ratio        = _safe(km_row.get("currentRatio"))
        interest_burden      = _safe(km_row.get("interestBurden"))
        net_debt_to_ebitda  = _safe(km_row.get("netDebtToEBITDA") or km_row.get("netDebtToEbitda"))
        fcf                  = _safe(km_row.get("freeCashFlow") or cf_row.get("freeCashFlow"))

        # Thresholds
        cr_pass   = current_ratio   >= 1.0  if current_ratio   is not None else None
        ib_pass   = interest_burden >= 2.0  if interest_burden is not None else None
        nd_pass   = net_debt_to_ebitda <= 4.0 if net_debt_to_ebitda is not None else None
        fcf_pass  = (fcf > 0)             if fcf             is not None else None

        row_fail = any(p is False for p in [cr_pass, ib_pass, nd_pass, fcf_pass])

        survival_yearly.append({
            "year":                year,
            "current_ratio":       current_ratio,
            "current_ratio_pass":  cr_pass,
            "interest_burden":     interest_burden,
            "interest_burden_pass": ib_pass,
            "net_debt_to_ebitda":  net_debt_to_ebitda,
            "net_debt_pass":       nd_pass,
            "fcf":                 fcf,
            "fcf_pass":            fcf_pass,
            "is_red_flag":         row_fail,
        })

    # Summary checks from latest row
    if _safe(km.get("currentRatio")) is not None:
        val  = _safe(km.get("currentRatio"))
        passed = val >= 1.0
        survival_checks.append({"metric": "Current Ratio", "value": val, "pass": passed, "threshold": ">= 1.0", "source": "key-metrics"})
        if not passed:
            survival_fail_reasons.append(f"Low liquidity: currentRatio={val:.2f}")

    if _safe(km.get("interestBurden")) is not None:
        val = _safe(km.get("interestBurden"))
        passed = val >= 2.0
        survival_checks.append({"metric": "Interest Burden (EBIT/Interest)", "value": val, "pass": passed, "threshold": ">= 2.0", "source": "key-metrics"})
        if not passed:
            survival_fail_reasons.append(f"Weak interest coverage: interestBurden={val:.2f}")

    if _safe(km.get("netDebtToEBITDA") or km.get("netDebtToEbitda")) is not None:
        val = _safe(km.get("netDebtToEBITDA") or km.get("netDebtToEbitda"))
        passed = val <= 4.0
        survival_checks.append({"metric": "Net Debt / EBITDA", "value": val, "pass": passed, "threshold": "<= 4.0", "source": "key-metrics"})
        if not passed:
            survival_fail_reasons.append(f"High leverage: netDebtToEBITDA={val:.2f}")

    # FCF persistence check across all years
    fcf_all = [r["fcf"] for r in survival_yearly if r["fcf"] is not None]
    if fcf_all:
        all_negative = all(v < 0 for v in fcf_all)
        survival_checks.append({
            "metric": "FCF Trend",
            "value": fcf_all,
            "pass": not all_negative,
            "threshold": "Not persistently negative",
            "source": "key-metrics"
        })
        if all_negative:
            survival_fail_reasons.append("Persistently negative free cash flow")

    survival_pass = len(survival_fail_reasons) == 0

    # =========================================================================
    # Layer 2 — Earnings Quality (Economic Reality)
    # =========================================================================
    earnings_checks = []
    earnings_notes  = []
    earnings_yearly = []

    for i in range(n):
        km_row  = key_metrics[i]
        inc_row = income[i]
        cf_row  = cashflow[i]
        year    = _year_from_row(km_row) or _year_from_row(inc_row)

        cfo = _safe(cf_row.get("operatingCashFlow") or cf_row.get("netCashProvidedByOperatingActivities"))
        fcf = _safe(cf_row.get("freeCashFlow"))
        ni  = _safe(inc_row.get("netIncome"))

        cfo_to_ni  = (cfo / ni) if (cfo is not None and ni and ni != 0) else None
        fcf_to_ni  = (fcf / ni) if (fcf is not None and ni and ni != 0) else None

        capex_to_rev = _safe(km_row.get("capexToRevenue") or km_row.get("capexToRevenueRatio"))
        sbc_to_rev   = _safe(km_row.get("stockBasedCompensationToRevenue") or km_row.get("stockBasedCompensationToRevenueRatio"))
        shares_out   = _safe(inc_row.get("weightedAverageShsOut"))

        cfo_pass = (0.8 <= cfo_to_ni <= 1.2) if cfo_to_ni is not None else None
        fcf_pass = (fcf_to_ni > 0)           if fcf_to_ni is not None else None

        row_flag = any(p is False for p in [cfo_pass, fcf_pass])

        earnings_yearly.append({
            "year":           year,
            "cfo":            cfo,
            "fcf":            fcf,
            "net_income":     ni,
            "cfo_to_ni":      cfo_to_ni,
            "cfo_to_ni_pass": cfo_pass,
            "fcf_to_ni":      fcf_to_ni,
            "fcf_to_ni_pass": fcf_pass,
            "capex_to_rev":   capex_to_rev,
            "sbc_to_rev":     sbc_to_rev,
            "shares_out":     shares_out,
            "is_red_flag":    row_flag,
        })

    # Average-across-years checks
    cfo_ratios = [r["cfo_to_ni"] for r in earnings_yearly if r["cfo_to_ni"] is not None]
    if cfo_ratios:
        avg = sum(cfo_ratios) / len(cfo_ratios)
        passed = 0.8 <= avg <= 1.2
        earnings_checks.append({"metric": "CFO / Net Income (avg)", "value": avg, "pass": passed, "rule_of_thumb": "~0.8–1.2 over cycle", "source": "income/cashflow"})
        if not passed:
            earnings_notes.append(f"Weak cash conversion: avg CFO/NetIncome={avg:.2f}")

    fcf_ratios = [r["fcf_to_ni"] for r in earnings_yearly if r["fcf_to_ni"] is not None]
    if fcf_ratios:
        avg = sum(fcf_ratios) / len(fcf_ratios)
        passed = avg > 0
        earnings_checks.append({"metric": "FCF / Net Income (avg)", "value": avg, "pass": passed, "rule_of_thumb": "Positive over cycle", "source": "income/cashflow"})
        if not passed:
            earnings_notes.append("FCF does not convert from Net Income (avg negative)")

    # Share dilution CAGR
    share_counts = [r["shares_out"] for r in reversed(earnings_yearly) if r["shares_out"] is not None]
    if len(share_counts) >= 2:
        try:
            start, end = share_counts[0], share_counts[-1]
            yrs = len(share_counts) - 1
            if start > 0 and yrs > 0:
                cagr = (end / start) ** (1.0 / yrs) - 1.0
                earnings_checks.append({"metric": f"Share Count CAGR ({yrs}y)", "value": cagr, "source": "income-statement"})
                if cagr > 0.07:
                    earnings_notes.append(f"High dilution: share count CAGR ~{cagr:.1%}")
        except Exception:
            pass

    # Capex/SBC from latest km
    capex_rev = _safe(km.get("capexToRevenue") or km.get("capexToRevenueRatio"))
    if capex_rev is not None:
        earnings_checks.append({"metric": "Capex / Revenue (latest)", "value": capex_rev, "source": "key-metrics"})
    sbc_rev = _safe(km.get("stockBasedCompensationToRevenue") or km.get("stockBasedCompensationToRevenueRatio"))
    if sbc_rev is not None:
        earnings_checks.append({"metric": "SBC / Revenue (latest)", "value": sbc_rev, "source": "key-metrics"})

    # =========================================================================
    # Layer 3 — Structural Health
    # =========================================================================
    structural_checks = []
    struct_notes      = []
    structural_yearly = []

    for i in range(n):
        km_row  = key_metrics[i]
        inc_row = income[i]
        bs_row  = balance[i]
        year    = _year_from_row(km_row) or _year_from_row(inc_row)

        roic         = _safe(km_row.get("returnOnInvestedCapital") or km_row.get("roic"))
        gross_margin = _safe(km_row.get("grossProfitMargin") or km_row.get("grossMargin"))
        op_margin    = _safe(km_row.get("operatingProfitMargin") or km_row.get("operatingMargin"))

        interest  = abs(_safe(inc_row.get("interestExpense") or 0) or 0)
        lt_debt   = _safe(bs_row.get("longTermDebt") or 0) or 0
        st_debt   = _safe(bs_row.get("shortTermDebt") or 0) or 0
        total_debt = lt_debt + st_debt
        cost_of_debt = (interest / total_debt) if (total_debt and interest) else None
        roic_spread  = (roic - cost_of_debt) if (roic is not None and cost_of_debt is not None) else None

        spread_flag = (roic_spread < 0) if roic_spread is not None else None

        structural_yearly.append({
            "year":          year,
            "roic":          roic,
            "gross_margin":  gross_margin,
            "op_margin":     op_margin,
            "cost_of_debt":  cost_of_debt,
            "roic_spread":   roic_spread,
            "is_red_flag":   spread_flag is True,
        })

    # Summary checks from latest
    roic_latest = _safe(km.get("returnOnInvestedCapital") or km.get("roic"))
    if roic_latest is not None:
        structural_checks.append({"metric": "ROIC (latest)", "value": roic_latest, "source": "key-metrics"})

    gm_latest = _safe(km.get("grossProfitMargin") or km.get("grossMargin"))
    if gm_latest is not None:
        structural_checks.append({"metric": "Gross Margin (latest)", "value": gm_latest, "source": "key-metrics"})

    om_latest = _safe(km.get("operatingProfitMargin") or km.get("operatingMargin"))
    if om_latest is not None:
        structural_checks.append({"metric": "Operating Margin (latest)", "value": om_latest, "source": "key-metrics"})

    # Flag years with negative economic spread
    neg_spread_years = [r["year"] for r in structural_yearly if r["roic_spread"] is not None and r["roic_spread"] < 0]
    if neg_spread_years:
        struct_notes.append(f"Negative ROIC-vs-cost-of-debt spread in: {', '.join(neg_spread_years)}")

    # =========================================================================
    # Layer 4 — Valuation
    # =========================================================================
    valuation_checks = []
    val_notes        = []
    valuation_yearly = []

    for i in range(n):
        km_row  = key_metrics[i]
        inc_row = income[i]
        year    = _year_from_row(km_row) or _year_from_row(inc_row)

        fcf_yield     = _safe(km_row.get("freeCashFlowYield") or km_row.get("freeCashFlowYieldPercentage"))
        ev_ebitda     = _safe(km_row.get("evToEbitda") or km_row.get("evToEbitdaRatio"))
        earnings_yield = _safe(km_row.get("earningsYield"))
        eps_growth    = _safe(km_row.get("epsDilutedGrowth") or km_row.get("epsGrowth") or km_row.get("earningsPerShareGrowth"))
        pe = (1.0 / earnings_yield) if (earnings_yield and earnings_yield != 0) else None
        peg = None
        if pe and eps_growth and eps_growth != 0:
            try:
                peg = pe / (eps_growth * 100.0) if eps_growth < 1 else pe / eps_growth
            except Exception:
                pass

        fcf_pass = (fcf_yield >= 0.03) if fcf_yield is not None else None

        valuation_yearly.append({
            "year":         year,
            "fcf_yield":    fcf_yield,
            "fcf_yield_pass": fcf_pass,
            "ev_ebitda":    ev_ebitda,
            "pe":           pe,
            "eps_growth":   eps_growth,
            "peg":          peg,
            "is_red_flag":  fcf_pass is False,
        })

    # Summary checks from latest
    fcf_yield_latest = _safe(km.get("freeCashFlowYield") or km.get("freeCashFlowYieldPercentage"))
    if fcf_yield_latest is not None:
        valuation_checks.append({"metric": "FCF Yield (latest)", "value": fcf_yield_latest, "rule_of_thumb": ">= 5% to Buy, < 3% is low", "source": "key-metrics"})
        if fcf_yield_latest < 0.03:
            val_notes.append(f"Low FCF yield: {fcf_yield_latest:.2%}")

    ev_ebitda_latest = _safe(km.get("evToEbitda") or km.get("evToEbitdaRatio"))
    if ev_ebitda_latest is not None:
        valuation_checks.append({"metric": "EV/EBITDA (latest)", "value": ev_ebitda_latest, "source": "key-metrics"})

    valuation_checks.append({"metric": "Reverse DCF", "value": None, "note": "Manual check recommended", "source": "derived"})

    # =========================================================================
    # Decision Logic
    # =========================================================================
    if not survival_pass:
        action = {
            "recommendation": "Avoid",
            "reason": "Failed survival filter",
            "size_note": "No exposure / reduce if owned"
        }
    elif earnings_notes or struct_notes:
        action = {
            "recommendation": "Watch",
            "reason": "Earnings or structural issues present",
            "size_note": "Small position or monitor closely"
        }
    else:
        if fcf_yield_latest and fcf_yield_latest >= 0.05:
            action = {
                "recommendation": "Buy",
                "reason": "Passes all filters with attractive FCF yield",
                "size_note": "Consider initial position sizing"
            }
        else:
            action = {
                "recommendation": "Watch",
                "reason": "Passes filters but valuation not yet compelling",
                "size_note": "Monitor for better entry point"
            }

    return {
        "ticker": symbol,
        "survival_filter": {
            "pass":        survival_pass,
            "checks":      survival_checks,
            "top_reasons": survival_fail_reasons[:2],
            "yearly":      survival_yearly,
        },
        "earnings_quality": {
            "checks":    earnings_checks,
            "red_flags": earnings_notes,
            "yearly":    earnings_yearly,
        },
        "structural_health": {
            "checks": structural_checks,
            "notes":  struct_notes,
            "yearly": structural_yearly,
        },
        "valuation": {
            "checks": valuation_checks,
            "notes":  val_notes,
            "yearly": valuation_yearly,
        },
        "thesis":               [],
        "invalidate_conditions": [],
        "action":               action,
        "raw_key_metrics_row":  km,
    }
