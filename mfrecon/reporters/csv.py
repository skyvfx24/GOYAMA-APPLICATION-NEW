"""CSV reporter class streaming reconciliation data subsets to separate flat files."""

import csv
from pathlib import Path
from typing import Any

from mfrecon.core.domain import CRMRecord, ReconciliationResult, ReportRecord


class CSVReporter:
    """Streams reconciliation result datasets directly to separate CSV files."""

    def __init__(self, output_dir: Path, run_id: str) -> None:
        self.output_dir = output_dir
        self.run_id = run_id

    def report(self, result: ReconciliationResult, core_result: Any | None = None) -> Path:
        """
        Generates discrepancies, matched, unmatched, and failed file CSVs.

        Args:
            result: Facade ReconciliationResult container.
            core_result: Optional engine ReconciliationResult containing matched/unmatched records.

        Returns:
            Path: The path to the main discrepancies CSV.
        """
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Main facade discrepancies path
        discrepancies_path = self.output_dir / f"discrepancies_{self.run_id}.csv"

        # 1. Write discrepancies
        self._write_discrepancies(result.discrepancies, discrepancies_path)
        self._write_discrepancies(result.discrepancies, self.output_dir / "discrepancies.csv")

        # 2. Write matched records (using core result matched_records if provided)
        matched_records = getattr(core_result or result, "matched_records", [])
        self._write_matched(matched_records, self.output_dir / f"matched_{self.run_id}.csv")
        self._write_matched(matched_records, self.output_dir / "matched.csv")

        # 3. Write unmatched records (using core result unmatched_records if provided)
        unmatched_records = getattr(core_result or result, "unmatched_records", [])
        self._write_unmatched(unmatched_records, self.output_dir / f"unmatched_{self.run_id}.csv")
        self._write_unmatched(unmatched_records, self.output_dir / "unmatched.csv")

        # 4. Write failed files
        self._write_failed_files(result.metadata.failed_files, self.output_dir / f"failed_files_{self.run_id}.csv")
        self._write_failed_files(result.metadata.failed_files, self.output_dir / "failed_files.csv")

        return discrepancies_path

    def _write_discrepancies(self, discrepancies: list[Any], path: Path) -> None:
        headers = [
            "discrepancy_type",
            "pan",
            "field_name",
            "crm_value",
            "report_value",
            "severity",
            "explanation",
            "file_name",
            "raw_row_index",
            "folio_number",
        ]
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for d in discrepancies:
                source_info = d.source_info or {}
                writer.writerow([
                    d.discrepancy_type.value,
                    d.pan,
                    d.field_name or "",
                    d.crm_value or "",
                    d.report_value or "",
                    d.severity,
                    d.explanation,
                    source_info.get("file_name", "N/A"),
                    source_info.get("raw_row_index", "N/A"),
                    source_info.get("folio_number", "N/A"),
                ])

    def _write_matched(self, matched_records: list[tuple[Any, Any]], path: Path) -> None:
        headers = [
            "pan",
            "investor_name",
            "mobile",
            "email",
            "kyc_status",
            "fatca_status",
            "investor_status",
            "last_transaction_date",
            "total_amount",
            "crm_client_id",
            "report_source",
            "report_folio",
            "report_raw_row_index",
        ]
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for crm, report in matched_records:
                writer.writerow([
                    crm.pan,
                    crm.investor_name,
                    crm.mobile or "",
                    crm.email or "",
                    crm.kyc_status.value,
                    crm.fatca_status.value,
                    crm.investor_status.value,
                    str(crm.last_transaction_date) if crm.last_transaction_date else "",
                    str(crm.total_amount),
                    crm.crm_client_id,
                    report.source.value,
                    report.folio_number or "",
                    report.raw_row_index,
                ])

    def _write_unmatched(self, unmatched_records: list[Any], path: Path) -> None:
        headers = [
            "record_type",
            "pan",
            "investor_name",
            "mobile",
            "email",
            "kyc_status",
            "fatca_status",
            "investor_status",
            "last_transaction_date",
            "total_amount",
            "crm_client_id",
            "report_source",
            "report_folio",
            "report_raw_row_index",
        ]
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for rec in unmatched_records:
                if isinstance(rec, CRMRecord):
                    writer.writerow([
                        "CRM",
                        rec.pan,
                        rec.investor_name,
                        rec.mobile or "",
                        rec.email or "",
                        rec.kyc_status.value,
                        rec.fatca_status.value,
                        rec.investor_status.value,
                        str(rec.last_transaction_date) if rec.last_transaction_date else "",
                        str(rec.total_amount),
                        rec.crm_client_id,
                        "",
                        "",
                        "",
                    ])
                elif isinstance(rec, ReportRecord):
                    writer.writerow([
                        "REPORT",
                        rec.pan,
                        rec.investor_name,
                        rec.mobile or "",
                        rec.email or "",
                        rec.kyc_status.value,
                        rec.fatca_status.value,
                        rec.investor_status.value,
                        str(rec.last_transaction_date) if rec.last_transaction_date else "",
                        str(rec.total_amount),
                        "",
                        rec.source.value,
                        rec.folio_number or "",
                        rec.raw_row_index,
                    ])

    def _write_failed_files(self, failed_files: list[Any], path: Path) -> None:
        headers = ["file_name", "source", "failure_type", "message"]
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for failure in failed_files:
                writer.writerow([
                    failure.file_name,
                    failure.source,
                    failure.failure_type,
                    failure.message,
                ])
