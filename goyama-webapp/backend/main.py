import sys
from pathlib import Path

# Add project root to sys.path so mfrecon is importable
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.routers import upload, reconciliation, reports, history, system, demo

app = FastAPI(
    title="Goyama Webapp API Wrapper",
    description="Thin wrapper over Mutual Fund Reconciliation Engine",
    version="2.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(upload.router)
app.include_router(reconciliation.router)
app.include_router(reports.router)
app.include_router(history.router)
app.include_router(system.router)
app.include_router(demo.router)

@app.on_event("startup")
def startup_event():
    logger.info("Starting up FastAPI wrapper for mfrecon...")
    try:
        # Pre-generate synthetic files on startup for seamless demo experience
        demo.ensure_demo_data_exists()
        logger.info("Startup complete: Synthetic files generated in demo_data/")
    except Exception as e:
        logger.error(f"Failed to generate demo data during startup: {e}")

# Serve static files in production if MFRECON_ASSET_DIR is set
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

asset_dir = os.environ.get("MFRECON_ASSET_DIR")
if asset_dir and os.path.exists(asset_dir):
    assets_path = os.path.join(asset_dir, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

    @app.get("/{fallback_path:path}")
    async def serve_frontend(fallback_path: str):
        if fallback_path:
            file_path = os.path.join(asset_dir, fallback_path)
            if os.path.isfile(file_path):
                return FileResponse(file_path)
        index_html = os.path.join(asset_dir, "index.html")
        return FileResponse(index_html)
else:
    @app.get("/")
    async def root():
        return {"message": "Mutual Fund Reconciliation Engine API is running"}
