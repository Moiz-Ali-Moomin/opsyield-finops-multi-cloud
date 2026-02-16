
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import date

@dataclass
class NormalizedCost:
    amount: float
    currency: str
    date: date
    service: str
    provider: str
    account: Optional[str] = None
    region: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    business_unit: Optional[str] = None

@dataclass
class Resource:
    id: str
    name: str
    type: str
    provider: str
    region: Optional[str] = None
    creation_date: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AnalysisResult:
    meta: Dict[str, Any]
    summary: Dict[str, Any]
    trends: List[NormalizedCost]
    anomalies: List[Any]
    forecast: List[Any]
    governance_issues: List[Any]
    resources: List[Resource]
