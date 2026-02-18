from typing import List, Dict, Any
from datetime import datetime
from .base import BaseWatcher
from ..core.models import Resource, NormalizedCost

class IdleWatcher(BaseWatcher):
    def watch(self, resources: List[Resource], costs: List[NormalizedCost]) -> List[Dict[str, Any]]:
        findings = []
        now = datetime.utcnow()
        
        for r in resources:
            score = 0
            reasons = []

            # 1. Low CPU Utilization
            if r.cpu_avg is not None and r.cpu_avg < 5.0:
                 score += 50
                 reasons.append(f"Low CPU: {r.cpu_avg}%")
            
            # 2. Unattached storage / Stopped instances
            state = (r.state or "").lower()
            if state in ["stopped", "terminated"]:
                 score += 30
                 reasons.append(f"Resource is {state}")

            # 3. Old and cheap/unused?
            # ... additional logic

            if score >= 50:
                findings.append({
                    "type": "idle_resource",
                    "resource_id": r.id,
                    "name": r.name,
                    "severity": "medium" if score < 80 else "high",
                    "score": score,
                    "reasons": reasons,
                    "cost_30d": r.cost_30d
                })
        return findings
