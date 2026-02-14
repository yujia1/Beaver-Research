"""
Pydantic Schemas for Stock Screener API

Defines request and response models for screener endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ============================================================================
# Trend and Metric Schemas
# ============================================================================

class TrendData(BaseModel):
    """Trend analysis data"""
    values: List[float] = Field(description="Historical values (oldest to newest)")
    years: List[int] = Field(description="Fiscal years")
    slope: float = Field(description="Linear regression slope")
    direction: str = Field(description="Trend direction: improving, declining, stable")
    latest_value: float = Field(description="Most recent value")


class MetricData(BaseModel):
    """Single metric calculation result"""
    name: str = Field(description="Metric name")
    latest_value: Optional[float] = Field(description="Most recent value")
    trend: Optional[TrendData] = Field(description="5-year trend analysis")
    is_red_flag: bool = Field(description="Whether this metric triggers a red flag")
    red_flag_reason: Optional[str] = Field(description="Reason for red flag")


class RedFlagSummary(BaseModel):
    """Summary of red flags for a stock"""
    has_red_flags: bool
    red_flag_count: int
    red_flags: List[Dict[str, Any]]
    strategies_flagged: List[str]


# ============================================================================
# Stock Metrics Response
# ============================================================================

class StockMetrics(BaseModel):
    """All screening metrics for a single stock"""
    ticker: str
    company_name: Optional[str] = None
    
    # Metrics
    fcf_to_dividends_buybacks: Optional[MetricData] = None
    fcf_to_revenue: Optional[MetricData] = None
    net_debt_to_ebitda: Optional[MetricData] = None
    capitalized_costs_to_revenue: Optional[MetricData] = None
    days_sales_outstanding: Optional[MetricData] = None
    ev_to_ebitda: Optional[MetricData] = None
    
    # Red flag summary
    red_flag_summary: Optional[RedFlagSummary] = None
    
    # Metadata
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    data_years: int = Field(default=5, description="Number of years of data used")


# ============================================================================
# Screening Request/Response
# ============================================================================

class ScreenerCriteria(BaseModel):
    """Criteria for screening stocks"""
    tickers: List[str] = Field(description="List of stock tickers to screen")
    strategies: List[str] = Field(
        default=["all"],
        description="Strategies to apply: 'all', 'cash_flow', 'balance_sheet', 'working_capital', 'valuation'"
    )
    years: int = Field(default=5, description="Number of years of historical data")
    
    class Config:
        schema_extra = {
            "example": {
                "tickers": ["AAPL", "MSFT", "GOOGL"],
                "strategies": ["all"],
                "years": 5
            }
        }


class ScreenerResult(BaseModel):
    """Result of screening operation"""
    ticker: str
    company_name: Optional[str] = None
    metrics: Dict[str, MetricData]
    red_flag_summary: RedFlagSummary
    screened_at: datetime = Field(default_factory=datetime.utcnow)


class BatchScreenRequest(BaseModel):
    """Request to trigger batch screening"""
    strategies: List[str] = Field(
        default=["all"],
        description="Strategies to run"
    )
    batch_size: int = Field(
        default=5,
        description="Number of stocks to process per batch"
    )
    delay_seconds: int = Field(
        default=60,
        description="Delay between batches in seconds"
    )
    limit: Optional[int] = Field(
        default=None,
        description="Limit total number of stocks (for testing)"
    )
    enable_peer_comparison: bool = Field(
        default=False,
        description="Enable peer comparison (slower)"
    )
    force_refresh: bool = Field(
        default=False,
        description="Force refresh of stock universe from FMP"
    )


class BatchScreenStatus(BaseModel):
    """Status of batch screening job"""
    run_id: int
    status: str  # running, completed, failed
    total_stocks: int
    processed_stocks: int
    flagged_stocks: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    error_message: Optional[str] = None


# ============================================================================
# Flagged Companies
# ============================================================================

class FlaggedCompanyResponse(BaseModel):
    """Response for flagged company"""
    id: int
    ticker: str
    company_name: Optional[str]
    sector: Optional[str]
    screening_date: datetime
    strategies_flagged: List[str]
    metrics: Dict[str, Any]
    red_flags: List[Dict[str, Any]]
    
    class Config:
        from_attributes = True


class FlaggedCompaniesFilter(BaseModel):
    """Filter criteria for flagged companies"""
    strategy: Optional[str] = Field(
        default=None,
        description="Filter by strategy: 'cash_flow', 'balance_sheet', 'working_capital', 'valuation'"
    )
    limit: int = Field(default=100, le=1000, description="Maximum number of results")
    offset: int = Field(default=0, description="Offset for pagination")
    sort_by: str = Field(default="red_flag_count", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order: asc or desc")


# ============================================================================
# Peer Comparison
# ============================================================================

class PeerComparisonRequest(BaseModel):
    """Request for peer comparison"""
    ticker: str = Field(description="Target stock ticker")
    peer_tickers: List[str] = Field(description="List of peer stock tickers")
    metric: str = Field(
        default="ev_to_ebitda",
        description="Metric to compare: 'ev_to_ebitda', 'net_debt_to_ebitda', etc."
    )


class PeerComparisonResult(BaseModel):
    """Result of peer comparison"""
    ticker: str
    metric_name: str
    ticker_value: float
    peer_values: Dict[str, float]
    peer_average: float
    peer_median: float
    deviation_from_average: float  # Percentage
    deviation_from_median: float  # Percentage
    is_outlier: bool
    interpretation: str


# ============================================================================
# Stock Universe
# ============================================================================

class StockUniverseItem(BaseModel):
    """Single stock in universe"""
    ticker: str
    company_name: Optional[str]
    exchange: Optional[str]
    sector: Optional[str]
    industry: Optional[str]
    market_cap: Optional[int]
    is_active: bool
    
    class Config:
        from_attributes = True


class StockUniverseUpdate(BaseModel):
    """Result of stock universe update"""
    total_stocks: int
    new_stocks: int
    updated_stocks: int
    updated_at: datetime
