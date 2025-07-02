"""Basic data models for trend information."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class TrendData:
    """Simple representation of a trending tech item."""
    
    title: str
    url: str
    source: str
    summary: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    scraped_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "summary": self.summary,
            "tags": self.tags,
            "scraped_at": self.scraped_at.isoformat()
        }


@dataclass
class TrendCollection:
    """Collection of trends."""
    
    trends: List[TrendData] = field(default_factory=list)
    source: str = ""
    scraped_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_trend(self, trend: TrendData) -> None:
        """Add a trend to the collection."""
        self.trends.append(trend)
    
    @property
    def total_count(self) -> int:
        """Get total number of trends."""
        return len(self.trends)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "trends": [trend.to_dict() for trend in self.trends],
            "source": self.source,
            "scraped_at": self.scraped_at.isoformat(),
            "total_count": self.total_count
        }