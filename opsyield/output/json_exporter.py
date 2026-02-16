from dataclasses import asdict
from typing import List, Dict
from ..core.models import NormalizedCost

def serialize_costs(costs: List[NormalizedCost]) -> List[dict]:
    return [asdict(c) for c in costs]

def serialize_optimization_results(optimizations: List[Dict]):
    # Already dicts, but good for validation/transform if needed
    return optimizations

def export_json(result: dict, filepath: str):
    # Implementation for exporting JSON to a file
    pass
