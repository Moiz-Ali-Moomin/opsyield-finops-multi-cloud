from fastapi import FastAPI, HTTPException, Query
from typing import Optional, List
from datetime import datetime
import logging

from ..core.orchestrator import Orchestrator
from ..providers.factory import ProviderFactory
from .adapters.analysis_adapter import adapt_analysis_result

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("opsyield-api")

app = FastAPI(title="OpsYield API", version="0.1.0")

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}

@app.get("/cloud/status")
async def get_cloud_status():
    """
    Production-grade cloud status endpoint.

    Returns structured per-provider status with debug info.
    Runs all provider checks concurrently via asyncio.gather().
    Cached for 60s to prevent repeated CLI calls.
    """
    try:
        return await ProviderFactory.get_all_statuses()
    except Exception as e:
        logger.error(f"Failed to fetch cloud status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/aggregate")
async def aggregate(providers: str = Query(..., description="Comma-separated list of providers"), days: int = 30):
    """
    Aggregate analysis across multiple providers.
    """

    try:
        provider_list = [p.strip() for p in providers.split(',')]
        logger.info(f"Aggregating providers: {provider_list}")
        orchestrator = Orchestrator()
        result = await orchestrator.aggregate_analysis(provider_list, days=days)
        logger.info(f"Orchestrator returned result type: {type(result)}")
        return adapt_analysis_result(result)
    except Exception as e:
        logger.error(f"Aggregation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analyze")
async def analyze_cost(
    provider: str, 
    days: int = 30, 
    project_id: Optional[str] = None
):
    """
    Analyze cost for a specific provider.
    Changed from POST to GET to match frontend contract.
    """
    try:
        orchestrator = Orchestrator()
        # Pass parameters to orchestrator
        result = await orchestrator.analyze(
            provider_name=provider,
            days=days,
            project_id=project_id
        )
        return adapt_analysis_result(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
