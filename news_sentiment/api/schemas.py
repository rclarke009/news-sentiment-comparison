"""
API request/response schemas.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl


class MostUpliftingResponse(BaseModel):
    """Response schema for most uplifting story."""
    title: str
    description: Optional[str]
    url: str
    source: str
    uplift_score: float
    final_score: float
    published_at: str
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SideStatsResponse(BaseModel):
    """Response schema for side statistics."""
    avg_uplift: float
    positive_percentage: float
    total_headlines: int
    most_uplifting: Optional[MostUpliftingResponse]
    score_distribution: dict[str, int]


class DailyComparisonResponse(BaseModel):
    """Response schema for daily comparison."""
    date: str
    conservative: SideStatsResponse
    liberal: SideStatsResponse
    created_at: str
    updated_at: str


class HistoryResponse(BaseModel):
    """Response schema for historical data."""
    comparisons: list[DailyComparisonResponse]
    days: int


class StatsResponse(BaseModel):
    """Response schema for aggregate statistics."""
    total_days: int
    conservative_avg: float
    liberal_avg: float
    conservative_positive_pct: float
    liberal_positive_pct: float


class SourcesResponse(BaseModel):
    """Response schema for configured news sources (display names only)."""
    conservative: list[str]
    liberal: list[str]
