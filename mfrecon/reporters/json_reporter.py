"""JSON reporter class serializing reconciliation results to a structured file."""

import json
from pathlib import Path

from mfrecon.core.domain import ReconciliationResult
from mfrecon.reporters.summary import SummaryReporter


class JSONReporter:
    """Exports reconciliation result details to a structured JSON file."""

    def __init__(self, output_dir: Path, run_id: str) -> None:
        self.output_dir = output_dir
        self.run_id = run_id
        self.summary_reporter = SummaryReporter()

    def report(self, result: ReconciliationResult, file_path: Path | None = None) -> Path:
        """
        Generates and saves the JSON report.

        Args:
            result: Facade ReconciliationResult container.
            file_path: Optional path override. Defaults to output_dir/reconciliation_result_{run_id}.json.

        Returns:
            Path: The path to the written JSON file.
        """
        if not file_path:
            file_path = self.output_dir / f"discrepancies_{self.run_id}.json"

        # Generate exact name fallback too
        fallback_path = self.output_dir / "reconciliation_result.json"

        metrics = self.summary_reporter.get_summary_metrics(result)

        data = {
            "statistics": {
                "total_crm_records": metrics["total_crm_records"],
                "total_report_records": metrics["total_report_records"],
                "matched_records": metrics["matched_records"],
                "missing_in_crm": metrics["missing_in_crm"],
                "missing_in_report": metrics["missing_in_report"],
                "field_discrepancies": metrics["field_discrepancies"],
                "validation_failures": metrics["validation_failures"],
            },
            "discrepancies": [d.model_dump(mode="json") for d in result.discrepancies],
            "failed_files": [f.model_dump(mode="json") for f in result.metadata.failed_files],
            "matched_audits": [a.model_dump(mode="json") for a in result.matched_audits],
        }

        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        # Write exact name copy for compliance
        with fallback_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        return file_path
