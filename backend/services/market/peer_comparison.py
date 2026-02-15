"""
Peer Comparison Service

Fetches peer companies and compares metrics for relative screening.
"""

import logging
from typing import List, Dict, Any, Optional
import statistics

from services.market.fmp_financial_service import (
    _make_fmp_request,
    fetch_all_financial_statements,
    FMPAPIError
)

logger = logging.getLogger(__name__)


def fetch_stock_peers(ticker: str) -> List[str]:
    """
    Fetch peer company tickers from FMP API
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        List of peer ticker symbols
    """
    try:
        endpoint = "stock-peers"
        params = {"symbol": ticker}
        
        data = _make_fmp_request(endpoint, params)
        
        # FMP returns list of peer data with 'symbol' field
        if isinstance(data, list) and len(data) > 0:
            # Extract symbols from peer data
            peers = [peer.get("symbol") for peer in data if peer.get("symbol")]
            logger.info(f"Found {len(peers)} peers for {ticker}: {peers}")
            return peers
        
        logger.warning(f"No peers found for {ticker}")
        return []
    
    except FMPAPIError as e:
        logger.error(f"Error fetching peers for {ticker}: {e}")
        return []


def calculate_peer_comparison(
    ticker: str,
    peer_tickers: List[str],
    metric_name: str,
    current_price: float = None
) -> Dict[str, Any]:
    """
    Calculate a metric for target stock and peers, then compare
    
    Args:
        ticker: Target stock ticker
        peer_tickers: List of peer tickers
        metric_name: Name of metric to compare (e.g., 'ev_to_ebitda', 'days_sales_outstanding')
        current_price: Current stock price (optional, for EV calculation)
    
    Returns:
        Dictionary with comparison results
    """
    peer_values = {}
    
    # Lazy import to avoid circular dependency
    from services.market.screener_calculator import calculate_all_metrics
    
    # Calculate metric for each peer
    for peer in peer_tickers:
        try:
            # Fetch financial data
            financial_data = fetch_all_financial_statements(peer, years=5)
            
            # Calculate metrics (without ticker to avoid recursive peer comparison)
            result = calculate_all_metrics(
                income_data=financial_data["income"],
                cash_flow_data=financial_data["cashflow"],
                balance_sheet_data=financial_data["balance"],
                current_price=current_price,
                ticker=None  # Don't pass ticker to avoid recursive peer comparison
            )
            metrics = result["metrics"]
            
            # Get the specific metric
            if metric_name in metrics and metrics[metric_name].latest_value is not None:
                peer_values[peer] = metrics[metric_name].latest_value
        
        except Exception as e:
            logger.error(f"Error calculating {metric_name} for peer {peer}: {e}")
            continue
    
    if not peer_values:
        return {
            "ticker": ticker,
            "metric_name": metric_name,
            "peer_count": 0,
            "peer_values": {},
            "peer_average": None,
            "peer_median": None,
            "error": "No peer data available"
        }
    
    # Calculate statistics
    values_list = list(peer_values.values())
    peer_average = statistics.mean(values_list)
    peer_median = statistics.median(values_list)
    peer_std_dev = statistics.stdev(values_list) if len(values_list) > 1 else 0
    
    return {
        "ticker": ticker,
        "metric_name": metric_name,
        "peer_count": len(peer_values),
        "peer_values": peer_values,
        "peer_average": peer_average,
        "peer_median": peer_median,
        "peer_std_dev": peer_std_dev,
        "peer_min": min(values_list),
        "peer_max": max(values_list)
    }


def check_peer_deviation(
    target_value: float,
    peer_comparison: Dict[str, Any],
    threshold_type: str = "multiplier",
    threshold_value: float = 2.0
) -> Dict[str, Any]:
    """
    Check if target value deviates significantly from peers
    
    Args:
        target_value: Target company's metric value
        peer_comparison: Peer comparison results from calculate_peer_comparison
        threshold_type: Type of threshold ('multiplier', 'std_dev', 'absolute')
        threshold_value: Threshold value (e.g., 2.0 for 2x multiplier, 2.0 for 2 std devs)
    
    Returns:
        Dictionary with deviation analysis and red flag status
    """
    if peer_comparison.get("peer_average") is None:
        return {
            "is_red_flag": False,
            "reason": "Insufficient peer data for comparison"
        }
    
    peer_avg = peer_comparison["peer_average"]
    peer_median = peer_comparison["peer_median"]
    peer_std_dev = peer_comparison.get("peer_std_dev", 0)
    
    # Calculate deviations
    deviation_from_avg = ((target_value - peer_avg) / peer_avg * 100) if peer_avg != 0 else 0
    deviation_from_median = ((target_value - peer_median) / peer_median * 100) if peer_median != 0 else 0
    
    # Check threshold based on type
    is_red_flag = False
    reason = None
    
    if threshold_type == "multiplier":
        # Check if target is > threshold_value times peer average
        multiplier = target_value / peer_avg if peer_avg != 0 else 0
        if multiplier > threshold_value:
            is_red_flag = True
            reason = f"Value {target_value:.2f} is {multiplier:.2f}x peer average ({peer_avg:.2f}), exceeds {threshold_value}x threshold"
        elif multiplier < (1 / threshold_value):
            is_red_flag = True
            reason = f"Value {target_value:.2f} is {multiplier:.2f}x peer average ({peer_avg:.2f}), below {1/threshold_value:.2f}x threshold"
    
    elif threshold_type == "std_dev":
        # Check if target is > threshold_value standard deviations from mean
        if peer_std_dev > 0:
            z_score = (target_value - peer_avg) / peer_std_dev
            if abs(z_score) > threshold_value:
                is_red_flag = True
                reason = f"Value {target_value:.2f} is {z_score:.2f} standard deviations from peer average ({peer_avg:.2f})"
    
    elif threshold_type == "absolute":
        # Check if absolute difference exceeds threshold
        absolute_diff = abs(target_value - peer_avg)
        if absolute_diff > threshold_value:
            is_red_flag = True
            reason = f"Value {target_value:.2f} differs from peer average ({peer_avg:.2f}) by {absolute_diff:.2f}, exceeds threshold {threshold_value}"
    
    return {
        "is_red_flag": is_red_flag,
        "reason": reason,
        "target_value": target_value,
        "peer_average": peer_avg,
        "peer_median": peer_median,
        "deviation_from_avg_pct": deviation_from_avg,
        "deviation_from_median_pct": deviation_from_median,
        "z_score": (target_value - peer_avg) / peer_std_dev if peer_std_dev > 0 else 0
    }


def compare_dso_to_peers(ticker: str, target_dso: float) -> Dict[str, Any]:
    """
    Compare DSO to peers with +20 days threshold
    
    Args:
        ticker: Target stock ticker
        target_dso: Target company's DSO value
    
    Returns:
        Comparison results with red flag status
    """
    # Fetch peers
    peers = fetch_stock_peers(ticker)
    
    if not peers:
        return {
            "is_red_flag": False,
            "reason": "No peers available for comparison"
        }
    
    # Calculate peer comparison
    peer_comparison = calculate_peer_comparison(
        ticker=ticker,
        peer_tickers=peers,
        metric_name="days_sales_outstanding"
    )
    
    # Check deviation with +20 days threshold
    result = check_peer_deviation(
        target_value=target_dso,
        peer_comparison=peer_comparison,
        threshold_type="absolute",
        threshold_value=20.0  # +/- 20 days
    )
    
    return result


def compare_ev_ebitda_to_peers(ticker: str, target_ev_ebitda: float) -> Dict[str, Any]:
    """
    Compare EV/EBITDA to peers with 2x multiplier threshold
    
    Args:
        ticker: Target stock ticker
        target_ev_ebitda: Target company's EV/EBITDA value
    
    Returns:
        Comparison results with red flag status
    """
    # Fetch peers
    peers = fetch_stock_peers(ticker)
    
    if not peers:
        return {
            "is_red_flag": False,
            "reason": "No peers available for comparison"
        }
    
    # Calculate peer comparison
    peer_comparison = calculate_peer_comparison(
        ticker=ticker,
        peer_tickers=peers,
        metric_name="ev_to_ebitda"
    )
    
    # Check deviation with 2x multiplier threshold
    result = check_peer_deviation(
        target_value=target_ev_ebitda,
        peer_comparison=peer_comparison,
        threshold_type="multiplier",
        threshold_value=2.0  # 2x peer average
    )
    
    return result


def compare_capitalized_costs_to_peers(ticker: str, target_ratio: float) -> Dict[str, Any]:
    """
    Compare Capitalized Costs/Revenue to peers with 2x multiplier threshold
    
    Args:
        ticker: Target stock ticker
        target_ratio: Target company's Capitalized Costs/Revenue ratio
    
    Returns:
        Comparison results with red flag status
    """
    # Fetch peers
    peers = fetch_stock_peers(ticker)
    
    if not peers:
        return {
            "is_red_flag": False,
            "reason": "No peers available for comparison"
        }
    
    # Calculate peer comparison
    peer_comparison = calculate_peer_comparison(
        ticker=ticker,
        peer_tickers=peers,
        metric_name="capitalized_costs_to_revenue"
    )
    
    # Check deviation with 2x multiplier threshold
    result = check_peer_deviation(
        target_value=target_ratio,
        peer_comparison=peer_comparison,
        threshold_type="multiplier",
        threshold_value=2.0  # 2x peer average
    )
    
    return result
