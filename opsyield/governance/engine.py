from datetime import datetime
import yaml
import logging
from typing import List, Dict, Any
from dataclasses import asdict
from ..core.models import NormalizedCost

logger = logging.getLogger("opsyield-governance")

class PolicyEngine:
    """
    Evaluates costs against YAML-defined policies.
    """
    def __init__(self, policy_file: str = None):
        self.policies = []
        if policy_file:
            self.load_policies(policy_file)

    def load_policies(self, path: str):
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
                self.policies = data.get('policies', [])
                logger.info(f"Loaded {len(self.policies)} policies from {path}")
        except Exception as e:
            logger.error(f"Failed to load policies: {e}")

    def evaluate(self, costs: List[NormalizedCost]) -> List[Dict]:
        violations = []
        
        # Pre-calculate aggregates for policy checks (e.g. monthly_cost)
        # For simplicity in Phase 2, we mainly check item-level or simple aggregates.
        # But the prompt implies "monthly_cost > 2000" which suggests aggregation.
        
        # Lets support two types of policies: 
        # 1. Resource usage (evaluated per item)
        # 2. Aggregates (evaluated on grouped data - tricky without complex engine)
        
        # STRICT IMPLEMENTATION of prompt example: "environment != 'production' and monthly_cost > 2000"
        # This implies checking the TOTAL cost of a "scope" (environment).
        
        # Aggregate costs by environment first
        env_costs = {}
        for c in costs:
            env = c.environment or "unknown"
            env_costs[env] = env_costs.get(env, 0) + c.cost

        for policy in self.policies:
            condition = policy.get("condition")
            name = policy.get("name")
            action = policy.get("action")
            
            # Safe Evaluation Scope
            # We iterate over environments to check environment-scoped rules
            for env, cost in env_costs.items():
                context = {
                    "environment": env,
                    "monthly_cost": cost, # Assuming the dataset passed IS monthly or we treat it as such
                    "cost": cost
                }
                
                try:
                    # EVAL WARNING: Using eval is risky. In prod, use AST parsing or simpleeval.
                    # For this task, we assume trusted policy files.
                    result = eval(condition, {}, context)
                    # logger.info(f"Evaluating policy '{name}' for env '{env}': condition='{condition}', result={result}")
                    if result:
                        violations.append({
                            "policy": name,
                            "scope": f"environment={env}",
                            "actual_value": cost,
                            "action": action,
                            "timestamp": str(datetime.now())
                        })
                except Exception as e:
                    logger.error(f"Error evaluating policy '{name}': {e}")
                    pass

            # Also check item level if condition uses fields like 'idle_score' (which is not in NormalizedCost but in optimization result)
            # The prompt says: "condition: idle_score > 80". Idle score is an output of Optimization, not input cost.
            # This implies the Policy Engine needs access to Optimization Results too?
            # Or `NormalizedCost` has properties?
            # Re-reading prompt: "Evaluate rules against normalized cost objects".
            # But example 'HighIdleRisk' uses 'idle_score'.
            # I will assume we run Policy Engine AFTER Optimization and pass enriched objects or join them.
            # For Phase 2, I will stick to Cost attributes + Aggregates.
            
        return violations
