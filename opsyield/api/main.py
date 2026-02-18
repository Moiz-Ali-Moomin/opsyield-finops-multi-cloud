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
async def aggregate(
    providers: str = Query(..., description="Comma-separated list of providers"), 
    days: int = 30,
    subscription_id: Optional[str] = None
):
    """
    Aggregate analysis across multiple providers.
    """

    try:
        provider_list = [p.strip() for p in providers.split(',')]
        logger.info(f"Aggregating providers: {provider_list}")
        orchestrator = Orchestrator()
        result = await orchestrator.aggregate_analysis(provider_list, days=days, subscription_id=subscription_id)
        logger.info(f"Orchestrator returned result type: {type(result)}")
        return adapt_analysis_result(result)
    except Exception as e:
        logger.error(f"Aggregation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analyze")
async def analyze_cost(
    provider: str, 
    days: int = 30, 
    project_id: Optional[str] = None,
    subscription_id: Optional[str] = None
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
            project_id=project_id,
            subscription_id=subscription_id
        )
        return adapt_analysis_result(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# ─── SPA Serving ──────────────────────────────────────────────────────────────
# Serve the React frontend if built and available in ../web/static

import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Determine path to static files (relative to this file)
# opsyield/api/main.py -> opsyield/web/static
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "web", "static")

if os.path.exists(STATIC_DIR):
    logger.info(f"Serving static files from {STATIC_DIR}")
    
    # Mount assets (JS/CSS)
    # Vite puts assets in /assets, so we mount it there.
    if os.path.exists(os.path.join(STATIC_DIR, "assets")):
        app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

    # Catch-all for SPA
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Allow API calls to pass through (though they should match above routes first)
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
             raise HTTPException(status_code=404, detail="Not Found")

        # Check if a specific file exists in static dir (e.g. favicon.ico, robots.txt)
        file_path = os.path.join(STATIC_DIR, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)

        # Fallback to index.html for client-side routing
        index_path = os.path.join(STATIC_DIR, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
            
        return {"message": "Frontend not found (index.html missing)"}
