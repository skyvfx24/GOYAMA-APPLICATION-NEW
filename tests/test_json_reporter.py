"""Unit tests for the JSONReporter class."""

import json
from pathlib import Path

from mfrecon.core.domain import (
    AuditTrace,
    Discrepancy,
    DiscrepancyType,
    FileFailure,
    MatchedAudit,
    ReconciliationResult,
    ReconciliationRunMetadata,
)
from mfrecon.reporters.json_reporter import JSONReporter


def test_json_reporter_generation(tmp_path: Path) -> None:
    """Verifies that JSONReporter properly generates the JSON discrepancy reports with appropriate structure."""
    metadata = ReconciliationRunMetadata(
        run_id="json-test-run",
        timestamp="2026-06-13T12:00:00Z",
        crm_file_hash="crmhash",
        report_file_hashes={"test.pdf": "pdfhash"},
        total_crm_records=5,
        total_report_records=8,
        validation_failures_count=2,
        discrepancies_count=1,
        failed_files=[
            FileFailure(
                file_name="test.pdf",
                source="CAMS",
                failure_type="PDF_DECRYPTION_ERROR",
                message="Decryption failed",
            )
        ],
    )

    audit_trace = AuditTrace(
        matching_route="EXACT_PAN",
        match_confidence=1.0,
        evaluation_timestamp="2026-06-13T12:00:00Z",
        reconciler_version="2.1",
        rule_evaluated="pan",
        skipped_comparisons=[],
    )

    discrepancies = [
        Discrepancy(
            discrepancy_type=DiscrepancyType.MOBILE_MISMATCH,
            pan="ABCDE1234F",
            field_name="mobile",
            crm_value="9876543210",
            report_value="9198765432",
            explanation="Mobile mismatch",
            source_info={"file_name": "cams.csv", "raw_row_index": "2", "folio_number": "12345"},
            audit_trace=audit_trace,
        )
    ]

    matched_audits = [
        MatchedAudit(
            pan="ABCDE1234F",
            route="EXACT_PAN",
            confidence=1.0,
            source="CAMS",
            timestamp="2026-06-13T12:00:00Z",
            skipped_comparisons=[],
        )
    ]

    result = ReconciliationResult(
        metadata=metadata,
        discrepancies=discrepancies,
        excel_report_path=None,
        csv_report_path=None,
        json_report_path=None,
        matched_audits=matched_audits,
    )

    run_id = "test_run_123"
    reporter = JSONReporter(output_dir=tmp_path, run_id=run_id)

    target_file = tmp_path / f"discrepancies_{run_id}.json"
    fallback_file = tmp_path / "reconciliation_result.json"

    reporter.report(result, file_path=target_file)

    assert target_file.exists()
    assert fallback_file.exists()

    with target_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Verify JSON structure
    assert "statistics" in data
    assert "discrepancies" in data
    assert "failed_files" in data
    assert "matched_audits" in data

    stats = data["statistics"]
    assert stats["total_crm_records"] == 5
    assert stats["total_report_records"] == 8
    assert stats["validation_failures"] == 2
    assert stats["field_discrepancies"] == 1

    discs = data["discrepancies"]
    assert len(discs) == 1
    assert discs[0]["pan"] == "ABCDE1234F"
    assert discs[0]["field_name"] == "mobile"
    assert discs[0]["crm_value"] == "9876543210"
    assert discs[0]["report_value"] == "9198765432"

    fails = data["failed_files"]
    assert len(fails) == 1
    assert fails[0]["file_name"] == "test.pdf"
    assert fails[0]["failure_type"] == "PDF_DECRYPTION_ERROR"

    audits = data["matched_audits"]
    assert len(audits) == 1
    assert audits[0]["pan"] == "ABCDE1234F"
    assert audits[0]["route"] == "EXACT_PAN"
