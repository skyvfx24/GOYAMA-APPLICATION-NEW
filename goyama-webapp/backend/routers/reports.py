from pathlib import Path
import copy
import zipfile
import tempfile
import shutil
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from backend.services.engine_runner import engine_runner
from backend.services.file_manager import file_manager
from backend.config import settings
from mfrecon.core.config import EngineConfig, load_config
from mfrecon.facade import ReconciliationEngine
from mfrecon.reporters.excel import ExcelReporter
from mfrecon.core.domain import CRMRecord, ReportRecord, Discrepancy

logger = logging.getLogger("mfrecon.reports_router")

router = APIRouter(prefix="/api/reports", tags=["Reports"])

@router.get("/{job_id}/excel")
async def get_excel_report(job_id: str):
    """Streams the Excel spreadsheet workbook for a completed run."""
    job = engine_runner.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    excel_path = job.get("output_paths", {}).get("excel")
    if not excel_path or not Path(excel_path).exists():
        raise HTTPException(status_code=404, detail="Excel report file not found on disk")
        
    filename = Path(excel_path).name
    return FileResponse(
        path=excel_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@router.get("/{job_id}/csv")
async def get_csv_report(job_id: str):
    """Streams the flat CSV database file for a completed run."""
    job = engine_runner.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    csv_path = job.get("output_paths", {}).get("csv")
    if not csv_path or not Path(csv_path).exists():
        raise HTTPException(status_code=404, detail="CSV report file not found on disk")
        
    filename = Path(csv_path).name
    return FileResponse(
        path=csv_path,
        filename=filename,
        media_type="text/csv"
    )

@router.get("/{job_id}/json")
async def get_json_report(job_id: str):
    """Streams the structured JSON file download for a completed run."""
    job = engine_runner.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    json_path = job.get("output_paths", {}).get("json")
    if not json_path or not Path(json_path).exists():
        raise HTTPException(status_code=404, detail="JSON report file not found on disk")
        
    filename = Path(json_path).name
    return FileResponse(
        path=json_path,
        filename=filename,
        media_type="application/json"
    )


def cleanup_temp_dir(temp_dir: str):
    try:
        shutil.rmtree(temp_dir)
    except Exception:
        pass


def run_recon_for_job(job):
    crm_id = job.get("crm_id")
    report_ids = job.get("report_ids")
    config_id = job.get("config_id")
    
    if not crm_id or not report_ids:
        raise HTTPException(status_code=400, detail="Missing source files in job metadata")
        
    crm_path = file_manager.get_file_path(crm_id)
    if not crm_path:
        raise HTTPException(status_code=404, detail="CRM Master file not found")
        
    report_paths = []
    for r_id in report_ids:
        r_path = file_manager.get_file_path(r_id)
        if r_path:
            report_paths.append(r_path)
            
    if not report_paths:
        raise HTTPException(status_code=404, detail="No valid report files found")
        
    # Resolve config
    config = None
    if config_id:
        config_path = file_manager.get_file_path(config_id)
        if config_path:
            try:
                config = load_config(config_path)
            except Exception:
                pass
    if config is None:
        if settings.DEFAULT_CONFIG_PATH.exists():
            try:
                config = load_config(settings.DEFAULT_CONFIG_PATH)
            except Exception:
                config = EngineConfig()
        else:
            config = EngineConfig()
            
    # Set output dir
    temp_output_dir = Path(tempfile.mkdtemp())
    config.output_directory = temp_output_dir
    
    engine = ReconciliationEngine(config)
    result = engine.run(crm_path, report_paths)
    
    return engine, result, crm_path, temp_output_dir


class FilteredCoreResult:
    def __init__(self, matched_records, unmatched_records):
        self.matched_records = matched_records
        self.unmatched_records = unmatched_records


def generate_client_workbook(engine, result, crm_path, pan, temp_dir):
    # Filter discrepancies
    filtered_discrepancies = [d for d in result.discrepancies if d.pan == pan]
    filtered_matched_audits = [a for a in result.matched_audits if a.pan == pan]
    
    core_result = getattr(engine, "last_recon_result", None)
    filtered_matched_records = []
    filtered_unmatched_records = []
    if core_result:
        if hasattr(core_result, "matched_records") and core_result.matched_records:
            filtered_matched_records = [(crm, rep) for crm, rep in core_result.matched_records if crm.pan == pan]
        if hasattr(core_result, "unmatched_records") and core_result.unmatched_records:
            filtered_unmatched_records = [rec for rec in core_result.unmatched_records if rec.pan == pan]
            
    # Filter validation failures
    validation_failures = getattr(engine, "last_validation_failures", []) or []
    filtered_validation_failures = []
    for f in validation_failures:
        raw_data = f.get("raw_data") or {}
        pan_val = (raw_data.get('pan') or raw_data.get('PAN') or raw_data.get('BSE_PAN') or raw_data.get('nse_pan') or raw_data.get('PAN_NO') or '').strip().upper()
        if pan_val == pan:
            filtered_validation_failures.append(f)
            
    # Create filtered result object
    filtered_result = copy.deepcopy(result)
    filtered_result.discrepancies = filtered_discrepancies
    filtered_result.matched_audits = filtered_matched_audits
    
    # Generate client workbook
    excel_reporter = ExcelReporter(output_dir=temp_dir, run_id=engine.run_id)
    client_file_path = temp_dir / f"{pan}_reconciliation.xlsx"
    excel_reporter.report(
        result=filtered_result,
        core_result=FilteredCoreResult(filtered_matched_records, filtered_unmatched_records),
        all_validation_failures=filtered_validation_failures,
        file_path=client_file_path,
        crm_path=crm_path
    )
    return client_file_path


@router.get("/{job_id}/excel/client/{pan}")
async def get_client_excel_report(job_id: str, pan: str, background_tasks: BackgroundTasks):
    """Generates and streams the Excel spreadsheet workbook for a single client (filtered by PAN)."""
    job = engine_runner.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    engine, result, crm_path, temp_dir = run_recon_for_job(job)
    
    # Check if this PAN actually has records in this job
    has_records = False
    core_result = getattr(engine, "last_recon_result", None)
    if core_result:
        if any(crm.pan == pan for crm, rep in getattr(core_result, "matched_records", []) or []):
            has_records = True
        elif any(rec.pan == pan for rec in getattr(core_result, "unmatched_records", []) or []):
            has_records = True
    if not has_records and any(d.pan == pan for d in result.discrepancies):
        has_records = True
        
    if not has_records:
        shutil.rmtree(temp_dir)
        raise HTTPException(status_code=404, detail=f"No reconciliation records found for PAN {pan}")
        
    try:
        # Determine name
        client_name = "Client"
        core_result = getattr(engine, "last_recon_result", None)
        if core_result:
            matched_recs = getattr(core_result, "matched_records", []) or []
            unmatched_recs = getattr(core_result, "unmatched_records", []) or []
            filtered_matched = [crm for crm, rep in matched_recs if crm.pan == pan]
            filtered_unmatched = [rec for rec in unmatched_recs if rec.pan == pan]
            if filtered_matched:
                client_name = filtered_matched[0].investor_name
            elif filtered_unmatched:
                client_name = filtered_unmatched[0].investor_name
                
        client_name_clean = "".join(c for c in client_name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        filename = f"{client_name_clean}_Reconciliation_Report.xlsx"
        
        client_file_path = generate_client_workbook(engine, result, crm_path, pan, temp_dir)
        
        background_tasks.add_task(cleanup_temp_dir, str(temp_dir))
        
        return FileResponse(
            path=client_file_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        shutil.rmtree(temp_dir)
        logger.error(f"Failed to generate client report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/excel/zip")
async def get_multiple_clients_excel_zip(job_id: str, pans: str, background_tasks: BackgroundTasks):
    """Generates Excel reports for multiple clients and returns them as a single ZIP file."""
    job = engine_runner.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    pan_list = [p.strip().upper() for p in pans.split(",") if p.strip()]
    if not pan_list:
        raise HTTPException(status_code=400, detail="No PANs specified")
        
    engine, result, crm_path, temp_dir = run_recon_for_job(job)
    
    try:
        zip_file_path = temp_dir / f"reconciliation_reports_{job_id}.zip"
        
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for pan in pan_list:
                # Check if client exists
                has_records = False
                core_result = getattr(engine, "last_recon_result", None)
                if core_result:
                    if any(crm.pan == pan for crm, rep in getattr(core_result, "matched_records", []) or []):
                        has_records = True
                    elif any(rec.pan == pan for rec in getattr(core_result, "unmatched_records", []) or []):
                        has_records = True
                if not has_records and any(d.pan == pan for d in result.discrepancies):
                    has_records = True
                    
                if not has_records:
                    continue
                    
                # Determine client name for file name
                client_name = "Client"
                if core_result:
                    matched_recs = getattr(core_result, "matched_records", []) or []
                    unmatched_recs = getattr(core_result, "unmatched_records", []) or []
                    filtered_matched = [crm for crm, rep in matched_recs if crm.pan == pan]
                    filtered_unmatched = [rec for rec in unmatched_recs if rec.pan == pan]
                    if filtered_matched:
                        client_name = filtered_matched[0].investor_name
                    elif filtered_unmatched:
                        client_name = filtered_unmatched[0].investor_name
                        
                client_name_clean = "".join(c for c in client_name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
                filename = f"{client_name_clean}_Reconciliation_Report.xlsx"
                
                # Generate client workbook file
                client_file_path = generate_client_workbook(engine, result, crm_path, pan, temp_dir)
                
                # Write to zip
                zip_file.write(client_file_path, arcname=filename)
                
        background_tasks.add_task(cleanup_temp_dir, str(temp_dir))
        
        return FileResponse(
            path=zip_file_path,
            filename=f"Reconciliation_Reports_{datetime.now().strftime('%Y%m%d')}.zip",
            media_type="application/zip"
        )
    except Exception as e:
        shutil.rmtree(temp_dir)
        logger.error(f"Failed to generate reports ZIP: {e}")
        raise HTTPException(status_code=500, detail=str(e))
