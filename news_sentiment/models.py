"""
Pydantic data models for the news sentiment comparison tool.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class Headline(BaseModel):
    """Individual news headline with metadata."""
    title: str = Field(..., description="Headline title")
    description: Optional[str] = Field(None, description="Headline description/summary")
    url: HttpUrl = Field(..., description="Article URL")
    source: str = Field(..., description="News source name")
    source_id: str = Field(..., description="News source ID")
    published_at: datetime = Field(..., description="Publication timestamp")
    political_side: str = Field(..., description="'conservative' or 'liberal'")
    uplift_score: Optional[float] = Field(None, description="Sentiment uplift score (-5 to +5)")
    keyword_boost: float = Field(0.0, description="Additional boost from puff piece keywords")
    final_score: Optional[float] = Field(None, description="Final score after keyword boost")
    collected_at: datetime = Field(default_factory=datetime.utcnow, description="Collection timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            HttpUrl: str
        }


class MostUpliftingStory(BaseModel):
    """Most uplifting story for a given side and date."""
    title: str
    description: Optional[str]
    url: HttpUrl
    source: str
    uplift_score: float
    final_score: float
    published_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            HttpUrl: str
        }


class DailyComparison(BaseModel):
    """Daily aggregated comparison between conservative and liberal sources."""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    conservative: dict = Field(..., description="Conservative side statistics")
    liberal: dict = Field(..., description="Liberal side statistics")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SideStatistics(BaseModel):
    """Statistics for one political side."""
    avg_uplift: float = Field(..., description="Average uplift score")
    positive_percentage: float = Field(..., description="Percentage of headlines with score > 0")
    total_headlines: int = Field(..., description="Total number of headlines")
    most_uplifting: Optional[MostUpliftingStory] = Field(None, description="Most uplifting story")
    score_distribution: dict[str, int] = Field(
        default_factory=dict,
        description="Count of headlines by score range"
    )


class SourceConfig(BaseModel):
    """News source configuration."""
    source_id: str
    name: str
    political_side: str  # 'conservative' or 'liberal'
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
