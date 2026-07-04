"""Unit tests for the SummaryReporter verifying metric aggregation and summary formatting."""

from mfrecon.core.domain import (
    AuditTrace,
    Discrepancy,
    DiscrepancyType,
    ReconciliationResult,
    ReconciliationRunMetadata,
)
from mfrecon.reporters.summary import SummaryReporter


def test_summary_reporter_metrics_calculation() -> None:
    """Verifies that reconciliation metrics and discrepancy counts are correctly aggregated."""
    metadata = ReconciliationRunMetadata(
        run_id="test-run-123",
        timestamp="2026-06-13T12:00:00Z",
        crm_file_hash="crmhash",
        report_file_hashes={"report1.csv": "rephash"},
        total_crm_records=100,
        total_report_records=150,
        validation_failures_count=5,
        discrepancies_count=4,
        failed_files=[],
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
            discrepancy_type=DiscrepancyType.MISSING_IN_CRM,
            pan="ABCDE1234F",
            explanation="Missing in CRM",
            audit_trace=audit,
        ),
        Discrepancy(
            discrepancy_type=DiscrepancyType.MISSING_IN_REPORT,
            pan="XYZWP5678Q",
            explanation="Missing in Report",
            audit_trace=audit,
        ),
        Discrepancy(
            discrepancy_type=DiscrepancyType.NAME_MISMATCH,
            pan="KLMNO9012P",
            field_name="investor_name",
            crm_value="John Doe",
            report_value="John A Doe",
            explanation="Name mismatch",
            audit_trace=audit,
        ),
        Discrepancy(
            discrepancy_type=DiscrepancyType.NAME_MISMATCH,
            pan="PQRST3456F",
            field_name="investor_name",
            crm_value="Jane Smith",
            report_value="Jane B Smith",
            explanation="Name mismatch",
            audit_trace=audit,
        ),
    ]

    result = ReconciliationResult(
        metadata=metadata,
        discrepancies=discrepancies,
        excel_report_path=None,
        csv_report_path=None,
        json_report_path=None,
        matched_audits=[],
    )

    reporter = SummaryReporter()
    metrics = reporter.get_summary_metrics(result)

    assert metrics["total_crm_records"] == 100
    assert metrics["total_report_records"] == 150
    assert metrics["matched_records"] == 0
    assert metrics["missing_in_crm"] == 1
    assert metrics["missing_in_report"] == 1
    assert metrics["field_discrepancies"] == 2
    assert metrics["validation_failures"] == 5
    assert metrics["failed_files_count"] == 0

    breakdown = metrics["discrepancy_breakdown"]
    assert breakdown[DiscrepancyType.MISSING_IN_CRM.value] == 1
    assert breakdown[DiscrepancyType.MISSING_IN_REPORT.value] == 1
    assert breakdown[DiscrepancyType.NAME_MISMATCH.value] == 2


def test_summary_reporter_output_text() -> None:
    """Verifies the generated plain text executive summary statement format and content."""
    metadata = ReconciliationRunMetadata(
        run_id="test-run-123",
        timestamp="2026-06-13T12:00:00Z",
        crm_file_hash="crmhash",
        report_file_hashes={},
        total_crm_records=10,
        total_report_records=12,
        validation_failures_count=1,
        discrepancies_count=0,
        failed_files=[],
    )

    result = ReconciliationResult(
        metadata=metadata,
        discrepancies=[],
        excel_report_path=None,
        csv_report_path=None,
        json_report_path=None,
        matched_audits=[],
    )

    reporter = SummaryReporter()
    summary = reporter.generate_summary(result)

    assert "RECONCILIATION RUN EXECUTIVE SUMMARY" in summary
    assert "Total CRM Records: 10" in summary
    assert "Total Report Records: 12" in summary
    assert "No discrepancies detected." in summary
