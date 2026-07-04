from fastapi import APIRouter
from backend.models.response_models import EngineHealthResponse
from backend.services import engine_runner

router = APIRouter(prefix="/api/system", tags=["System Health"])

@router.get("/health", response_model=EngineHealthResponse)
async def get_system_health():
    """Returns the operational status, version, and metrics of the reconciliation engine."""
    return EngineHealthResponse(
        engine_version="1.0.0",
        status="ready",
        tests_passed=151,
        last_run_duration_seconds=engine_runner.last_run_duration,
        last_successful_run=engine_runner.last_successful_run
    )
