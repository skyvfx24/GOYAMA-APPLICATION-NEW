import uuid
from datetime import datetime, UTC
from fastapi import APIRouter, BackgroundTasks, HTTPException
from backend.services.engine_runner import engine_runner, jobs
from backend.models.request_models import ReconciliationRunRequest
from backend.models.response_models import JobStatusResponse

router = APIRouter(prefix="/api/reconciliation", tags=["Reconciliation"])

@router.post("/run", status_code=202)
async def trigger_reconciliation(
    request: ReconciliationRunRequest,
    background_tasks: BackgroundTasks
):
    """Triggers the E2E reconciliation engine in the background."""
    job_id = str(uuid.uuid4())
    
    # Initialize job in store
    jobs[job_id] = {
        "status": "pending",
        "progress": "Queued reconciliation job...",
        "pipeline_stage": 0,
        "result": None,
        "error": None,
        "created_at": datetime.now(UTC),
        "output_paths": {},
        "crm_id": request.crm_id,
        "report_ids": request.report_ids,
        "config_id": request.config_id
    }
    
    # Enqueue background execution task
    background_tasks.add_task(
        engine_runner.run_reconciliation_job,
        job_id=job_id,
        crm_id=request.crm_id,
        report_ids=request.report_ids,
        config_id=request.config_id
    )
    
    return {"job_id": job_id}

@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Polls the execution status and active stage of a run."""
    job = engine_runner.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        pipeline_stage=job["pipeline_stage"],
        error=job["error"],
        created_at=job["created_at"]
    )

@router.get("/{job_id}/result")
async def get_job_result(job_id: str):
    """Retrieves the full serialized result list and metrics for a completed run."""
    job = engine_runner.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job["status"] == "error":
        raise HTTPException(status_code=500, detail=f"Job failed with error: {job['error']}")
        
    if job["status"] != "done":
        raise HTTPException(status_code=400, detail="Job is not completed yet")
        
    return job["result"]
