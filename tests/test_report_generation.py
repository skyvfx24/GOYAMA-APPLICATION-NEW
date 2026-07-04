"""Unit tests for report generation configuration, empty sets, and large dataset processing."""

from pathlib import Path

from mfrecon.core.config import EngineConfig, ReportingConfig
from mfrecon.core.domain import (
    AuditTrace,
    Discrepancy,
    DiscrepancyType,
    ReconciliationResult,
    ReconciliationRunMetadata,
)
from mfrecon.facade import ReconciliationEngine
from mfrecon.reporters.csv import CSVReporter
from mfrecon.reporters.excel import ExcelReporter
from mfrecon.reporters.json_reporter import JSONReporter


def test_empty_results_generation(tmp_path: Path) -> None:
    """Verifies that the reporting layer successfully runs and handles empty reconciliation results."""
    metadata = ReconciliationRunMetadata(
        run_id="empty-test",
        timestamp="2026-06-13T12:00:00Z",
        crm_file_hash="empty_hash",
        report_file_hashes={},
        total_crm_records=0,
        total_report_records=0,
        validation_failures_count=0,
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

    # Excel
    excel_reporter = ExcelReporter(output_dir=tmp_path, run_id="empty-test")
    excel_reporter.report(result)
    assert (tmp_path / "discrepancies_empty-test.xlsx").exists()

    # CSV
    csv_reporter = CSVReporter(output_dir=tmp_path, run_id="empty-test")
    csv_reporter.report(result)
    assert (tmp_path / "discrepancies_empty-test.csv").exists()

    # JSON
    json_reporter = JSONReporter(output_dir=tmp_path, run_id="empty-test")
    json_reporter.report(result)
    assert (tmp_path / "discrepancies_empty-test.json").exists()


def test_config_driven_formats_selection(tmp_path: Path) -> None:
    """Verifies facade selectively generates only configured formats based on ReportingConfig."""
    # Write empty crm and report files to execute run()
    crm_file = tmp_path / "crm_empty.csv"
    crm_file.write_text("PAN,Investor Name,Client ID\n", encoding="utf-8")

    cams_file = tmp_path / "cams_empty.csv"
    cams_file.write_text("PAN,Investor Name\n", encoding="utf-8")

    # Only request JSON output format
    config = EngineConfig(
        output_directory=tmp_path,
        reporting=ReportingConfig(
            default_output_formats=["excel"],
            formats=["json"],  # override to JSON only
        ),
    )

    engine = ReconciliationEngine(config)
    result = engine.run(crm_file, [cams_file])

    # Assert only JSON was generated
    assert result.json_report_path is not None
    assert Path(result.json_report_path).exists()
    assert result.excel_report_path is None
    assert result.csv_report_path is None


def test_large_dataset_performance(tmp_path: Path) -> None:
    """Tests that exporting large datasets (e.g. 10,000+ items) performs efficiently without OOM."""
    metadata = ReconciliationRunMetadata(
        run_id="large-perf-test",
        timestamp="2026-06-13T12:00:00Z",
        crm_file_hash="hash",
        report_file_hashes={},
        total_crm_records=10000,
        total_report_records=10000,
        validation_failures_count=0,
        discrepancies_count=10000,
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

    # Generate 10,000 discrepancies
    discrepancies = [
        Discrepancy(
            discrepancy_type=DiscrepancyType.AMOUNT_MISMATCH,
            pan=f"ABCDE{i:04d}F",
            field_name="total_amount",
            crm_value="100.00",
            report_value="150.00",
            explanation="Amount mismatch",
            audit_trace=audit,
        )
        for i in range(10000)
    ]

    result = ReconciliationResult(
        metadata=metadata,
        discrepancies=discrepancies,
        excel_report_path=None,
        csv_report_path=None,
        json_report_path=None,
        matched_audits=[],
    )

    # Test CSV generation speed and memory
    csv_reporter = CSVReporter(output_dir=tmp_path, run_id="large-perf-test")
    csv_reporter.report(result)

    assert (tmp_path / "discrepancies_large-perf-test.csv").exists()

    # Test JSON generation
    json_reporter = JSONReporter(output_dir=tmp_path, run_id="large-perf-test")
    json_reporter.report(result)

    assert (tmp_path / "discrepancies_large-perf-test.json").exists()
