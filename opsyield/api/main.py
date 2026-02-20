from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from datetime import datetime
import logging
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from ..core.orchestrator import Orchestrator
from ..providers.factory import ProviderFactory
from .adapters.analysis_adapter import adapt_analysis_result

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("opsyield-api")

from .auth import router as auth_router
from .cloud_accounts import router as cloud_router
from .cost import router as cost_router

app = FastAPI(title="OpsYield API", version="0.1.1")

app.include_router(auth_router)
app.include_router(cloud_router)
app.include_router(cost_router)

# ─── CORS Configuration ───────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for CLI/local usage safety
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── API Routes ───────────────────────────────────────────────────────────────

@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "0.1.1"}

@app.get("/api/cloud/status")
async def get_cloud_status():
    """
    Production-grade cloud status endpoint.
    """
    try:
        return await ProviderFactory.get_all_statuses()
    except Exception as e:
        logger.error(f"Failed to fetch cloud status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/aggregate")
async def aggregate(
    providers: str = Query(..., description="Comma-separated list of providers"), 
    days: int = 30,
    subscription_id: Optional[str] = None
):
    try:
        provider_list = [p.strip() for p in providers.split(',')]
        logger.info(f"Aggregating providers: {provider_list}")
        orchestrator = Orchestrator()
        result = await orchestrator.aggregate_analysis(provider_list, days=days, subscription_id=subscription_id)
        return adapt_analysis_result(result)
    except Exception as e:
        logger.error(f"Aggregation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analyze")
async def analyze_cost(
    provider: str, 
    days: int = 30, 
    project_id: Optional[str] = None,
    subscription_id: Optional[str] = None
):
    try:
        orchestrator = Orchestrator()
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

# ─── SPA Serving ──────────────────────────────────────────────────────────────
# Serve the React frontend if built and available in ../web/static or ./dist

# Determine path to static files
# Priority 1: dist folder in current working directory (npx opsyield behavior)
# Priority 2: ../web/static relative to this file (legacy)

CWD_DIST = os.path.join(os.getcwd(), "dist")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "web", "static")

SERVE_DIR = None
if os.path.exists(CWD_DIST):
    SERVE_DIR = CWD_DIST
elif os.path.exists(STATIC_DIR):
    SERVE_DIR = STATIC_DIR

if SERVE_DIR:
    logger.info(f"Serving static files from {SERVE_DIR}")
    
    # Mount assets if they exist
    if os.path.exists(os.path.join(SERVE_DIR, "assets")):
        app.mount("/assets", StaticFiles(directory=os.path.join(SERVE_DIR, "assets")), name="assets")

    # Catch-all for SPA
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Allow API calls to pass through (though they should match above routes 
        # first due to order definition)
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
             raise HTTPException(status_code=404, detail="Not Found")

        # Check if file exists
        file_path = os.path.join(SERVE_DIR, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)

        # Fallback to index.html
        index_path = os.path.join(SERVE_DIR, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
            
        return {"message": "Frontend not found (index.html missing)"}
