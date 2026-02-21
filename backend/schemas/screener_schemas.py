"""
Pydantic Schemas for Stock Screener API

Defines request and response models for screener endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ============================================================================
# Batch Screening Request/Status
# ============================================================================

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
    status: str  # running, completed, failed, stopped
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
    """Response for a flagged company record"""
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


# ============================================================================
# Stock Universe
# ============================================================================

class StockUniverseUpdate(BaseModel):
    """Result of stock universe update"""
    total_stocks: int
    new_stocks: int
    updated_stocks: int
    updated_at: datetime


# ============================================================================
# Layered Screener Result (FMP key-metrics driven)
# ============================================================================

class LayerResult(BaseModel):
    """Result for a single screening layer"""
    checks: List[Dict[str, Any]] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
    top_reasons: Optional[List[str]] = None
    yearly: List[Dict[str, Any]] = Field(default_factory=list, description="Per-fiscal-year breakdown rows (newest → oldest)")


class LayeredScreenerResult(BaseModel):
    """Full 4-layer FMP screener result"""
    ticker: str
    survival_filter: LayerResult
    earnings_quality: LayerResult
    structural_health: LayerResult
    valuation: LayerResult
    thesis: List[str] = Field(default_factory=list)
    invalidate_conditions: List[str] = Field(default_factory=list)
    action: Dict[str, Any]
    raw_key_metrics_row: Optional[Dict[str, Any]] = None
