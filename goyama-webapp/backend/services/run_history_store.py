import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger
from datetime import datetime, UTC
from backend.config.settings import settings

class RunHistoryStore:
    """Manages persistence of reconciliation run executions as JSON files in run_history/."""

    @staticmethod
    def get_next_run_id() -> str:
        """Determines the next sequential run ID (e.g. RUN-001, RUN-002)."""
        history_dir = settings.RUN_HISTORY_DIR
        files = list(history_dir.glob("RUN-*.json"))
        max_idx = 0
        for f in files:
            name = f.stem  # e.g., RUN-001
            try:
                parts = name.split("-")
                if len(parts) == 2:
                    idx = int(parts[1])
                    if idx > max_idx:
                        max_idx = idx
            except (ValueError, IndexError):
                continue
        return f"RUN-{max_idx + 1:03d}"

    @classmethod
    def save_run(cls, result_data: Dict[str, Any], crm_filename: str, report_count: int) -> str:
        """Saves a completed run result to run_history/ and returns the generated run_id."""
        run_id = cls.get_next_run_id()
        
        # Inject run_id and metadata info into the result
        result_data["run_id"] = run_id
        
        summary = result_data.get("summary", {})
        match_rate = float(summary.get("match_rate_percent", 0.0))
        discrepancies_count = int(summary.get("discrepancy_count", 0))
        
        # Save a metadata header for fast listing
        run_record = {
            "run_id": run_id,
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "crm_filename": crm_filename,
            "report_count": report_count,
            "match_rate_percent": match_rate,
            "discrepancy_count": discrepancies_count,
            "status": "success" if result_data.get("status") == "done" else "failed",
            "result": result_data
        }
        
        filepath = settings.RUN_HISTORY_DIR / f"{run_id}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(run_record, f, indent=2)
            
        logger.info(f"Run saved to history: {filepath}")
        return run_id

    @staticmethod
    def list_runs() -> List[Dict[str, Any]]:
        """Returns the list of all historical runs (metadata only, excluding full results)."""
        history_dir = settings.RUN_HISTORY_DIR
        runs = []
        for filepath in sorted(history_dir.glob("RUN-*.json"), reverse=True):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Exclude the heavy result payload when listing
                    summary = {k: v for k, v in data.items() if k != "result"}
                    runs.append(summary)
            except Exception as e:
                logger.error(f"Error reading run file {filepath.name}: {e}")
        return runs

    @staticmethod
    def get_run(run_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves the full run details (including result payload) for a run_id."""
        filepath = settings.RUN_HISTORY_DIR / f"{run_id}.json"
        if not filepath.exists():
            return None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading run file {filepath.name}: {e}")
            return None

run_history_store = RunHistoryStore()
