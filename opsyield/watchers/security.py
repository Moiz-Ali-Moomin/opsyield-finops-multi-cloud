from typing import List, Dict, Any
from .base import BaseWatcher
from ..core.models import Resource, NormalizedCost

class SecurityWatcher(BaseWatcher):
    def watch(self, resources: List[Resource], costs: List[NormalizedCost]) -> List[Dict[str, Any]]:
        findings = []
        
        for r in resources:
            # 1. Public IP on Database?
            if "sql" in r.type.lower() or "rds" in r.type.lower():
                if r.external_ip:
                    findings.append({
                        "type": "security_risk",
                        "subtype": "public_database",
                        "resource_id": r.id,
                        "severity": "critical",
                        "details": "Database has external IP exposed."
                    })
            
            # 2. Public S3 Buckets? 
            # (Requires deeper inspection which we might not have yet, but if tags say 'Public'...)
            
            # 3. Legacy instance types?
            if r.class_type and "t1." in r.class_type:
                 findings.append({
                    "type": "security_risk",
                    "subtype": "legacy_instance",
                    "resource_id": r.id,
                    "severity": "low",
                    "details": "Using old generation instance type."
                })

        return findings
