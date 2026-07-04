from fastapi import APIRouter, HTTPException
from typing import List
from backend.services.run_history_store import run_history_store
from backend.models.response_models import HistoryRunSummary

router = APIRouter(prefix="/api/runs", tags=["Run History"])

@router.get("", response_model=List[HistoryRunSummary])
async def list_runs():
    """Lists summaries of all previous completed reconciliation runs."""
    return run_history_store.list_runs()

@router.get("/{run_id}")
async def get_run_details(run_id: str):
    """Retrieves the full result payload for a historical run."""
    run_record = run_history_store.get_run(run_id)
    if not run_record:
        raise HTTPException(status_code=404, detail=f"Run history record {run_id} not found")
        
    return run_record["result"]
