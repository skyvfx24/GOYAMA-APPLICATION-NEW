from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime

class UploadResponse(BaseModel):
    file_id: str
    filename: str
    source_type: str  # CRM, CAMS, KFINTECH, BSE, NSE, PDF_CAS, CONFIG

class MultiUploadResponse(BaseModel):
    uploaded_files: List[UploadResponse]

class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # pending | running | done | error
    progress: str
    pipeline_stage: int  # 0-4
    error: Optional[str] = None
    created_at: datetime

class EngineHealthResponse(BaseModel):
    engine_version: str
    status: str  # ready | degraded | error
    tests_passed: int
    last_run_duration_seconds: Optional[float] = None
    last_successful_run: Optional[str] = None

class HistoryRunSummary(BaseModel):
    run_id: str
    timestamp: str
    crm_filename: str
    report_count: int
    match_rate_percent: float
    discrepancy_count: int
    status: str  # success | failed | partial
