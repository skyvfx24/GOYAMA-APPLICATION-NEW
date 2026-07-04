import sys
from pathlib import Path
# Dynamically add the workspace root to sys.path so we can import mfrecon cleanly
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


import time
import uuid
import traceback
from datetime import datetime, UTC
from typing import Dict, Any, Optional
from loguru import logger

from mfrecon import ReconciliationEngine, EngineConfig, load_config
from backend.config.settings import settings
from backend.services.file_manager import file_manager
from backend.services.result_serializer import result_serializer
from backend.services.run_history_store import run_history_store

# In-memory job store
jobs: Dict[str, Dict[str, Any]] = {}

class EngineRunner:
    """Orchestrates job execution in background tasks and manages the job store."""

    @staticmethod
    def get_job(job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a job record from the in-memory store."""
        return jobs.get(job_id)

    @classmethod
    def run_reconciliation_job(
        cls,
        job_id: str,
        crm_id: str,
        report_ids: list[str],
        config_id: Optional[str] = None
    ) -> None:
        """Runs the E2E reconciliation engine inside a background task."""
        job = jobs[job_id]
        
        try:
            # Stage 0: CRM Uploaded
            job["pipeline_stage"] = 0
            job["progress"] = "Locating uploaded files..."
            time.sleep(0.3)
            
            crm_path = file_manager.get_file_path(crm_id)
            if not crm_path:
                raise ValueError("CRM Master file could not be found.")
                
            report_paths = []
            for r_id in report_ids:
                r_path = file_manager.get_file_path(r_id)
                if r_path:
                    report_paths.append(r_path)
                    
            if not report_paths:
                raise ValueError("No valid report files found.")
                
            # Stage 1: Reports Uploaded
            job["pipeline_stage"] = 1
            job["progress"] = "Parsing and validating configuration..."
            time.sleep(0.3)
            
            # Resolve Engine Config
            config = None
            if config_id:
                config_path = file_manager.get_file_path(config_id)
                if config_path:
                    try:
                        config = load_config(config_path)
                        logger.info(f"Loaded custom config from {config_path}")
                    except Exception as e:
                        logger.error(f"Failed to load custom config: {e}. Falling back to default.")
            
            if config is None:
                if settings.DEFAULT_CONFIG_PATH.exists():
                    try:
                        config = load_config(settings.DEFAULT_CONFIG_PATH)
                        logger.info("Loaded default config from file.")
                    except Exception as e:
                        logger.error(f"Failed to load default config: {e}. Initializing standard defaults.")
                        config = EngineConfig()
                else:
                    config = EngineConfig()
            
            # Set the engine output directory to this specific job's folder
            job_output_dir = settings.TEMP_DIR / job_id / "output"
            job_output_dir.mkdir(parents=True, exist_ok=True)
            config.output_directory = job_output_dir
            
            # Stage 2: Validation
            job["pipeline_stage"] = 2
            job["progress"] = "Initializing Reconciliation Engine..."
            time.sleep(0.3)
            
            engine = ReconciliationEngine(config)
            
            # Stage 3: Reconciliation
            job["pipeline_stage"] = 3
            job["status"] = "running"
            job["progress"] = "Running core matching and discrepancy checks..."
            
            # Run engine
            start_time = time.perf_counter()
            result = engine.run(crm_path, report_paths)
            end_time = time.perf_counter()
            
            duration = end_time - start_time
            logger.info(f"Engine reconciliation complete in {duration:.2f} seconds.")
            
            # Stage 4: Report Generation
            job["pipeline_stage"] = 4
            job["progress"] = "Writing final discrepancy reports..."
            time.sleep(0.3)
            
            # Serialize the result
            serialized_result = result_serializer.serialize(job_id, result)
            
            # Update output file paths inside job record for download
            job["output_paths"] = {
                "excel": result.excel_report_path,
                "csv": result.csv_report_path,
                "json": result.json_report_path
            }
            
            # Persist run to history
            run_id = run_history_store.save_run(
                result_data=serialized_result,
                crm_filename=crm_path.name,
                report_count=len(report_paths)
            )
            
            # Update health statistics
            cls._update_health_metrics(duration)
            
            # Complete the job
            job["status"] = "done"
            job["progress"] = "Reconciliation completed successfully."
            job["result"] = serialized_result
            
        except Exception as e:
            logger.error(f"Reconciliation job {job_id} failed: {e}")
            traceback.print_exc()
            job["status"] = "error"
            job["progress"] = "Reconciliation execution failed."
            job["error"] = str(e)

    @staticmethod
    def _update_health_metrics(duration: float) -> None:
        """Helper to cache metadata of the last execution for the system health checks."""
        # We store these temporarily in an in-memory dictionary or file. 
        # For simplicity, we write them to a small cache file or global variables.
        global last_run_duration, last_successful_run
        last_run_duration = duration
        last_successful_run = datetime.now(UTC).isoformat().replace("+00:00", "Z")

# Global health cache variables
last_run_duration: Optional[float] = None
last_successful_run: Optional[str] = None

# Export instance of EngineRunner
engine_runner = EngineRunner()

