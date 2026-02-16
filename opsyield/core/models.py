from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Any, List

@dataclass
class NormalizedCost:
    """
    Unified Billing Normalization Object.
    All analytics, scoring, forecasting, and policies must operate on this structure.
    """
    provider: str
    service: str
    region: str
    resource_id: str
    cost: float
    currency: str
    timestamp: datetime
    team: Optional[str] = None
    business_unit: Optional[str] = None
    environment: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class Resource:
    id: str
    name: str
    type: str
    provider: str
    region: Optional[str] = None
    creation_date: Optional[datetime] = None

@dataclass
class AnalysisResult:
    meta: Dict[str, str]
    summary: Dict[str, Any]
    executive_summary: Dict[str, Any]
    trends: Any # Summary dict from AnalyticsEngine
    daily_trends: List[Dict[str, Any]] # Raw daily breakdown for charts
    anomalies: List[Dict]
    forecast: Dict
    governance_issues: List[Dict]
    optimizations: List[Dict]
    resources: List[Resource]
