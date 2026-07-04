"""Unit tests for Phase 6.1 production readiness fixes."""

from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from mfrecon.core.config import EngineConfig, SourceProfileConfig
from mfrecon.core.domain import CRMRecord, RecordSource, ReportRecord
from mfrecon.core.exceptions import FileAccessError, PDFDecryptionError
from mfrecon.facade import ReconciliationEngine
from mfrecon.parsers.pdf_cas import PDFCASParser
from mfrecon.validators.duplicate import DuplicateDetector


# Helpers for creating test files
def create_csv_data(path: Path, data: dict[str, list[str | float | None]]) -> None:
    df = pd.DataFrame(data)
    df.to_csv(path, index=False, encoding="utf-8")


def test_facade_e2e_successful_run(tmp_path: Path) -> None:
    """Verifies a successful E2E facade run coordinating all steps."""
    crm_path = tmp_path / "crm.csv"
    create_csv_data(crm_path, {
        "PAN": ["ABCDE1234F"],
        "Investor Name": ["Ramesh Sharma"],
        "Client ID": ["CRM001"],
        "Total Amount": [150000.00]
    })

    cams_path = tmp_path / "cams.csv"
    create_csv_data(cams_path, {
        "PAN": ["ABCDE1234F"],
        "Investor Name": ["Ramesh Sharma"],
        "Folio Number": ["F123"],
        "Total Amount": [150000.00]
    })

    config = EngineConfig(output_directory=tmp_path)
    engine = ReconciliationEngine(config)
    result = engine.run(crm_path, [cams_path])

    assert result.metadata.total_crm_records == 1
    assert result.metadata.total_report_records == 1
    assert len(result.discrepancies) == 0
    assert len(result.matched_audits) == 1
    assert result.matched_audits[0].pan == "ABCDE1234F"
    assert result.matched_audits[0].route == "EXACT_PAN"


def test_facade_e2e_empty_crm_records(tmp_path: Path) -> None:
    """Verifies facade run when CRM file has headers but 0 records."""
    crm_path = tmp_path / "crm_empty.csv"
    create_csv_data(crm_path, {
        "PAN": [],
        "Investor Name": [],
        "Client ID": []
    })

    cams_path = tmp_path / "cams.csv"
    create_csv_data(cams_path, {
        "PAN": ["ABCDE1234F"],
        "Investor Name": ["Ramesh Sharma"]
    })

    config = EngineConfig(output_directory=tmp_path)
    engine = ReconciliationEngine(config)
    result = engine.run(crm_path, [cams_path])

    assert result.metadata.total_crm_records == 0
    assert result.metadata.total_report_records == 1
    # Report record should be unmatched (missing in CRM)
    assert len(result.discrepancies) == 1
    assert result.discrepancies[0].discrepancy_type.value == "MISSING_IN_CRM"


def test_facade_e2e_missing_crm_file(tmp_path: Path) -> None:
    """Verifies that running with a missing CRM file raises FileAccessError."""
    engine = ReconciliationEngine(EngineConfig(output_directory=tmp_path))
    with pytest.raises(FileAccessError):
        engine.run(tmp_path / "non_existent_crm.csv", [])


def test_facade_e2e_missing_report_file(tmp_path: Path) -> None:
    """Verifies that running with a missing report file raises FileAccessError."""
    crm_path = tmp_path / "crm.csv"
    create_csv_data(crm_path, {
        "PAN": ["ABCDE1234F"],
        "Investor Name": ["Ramesh Sharma"]
    })

    engine = ReconciliationEngine(EngineConfig(output_directory=tmp_path))
    with pytest.raises(FileAccessError):
        engine.run(crm_path, [tmp_path / "non_existent_report.csv"])


def test_crm_duplicate_different_clients_no_collision() -> None:
    """Verifies that CRM records with the same PAN but different client IDs do not collide."""
    detector = DuplicateDetector()
    rec1 = CRMRecord(
        crm_client_id="C1",
        pan="ABCDE1234F",
        investor_name="Ramesh Sharma",
        total_amount=Decimal("100.00")
    )
    rec2 = CRMRecord(
        crm_client_id="C2",
        pan="ABCDE1234F",
        investor_name="Ramesh Sharma",
        total_amount=Decimal("100.00")
    )

    valid, invalid, failures = detector.process([rec1, rec2])
    assert len(valid) == 2
    assert len(invalid) == 0
    assert len(failures) == 0


def test_crm_duplicate_same_client_exact_collision() -> None:
    """Verifies that CRM records with the same PAN and same client ID are flagged as EXACT_DUPLICATE."""
    detector = DuplicateDetector()
    rec1 = CRMRecord(
        crm_client_id="C1",
        pan="ABCDE1234F",
        investor_name="Ramesh Sharma",
        total_amount=Decimal("100.00")
    )
    rec2 = CRMRecord(
        crm_client_id="C1",
        pan="ABCDE1234F",
        investor_name="Ramesh Sharma",
        total_amount=Decimal("100.00")
    )

    valid, invalid, failures = detector.process([rec1, rec2])
    assert len(valid) == 1
    assert len(invalid) == 1
    assert len(failures) == 1
    assert failures[0]["failure_type"] == "EXACT_DUPLICATE"


def test_crm_duplicate_same_client_conflicting_collision() -> None:
    """Verifies that CRM records with same client ID and conflicting fields are flagged as CONFLICTING_DUPLICATE."""
    detector = DuplicateDetector()
    rec1 = CRMRecord(
        crm_client_id="C1",
        pan="ABCDE1234F",
        investor_name="Ramesh Sharma",
        total_amount=Decimal("100.00")
    )
    rec2 = CRMRecord(
        crm_client_id="C1",
        pan="ABCDE1234F",
        investor_name="Ramesh Kumar Sharma",
        total_amount=Decimal("200.00")
    )

    valid, invalid, failures = detector.process([rec1, rec2])
    assert len(valid) == 1
    assert len(invalid) == 1
    assert len(failures) == 1
    assert failures[0]["failure_type"] == "CONFLICTING_DUPLICATE"


def test_report_duplicate_different_folios_no_collision() -> None:
    """Verifies report records with the same PAN but different folios do not collide."""
    detector = DuplicateDetector()
    rec1 = ReportRecord(
        source=RecordSource.CAMS,
        folio_number="F123",
        raw_row_index=1,
        pan="ABCDE1234F",
        investor_name="Ramesh Sharma"
    )
    rec2 = ReportRecord(
        source=RecordSource.CAMS,
        folio_number="F456",
        raw_row_index=2,
        pan="ABCDE1234F",
        investor_name="Ramesh Sharma"
    )

    valid, invalid, failures = detector.process([rec1, rec2])
    assert len(valid) == 2
    assert len(invalid) == 0
    assert len(failures) == 0


def test_report_duplicate_same_folio_exact_collision() -> None:
    """Verifies report records with same PAN and folio are flagged as EXACT_DUPLICATE."""
    detector = DuplicateDetector()
    rec1 = ReportRecord(
        source=RecordSource.CAMS,
        folio_number="F123",
        raw_row_index=1,
        pan="ABCDE1234F",
        investor_name="Ramesh Sharma"
    )
    rec2 = ReportRecord(
        source=RecordSource.CAMS,
        folio_number="F123",
        raw_row_index=2,
        pan="ABCDE1234F",
        investor_name="Ramesh Sharma"
    )

    valid, invalid, failures = detector.process([rec1, rec2])
    assert len(valid) == 1
    assert len(invalid) == 1
    assert len(failures) == 1
    assert failures[0]["failure_type"] == "EXACT_DUPLICATE"


def test_report_duplicate_same_folio_conflicting_collision() -> None:
    """Verifies report records with same folio but conflicts are flagged as CONFLICTING_DUPLICATE."""
    detector = DuplicateDetector()
    rec1 = ReportRecord(
        source=RecordSource.CAMS,
        folio_number="F123",
        raw_row_index=1,
        pan="ABCDE1234F",
        investor_name="Ramesh Sharma"
    )
    rec2 = ReportRecord(
        source=RecordSource.CAMS,
        folio_number="F123",
        raw_row_index=2,
        pan="ABCDE1234F",
        investor_name="Ramesh K Sharma"
    )

    valid, invalid, failures = detector.process([rec1, rec2])
    assert len(valid) == 1
    assert len(invalid) == 1
    assert len(failures) == 1
    assert failures[0]["failure_type"] == "CONFLICTING_DUPLICATE"


def test_report_duplicate_no_folio_exact_collision() -> None:
    """Verifies report records with same PAN but missing folios collide and flag as EXACT_DUPLICATE."""
    detector = DuplicateDetector()
    rec1 = ReportRecord(
        source=RecordSource.CAMS,
        folio_number=None,
        raw_row_index=1,
        pan="ABCDE1234F",
        investor_name="Ramesh Sharma"
    )
    rec2 = ReportRecord(
        source=RecordSource.CAMS,
        folio_number=None,
        raw_row_index=2,
        pan="ABCDE1234F",
        investor_name="Ramesh Sharma"
    )

    valid, invalid, failures = detector.process([rec1, rec2])
    assert len(valid) == 1
    assert len(invalid) == 1
    assert len(failures) == 1
    assert failures[0]["failure_type"] == "EXACT_DUPLICATE"


def test_report_duplicate_no_folio_conflicting_collision() -> None:
    """Verifies report records with same PAN, missing folios and conflict are flagged as CONFLICTING_DUPLICATE."""
    detector = DuplicateDetector()
    rec1 = ReportRecord(
        source=RecordSource.CAMS,
        folio_number=None,
        raw_row_index=1,
        pan="ABCDE1234F",
        investor_name="Ramesh Sharma"
    )
    rec2 = ReportRecord(
        source=RecordSource.CAMS,
        folio_number=None,
        raw_row_index=2,
        pan="ABCDE1234F",
        investor_name="Ramesh K Sharma"
    )

    valid, invalid, failures = detector.process([rec1, rec2])
    assert len(valid) == 1
    assert len(invalid) == 1
    assert len(failures) == 1
    assert failures[0]["failure_type"] == "CONFLICTING_DUPLICATE"


def test_pdf_decryption_error_isolation(tmp_path: Path) -> None:
    """Verifies PDFDecryptionError is isolated as a FileFailure, batch succeeding."""
    crm_path = tmp_path / "crm.csv"
    create_csv_data(crm_path, {
        "PAN": ["ABCDE1234F"],
        "Investor Name": ["Ramesh Sharma"]
    })

    pdf_path = tmp_path / "statement.pdf"
    pdf_path.touch()

    config = EngineConfig(output_directory=tmp_path)
    engine = ReconciliationEngine(config)

    # Mock PDFCASParser.parse_report to raise PDFDecryptionError
    with patch.object(PDFCASParser, "parse_report", side_effect=PDFDecryptionError("Mock PDF Decryption failure")):
        result = engine.run(crm_path, [pdf_path])

    # Batch succeeds, failed_files contains the failure
    assert len(result.metadata.failed_files) == 1
    assert result.metadata.failed_files[0].file_name == "statement.pdf"
    assert result.metadata.failed_files[0].source == "PDF_CAS"
    assert result.metadata.failed_files[0].failure_type == "PDF_DECRYPTION_ERROR"


def test_pdf_decryption_error_batch_continues(tmp_path: Path) -> None:
    """Verifies E2E execution continues parsing remaining files after a PDF decryption error."""
    crm_path = tmp_path / "crm.csv"
    create_csv_data(crm_path, {
        "PAN": ["ABCDE1234F"],
        "Investor Name": ["Ramesh Sharma"],
        "Client ID": ["CRM001"]
    })

    pdf_path = tmp_path / "statement.pdf"
    pdf_path.touch()

    cams_path = tmp_path / "cams.csv"
    create_csv_data(cams_path, {
        "PAN": ["ABCDE1234F"],
        "Investor Name": ["Ramesh Sharma"]
    })

    config = EngineConfig(output_directory=tmp_path)
    engine = ReconciliationEngine(config)

    with patch.object(PDFCASParser, "parse_report", side_effect=PDFDecryptionError("Mock decryption failure")):
        result = engine.run(crm_path, [pdf_path, cams_path])

    # Batch succeeds
    assert len(result.metadata.failed_files) == 1
    assert result.metadata.failed_files[0].file_name == "statement.pdf"
    # CAMS record successfully reconciled
    assert result.metadata.total_report_records == 1
    assert len(result.matched_audits) == 1
    assert result.matched_audits[0].pan == "ABCDE1234F"


def test_parser_detection_error_isolation(tmp_path: Path) -> None:
    """Verifies that report files failing parser detection are recorded as FileFailure."""
    crm_path = tmp_path / "crm.csv"
    create_csv_data(crm_path, {
        "PAN": ["ABCDE1234F"],
        "Investor Name": ["Ramesh Sharma"]
    })

    unrecognized_file = tmp_path / "unknown_ext.txt"
    unrecognized_file.write_text("Unstructured random data", encoding="utf-8")

    config = EngineConfig(output_directory=tmp_path)
    engine = ReconciliationEngine(config)
    result = engine.run(crm_path, [unrecognized_file])

    assert len(result.metadata.failed_files) == 1
    assert result.metadata.failed_files[0].file_name == "unknown_ext.txt"
    assert result.metadata.failed_files[0].source == "UNKNOWN"
    assert result.metadata.failed_files[0].failure_type == "PARSER_DETECTION_ERROR"


def test_matched_audit_exact_pan(tmp_path: Path) -> None:
    """Verifies successful match details recorded for EXACT_PAN route."""
    crm_path = tmp_path / "crm.csv"
    create_csv_data(crm_path, {
        "PAN": ["ABCDE1234F"],
        "Investor Name": ["Ramesh Sharma"],
        "Client ID": ["CRM001"]
    })

    cams_path = tmp_path / "cams.csv"
    create_csv_data(cams_path, {
        "PAN": ["ABCDE1234F"],
        "Investor Name": ["Ramesh Sharma"]
    })

    config = EngineConfig(output_directory=tmp_path)
    engine = ReconciliationEngine(config)
    result = engine.run(crm_path, [cams_path])

    assert len(result.matched_audits) == 1
    audit = result.matched_audits[0]
    assert audit.pan == "ABCDE1234F"
    assert audit.route == "EXACT_PAN"
    assert audit.confidence == 1.0
    assert audit.source == "CAMS"
    assert audit.timestamp != ""


def test_matched_audit_fuzzy_match(tmp_path: Path) -> None:
    """Verifies successful match details recorded for fuzzy fallback match route."""
    crm_path = tmp_path / "crm.csv"
    create_csv_data(crm_path, {
        "PAN": ["ABCDE1234F"],
        "Investor Name": ["Ramesh Sharma"],
        "Mobile": ["9876543210"],
        "Client ID": ["CRM001"]
    })

    # Report has different PAN (won't match exactly) but same mobile and similar name
    cams_path = tmp_path / "cams.csv"
    create_csv_data(cams_path, {
        "PAN": ["XYZWP5678Q"],
        "Investor Name": ["Ramesh K Sharma"],
        "Mobile": ["9876543210"]
    })

    config = EngineConfig(output_directory=tmp_path)
    # Enable fuzzy matching globally
    config.matching.enable_fuzzy_matching = True
    config.matching.fuzzy_threshold = 0.80
    config.matching.fuzzy_secondary_keys = ["mobile"]

    engine = ReconciliationEngine(config)
    result = engine.run(crm_path, [cams_path])

    assert len(result.matched_audits) == 1
    audit = result.matched_audits[0]
    # Reconciled to CRM's PAN since it matched to the CRM record!
    # Wait, does the audit route PAN record the report PAN or the resolved/matched CRM record PAN?
    # Let's check reconciler.py: `pan=report.pan` is passed to MatchedAudit constructor.
    assert audit.pan == "XYZWP5678Q"
    assert audit.route == "FUZZY_NAME_AND_MOBILE"
    assert audit.confidence >= 0.80


def test_matched_audit_skipped_comparisons(tmp_path: Path) -> None:
    """Verifies that skipped comparisons are correctly calculated and logged in the MatchedAudit."""
    crm_path = tmp_path / "crm.csv"
    create_csv_data(crm_path, {
        "PAN": ["ABCDE1234F"],
        "Investor Name": ["Ramesh Sharma"],
        "Client ID": ["CRM001"]
    })

    cams_path = tmp_path / "cams.csv"
    create_csv_data(cams_path, {
        "PAN": ["ABCDE1234F"],
        "Investor Name": ["Ramesh Sharma"]
    })

    config = EngineConfig(output_directory=tmp_path)
    # Configure source profile for CAMS to only compare pan and investor_name
    config.sources["CAMS"] = SourceProfileConfig(
        available_fields=["pan", "investor_name"],
        required_fields=["pan", "investor_name"],
        compare=["pan", "investor_name"],
        validations=["pan_format"]
    )

    engine = ReconciliationEngine(config)
    result = engine.run(crm_path, [cams_path])

    assert len(result.matched_audits) == 1
    audit = result.matched_audits[0]
    assert "EMAIL_COMPARISON_SKIPPED" in audit.skipped_comparisons
    assert "MOBILE_COMPARISON_SKIPPED" in audit.skipped_comparisons
    assert "AMOUNT_COMPARISON_SKIPPED" in audit.skipped_comparisons


def test_reconciliation_result_audit_storage(tmp_path: Path) -> None:
    """Verifies that facade results correctly populate all run metadata details."""
    crm_path = tmp_path / "crm.csv"
    create_csv_data(crm_path, {
        "PAN": ["ABCDE1234F"],
        "Investor Name": ["Ramesh Sharma"],
        "Client ID": ["CRM001"]
    })

    cams_path = tmp_path / "cams.csv"
    create_csv_data(cams_path, {
        "PAN": ["ABCDE1234F"],
        "Investor Name": ["Ramesh Sharma"]
    })

    config = EngineConfig(output_directory=tmp_path)
    engine = ReconciliationEngine(config)
    result = engine.run(crm_path, [cams_path])

    assert result.metadata.run_id == engine.run_id
    assert result.metadata.timestamp != ""
    assert result.metadata.crm_file_hash != ""
    assert cams_path.name in result.metadata.report_file_hashes


def test_facade_validation_failures_aggregation(tmp_path: Path) -> None:
    """Verifies validation failures from both parsing and validation engine are aggregated."""
    crm_path = tmp_path / "crm.csv"
    # Row 2 has invalid PAN format, Row 3 has missing required fields
    create_csv_data(crm_path, {
        "PAN": ["ABCDE1234F", "INVALID_PAN_123", ""],
        "Investor Name": ["Ramesh Sharma", "Suresh Kumar", "Amit Sharma"],
        "Client ID": ["CRM001", "CRM002", "CRM003"]
    })

    config = EngineConfig(output_directory=tmp_path)
    engine = ReconciliationEngine(config)
    result = engine.run(crm_path, [])

    # Total CRM records parsed: 3 (including failures)
    # Row 3 fails required PAN validation in CRM parser -> 1 parser failure.
    # Row 2 (INVALID_PAN_123) fails validation in ValidationEngine (regex format check) -> 1 engine failure.
    # So total validation failures = 2.
    assert result.metadata.total_crm_records == 3
    assert result.metadata.validation_failures_count == 2


def test_facade_output_paths(tmp_path: Path) -> None:
    """Verifies correct output paths generated with matching facade run ID."""
    crm_path = tmp_path / "crm.csv"
    create_csv_data(crm_path, {
        "PAN": ["ABCDE1234F"],
        "Investor Name": ["Ramesh Sharma"]
    })

    config = EngineConfig(output_directory=tmp_path)
    engine = ReconciliationEngine(config)
    result = engine.run(crm_path, [])

    assert result.excel_report_path == str(tmp_path / f"discrepancies_{engine.run_id}.xlsx")
    assert result.csv_report_path == str(tmp_path / f"discrepancies_{engine.run_id}.csv")
    assert result.json_report_path == str(tmp_path / f"discrepancies_{engine.run_id}.json")


def test_facade_multiple_reports(tmp_path: Path) -> None:
    """Verifies that E2E facade successfully coordinates run on multiple reports concurrently."""
    crm_path = tmp_path / "crm.csv"
    create_csv_data(crm_path, {
        "PAN": ["ABCDE1234F", "XYZWP5678Q"],
        "Investor Name": ["Ramesh Sharma", "Sita Sharma"],
        "Client ID": ["CRM001", "CRM002"]
    })

    cams_path = tmp_path / "cams.csv"
    create_csv_data(cams_path, {
        "PAN": ["ABCDE1234F"],
        "Investor Name": ["Ramesh Sharma"]
    })

    kfin_path = tmp_path / "kfintech.csv"
    create_csv_data(kfin_path, {
        "PAN": ["XYZWP5678Q"],
        "Investor Name": ["Sita Sharma"]
    })

    config = EngineConfig(output_directory=tmp_path)
    engine = ReconciliationEngine(config)
    result = engine.run(crm_path, [cams_path, kfin_path])

    assert result.metadata.total_crm_records == 2
    assert result.metadata.total_report_records == 2
    assert len(result.discrepancies) == 0
    assert len(result.matched_audits) == 2
