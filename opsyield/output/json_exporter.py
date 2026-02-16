
import json
from dataclasses import asdict
from ..core.models import AnalysisResult

def export_json(result: AnalysisResult, filepath: str):
    with open(filepath, 'w') as f:
        # crude serialization
        data = asdict(result)
        # handle date serialization if needed
        json.dump(data, f, indent=2, default=str)
