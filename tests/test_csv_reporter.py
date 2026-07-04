"""Unit tests for the CSVReporter class."""

import csv
from decimal import Decimal
from pathlib import Path

from mfrecon.core.domain import (
    AuditTrace,
    CRMRecord,
    Discrepancy,
    DiscrepancyType,
    FATCAStatus,
    FileFailure,
    InvestorStatus,
    KYCStatus,
    ReconciliationResult,
    ReconciliationRunMetadata,
    RecordSource,
    ReportRecord,
)
from mfrecon.reporters.csv import CSVReporter


class DummyCoreResult:
    """Mock container for matched and unmatched records from engine."""
    def __init__(self, matched_records, unmatched_records):
        self.matched_records = matched_records
        self.unmatched_records = unmatched_records


def test_csv_reporter_generation(tmp_path: Path) -> None:
    """Verifies that CSVReporter properly generates the flat CSV reports."""
    metadata = ReconciliationRunMetadata(
        run_id="csv-test-run",
        timestamp="2026-06-13T12:00:00Z",
        crm_file_hash="crmhash",
        report_file_hashes={},
        total_crm_records=2,
        total_report_records=3,
        validation_failures_count=0,
        discrepancies_count=1,
        failed_files=[
            FileFailure(
                file_name="failed.xlsx",
                source="BSE",
                failure_type="PARSER_ERROR",
                message="Bad structure",
            )
        ],
    )

    audit = AuditTrace(
        matching_route="EXACT_PAN",
        match_confidence=1.0,
        evaluation_timestamp="2026-06-13T12:00:00Z",
        reconciler_version="2.1",
        rule_evaluated="pan",
        skipped_comparisons=[],
    )

    discrepancies = [
        Discrepancy(
            discrepancy_type=DiscrepancyType.EMAIL_MISMATCH,
            pan="ABCDE1234F",
            field_name="email",
            crm_value="crm@test.com",
            report_value="rep@test.com",
            explanation="Email mismatch",
            source_info={"file_name": "cams.csv", "raw_row_index": "5", "folio_number": "999"},
            audit_trace=audit,
        )
    ]

    crm_rec = CRMRecord(
        pan="ABCDE1234F",
        investor_name="Ramesh Sharma",
        mobile="9876543210",
        email="crm@test.com",
        kyc_status=KYCStatus.VERIFIED,
        fatca_status=FATCAStatus.COMPLIANT,
        investor_status=InvestorStatus.ACTIVE,
        total_amount=Decimal("10000.00"),
        crm_client_id="CRM001",
    )

    rep_rec = ReportRecord(
        pan="ABCDE1234F",
        investor_name="Ramesh Sharma",
        mobile="9876543210",
        email="rep@test.com",
        kyc_status=KYCStatus.VERIFIED,
        fatca_status=FATCAStatus.COMPLIANT,
        investor_status=InvestorStatus.ACTIVE,
        total_amount=Decimal("10000.00"),
        source=RecordSource.CAMS,
        folio_number="999",
        raw_row_index=5,
    )

    unmatched_crm = CRMRecord(
        pan="XYZWP5678Q",
        investor_name="Sita Sharma",
        mobile="9876543211",
        email="sita@test.com",
        kyc_status=KYCStatus.PENDING,
        fatca_status=FATCAStatus.PENDING,
        investor_status=InvestorStatus.ACTIVE,
        total_amount=Decimal("5000.00"),
        crm_client_id="CRM002",
    )

    result = ReconciliationResult(
        metadata=metadata,
        discrepancies=discrepancies,
        excel_report_path=None,
        csv_report_path=None,
        json_report_path=None,
        matched_audits=[],
    )

    core_result = DummyCoreResult(
        matched_records=[(crm_rec, rep_rec)],
        unmatched_records=[unmatched_crm],
    )

    run_id = "testrun"
    reporter = CSVReporter(output_dir=tmp_path, run_id=run_id)
    reporter.report(result, core_result=core_result)

    # Check that output CSV files exist
    assert (tmp_path / f"discrepancies_{run_id}.csv").exists()
    assert (tmp_path / "discrepancies.csv").exists()
    assert (tmp_path / f"matched_{run_id}.csv").exists()
    assert (tmp_path / "matched.csv").exists()
    assert (tmp_path / f"unmatched_{run_id}.csv").exists()
    assert (tmp_path / "unmatched.csv").exists()
    assert (tmp_path / f"failed_files_{run_id}.csv").exists()
    assert (tmp_path / "failed_files.csv").exists()

    # Read and verify discrepancies.csv contents
    with (tmp_path / "discrepancies.csv").open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    assert len(rows) == 2  # header + 1 row
    assert rows[1][0] == DiscrepancyType.EMAIL_MISMATCH.value
    assert rows[1][1] == "ABCDE1234F"
    assert rows[1][2] == "email"
    assert rows[1][3] == "crm@test.com"
    assert rows[1][4] == "rep@test.com"
    assert rows[1][7] == "cams.csv"
    assert rows[1][8] == "5"
    assert rows[1][9] == "999"

    # Read and verify matched.csv contents
    with (tmp_path / "matched.csv").open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    assert len(rows) == 2
    assert rows[1][0] == "ABCDE1234F"
    assert rows[1][1] == "Ramesh Sharma"
    assert rows[1][9] == "CRM001"
    assert rows[1][10] == "CAMS"
    assert rows[1][11] == "999"

    # Read and verify unmatched.csv contents
    with (tmp_path / "unmatched.csv").open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    assert len(rows) == 2
    assert rows[1][0] == "CRM"
    assert rows[1][1] == "XYZWP5678Q"
    assert rows[1][2] == "Sita Sharma"
    assert rows[1][10] == "CRM002"

    # Read and verify failed_files.csv contents
    with (tmp_path / "failed_files.csv").open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    assert len(rows) == 2
    assert rows[1][0] == "failed.xlsx"
    assert rows[1][1] == "BSE"
    assert rows[1][2] == "PARSER_ERROR"
    assert rows[1][3] == "Bad structure"
