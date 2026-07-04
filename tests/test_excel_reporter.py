"""Unit tests for the ExcelReporter class verifying multi-sheet openpyxl workbook layout and design rules."""

from decimal import Decimal
from pathlib import Path

import openpyxl

from mfrecon.core.domain import (
    AuditTrace,
    CRMRecord,
    Discrepancy,
    DiscrepancyType,
    FATCAStatus,
    FileFailure,
    InvestorStatus,
    KYCStatus,
    MatchedAudit,
    ReconciliationResult,
    ReconciliationRunMetadata,
    RecordSource,
    ReportRecord,
)
from mfrecon.reporters.excel import ExcelReporter


class DummyCoreResult:
    """Mock container for matched and unmatched records from engine."""
    def __init__(self, matched_records, unmatched_records):
        self.matched_records = matched_records
        self.unmatched_records = unmatched_records


def test_excel_reporter_workbook_generation(tmp_path: Path) -> None:
    """Verifies the multi-sheet layout, formatting styles, and formatting details of Excel reports."""
    metadata = ReconciliationRunMetadata(
        run_id="excel-test-run",
        timestamp="2026-06-13T12:00:00Z",
        crm_file_hash="crmhash",
        report_file_hashes={},
        total_crm_records=2,
        total_report_records=3,
        validation_failures_count=2,
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

    # Two validation failures for duplicates
    validation_failures = [
        {
            "row_number": 2,
            "source": "CRM",
            "failure_type": "EXACT_DUPLICATE",
            "field_name": "pan",
            "message": "Exact duplicate",
            "raw_data": {"pan": "ABCDE1234F"},
        },
        {
            "row_number": 3,
            "source": "CAMS",
            "failure_type": "CONFLICTING_DUPLICATE",
            "field_name": "pan",
            "message": "Conflicting duplicate",
            "raw_data": {"pan": "XYZWP5678Q"},
        },
    ]

    result = ReconciliationResult(
        metadata=metadata,
        discrepancies=discrepancies,
        excel_report_path=None,
        csv_report_path=None,
        json_report_path=None,
        matched_audits=matched_audits,
    )

    core_result = DummyCoreResult(
        matched_records=[(crm_rec, rep_rec)],
        unmatched_records=[unmatched_crm],
    )

    run_id = "excelrun"
    reporter = ExcelReporter(output_dir=tmp_path, run_id=run_id)

    target_file = tmp_path / f"discrepancies_{run_id}.xlsx"
    reporter.report(
        result=result,
        core_result=core_result,
        all_validation_failures=validation_failures,
        file_path=target_file,
    )

    assert target_file.exists()
    assert (tmp_path / "discrepancies.xlsx").exists()

    # Load and verify Excel sheet names
    wb = openpyxl.load_workbook(target_file)
    expected_sheets = [
        "Summary",
        "Reconciliation",
        "Errors & Actions",
    ]
    assert list(wb.sheetnames) == expected_sheets

    # Verify Summary Sheet Title block and GridLines
    ws_summary = wb["Summary"]
    assert ws_summary.views.sheetView[0].showGridLines is True
    assert ws_summary["A1"].value == "Data Reconciliation: CRM vs External Sources"
    
    # Verify Reconciliation sheet formatting & contents
    ws_recon = wb["Reconciliation"]
    assert ws_recon.views.sheetView[0].showGridLines is True
    assert "Field-by-field reconciliation" in ws_recon["A1"].value
    assert ws_recon["A4"].value == "Field"

    # Verify Errors & Actions contents
    ws_errors = wb["Errors & Actions"]
    assert ws_errors.views.sheetView[0].showGridLines is True
    assert ws_errors["A1"].value == "Errors found & recommended action"
    assert ws_errors["A3"].value == "#"
    assert ws_errors["B3"].value == "Severity"
    assert ws_errors["C3"].value == "Source"

    # Verify auto widths logic applied
    col_width = ws_errors.column_dimensions["A"].width
    assert col_width is not None
    assert col_width > 5


def test_excel_reporter_multiple_columns(tmp_path: Path) -> None:
    """Verifies that multiple sources/files generate distinct columns with correct headers."""
    metadata = ReconciliationRunMetadata(
        run_id="excel-multi-test",
        timestamp="2026-06-26T12:00:00Z",
        crm_file_hash="crmhash",
        report_file_hashes={},
        total_crm_records=1,
        total_report_records=5,
        validation_failures_count=0,
        discrepancies_count=0,
        failed_files=[],
    )

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

    # 5 report records matching the primary PAN
    bse1 = ReportRecord(
        pan="ABCDE1234F", investor_name="Ramesh Sharma", mobile="9876543210", email="crm@test.com",
        source=RecordSource.BSE, folio_number="123", raw_row_index=2, total_amount=Decimal("10000.00")
    )
    object.__setattr__(bse1, "file_name", "BSE_master_123.xlsx")

    bse2 = ReportRecord(
        pan="ABCDE1234F", investor_name="Ramesh Sharma", mobile="9876543210", email="crm@test.com",
        source=RecordSource.BSE, folio_number="DHIRAJ", raw_row_index=3, total_amount=Decimal("10000.00")
    )
    object.__setattr__(bse2, "file_name", "BSE_master_DHIRAJ.xlsx")

    nse = ReportRecord(
        pan="ABCDE1234F", investor_name="Ramesh Sharma", mobile="9876543210", email="crm@test.com",
        source=RecordSource.NSE, folio_number="N/A", raw_row_index=2, total_amount=Decimal("10000.00")
    )
    object.__setattr__(nse, "file_name", "NSE_master.xlsx")

    kfin = ReportRecord(
        pan="ABCDE1234F", investor_name="Ramesh Sharma", mobile="9876543210", email="crm@test.com",
        source=RecordSource.KFINTECH, folio_number="N/A", raw_row_index=2, total_amount=Decimal("10000.00")
    )
    object.__setattr__(kfin, "file_name", "Kfin_MFSD211.xlsx")

    cams = ReportRecord(
        pan="ABCDE1234F", investor_name="Ramesh Sharma", mobile="9876543210", email="crm@test.com",
        source=RecordSource.CAMS, folio_number="N/A", raw_row_index=2, total_amount=Decimal("10000.00")
    )
    object.__setattr__(cams, "file_name", "cams_data.xlsx")

    pdf_rec = ReportRecord(
        pan="ABCDE1234F", investor_name="Ramesh Sharma", mobile="9876543210", email="crm@test.com",
        source=RecordSource.PDF_CAS, folio_number="N/A", raw_row_index=1, total_amount=Decimal("10000.00")
    )
    object.__setattr__(pdf_rec, "file_name", "pdf_statement.pdf")

    core_result = DummyCoreResult(
        matched_records=[
            (crm_rec, pdf_rec),
            (crm_rec, bse1),
            (crm_rec, bse2),
            (crm_rec, nse),
            (crm_rec, kfin),
            (crm_rec, cams),
        ],
        unmatched_records=[]
    )

    result = ReconciliationResult(
        metadata=metadata,
        discrepancies=[],
        excel_report_path=None,
        csv_report_path=None,
        json_report_path=None,
        matched_audits=[],
    )

    reporter = ExcelReporter(output_dir=tmp_path, run_id="multitest")
    target_file = tmp_path / "discrepancies_multitest.xlsx"
    reporter.report(
        result=result,
        core_result=core_result,
        all_validation_failures=[],
        file_path=target_file,
    )

    # Load and verify Reconciliation headers
    wb = openpyxl.load_workbook(target_file)
    ws_recon = wb["Reconciliation"]
    
    # Headers should start in row 4
    headers = [ws_recon.cell(row=4, column=c).value for c in range(1, 9)]
    expected_headers = [
        "Field",
        "CRM (reference)",
        "CAS",
        "BSE (code 123)",
        "BSE (code DHIRAJ)",
        "NSE",
        "CAMS/KFintech",
        "CAMS/KFintech"
    ]
    assert headers == expected_headers


def test_excel_reporter_unique_columns_for_multiple_similar_files(tmp_path: Path) -> None:
    """Verifies that multiple similar source files (e.g. 2 CAMS, 2 Insurance) get unique headers."""
    metadata = ReconciliationRunMetadata(
        run_id="excel-similar-test",
        timestamp="2026-06-26T12:00:00Z",
        crm_file_hash="crmhash",
        report_file_hashes={
            "cams_jan.xlsx": "h1",
            "cams_feb.xlsx": "h2",
            "hdfc_insurance.xlsx": "h3",
            "lic_insurance.xlsx": "h4"
        },
        total_crm_records=1,
        total_report_records=4,
        validation_failures_count=0,
        discrepancies_count=0,
        failed_files=[],
    )

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

    cams1 = ReportRecord(
        pan="ABCDE1234F", investor_name="Ramesh Sharma", mobile="9876543210", email="crm@test.com",
        source=RecordSource.CAMS, folio_number="N/A", raw_row_index=2, total_amount=Decimal("10000.00")
    )
    object.__setattr__(cams1, "file_name", "cams_jan.xlsx")
    object.__setattr__(cams1, "file_id", "session-cams-jan")

    cams2 = ReportRecord(
        pan="ABCDE1234F", investor_name="Ramesh Sharma", mobile="9876543210", email="crm@test.com",
        source=RecordSource.CAMS, folio_number="N/A", raw_row_index=2, total_amount=Decimal("10000.00")
    )
    object.__setattr__(cams2, "file_name", "cams_feb.xlsx")
    object.__setattr__(cams2, "file_id", "session-cams-feb")

    ins1 = ReportRecord(
        pan="ABCDE1234F", investor_name="Ramesh Sharma", mobile="9876543210", email="crm@test.com",
        source=RecordSource.INSURANCE, folio_number="N/A", raw_row_index=2, total_amount=Decimal("10000.00")
    )
    object.__setattr__(ins1, "file_name", "hdfc_insurance.xlsx")
    object.__setattr__(ins1, "file_id", "session-hdfc")

    ins2 = ReportRecord(
        pan="ABCDE1234F", investor_name="Ramesh Sharma", mobile="9876543210", email="crm@test.com",
        source=RecordSource.INSURANCE, folio_number="N/A", raw_row_index=2, total_amount=Decimal("10000.00")
    )
    object.__setattr__(ins2, "file_name", "lic_insurance.xlsx")
    object.__setattr__(ins2, "file_id", "session-lic")

    core_result = DummyCoreResult(
        matched_records=[
            (crm_rec, cams1),
            (crm_rec, cams2),
            (crm_rec, ins1),
            (crm_rec, ins2),
        ],
        unmatched_records=[]
    )

    result = ReconciliationResult(
        metadata=metadata,
        discrepancies=[],
        excel_report_path=None,
        csv_report_path=None,
        json_report_path=None,
        matched_audits=[],
    )

    reporter = ExcelReporter(output_dir=tmp_path, run_id="similartest")
    target_file = tmp_path / "discrepancies_similartest.xlsx"
    reporter.report(
        result=result,
        core_result=core_result,
        all_validation_failures=[],
        file_path=target_file,
    )

    wb = openpyxl.load_workbook(target_file)
    ws_recon = wb["Reconciliation"]
    
    headers = [ws_recon.cell(row=4, column=c).value for c in range(1, 7)]
    expected_headers = [
        "Field",
        "CRM (reference)",
        "CAMS/KFintech (Cams Feb)",
        "CAMS/KFintech (Cams Jan)",
        "SOA (Hdfc Insurance)",
        "SOA (Lic Insurance)"
    ]
    assert headers == expected_headers

