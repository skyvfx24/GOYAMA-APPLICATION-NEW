import pytest
import pandas as pd
from unittest.mock import patch
from decimal import Decimal
from datetime import date
from pathlib import Path

from mfrecon.core.config import EngineConfig, SourceProfileConfig
from mfrecon.core.domain import (
    CRMRecord,
    DiscrepancyType,
    FATCAStatus,
    InvestorStatus,
    KYCStatus,
    RecordSource,
    ReportRecord
)
from mfrecon.engine.discrepancy import compare_records, get_skipped_audit_note
from mfrecon.facade import ReconciliationEngine
from mfrecon.engine.explainability import format_explanation
from mfrecon.parsers.cams import CAMSParser
from mfrecon.parsers.kfintech import KFintechParser
from mfrecon.parsers.bse import BSEParser
from mfrecon.parsers.nse import NSEParser
from mfrecon.parsers.pdf_cas import PDFCASParser
from mfrecon.parsers.crm import CRMParser


# 1. FIELD_MISSING / FIELD_EMPTY Tests
def test_field_missing_status_cams():
    crm = CRMRecord(crm_client_id="C1", pan="A1", investor_name="N1", investor_status=InvestorStatus.ACTIVE)
    report = ReportRecord(
        source=RecordSource.CAMS, raw_row_index=1, pan="A1", investor_name="N1",
        missing_fields=["investor_status"]
    )
    profile = SourceProfileConfig(compare=["investor_status"])
    config = EngineConfig()
    discs = compare_records(crm, report, profile, config, "EXACT_PAN", 1.0)
    assert len(discs) == 1
    assert discs[0].discrepancy_type == DiscrepancyType.FIELD_MISSING
    assert discs[0].field_name == "investor_status"
    assert "missing" in discs[0].explanation


def test_field_missing_mobile_kfintech():
    crm = CRMRecord(crm_client_id="C1", pan="A1", investor_name="N1", mobile="9876543210")
    report = ReportRecord(
        source=RecordSource.KFINTECH, raw_row_index=1, pan="A1", investor_name="N1",
        missing_fields=["mobile"]
    )
    profile = SourceProfileConfig(compare=["mobile"])
    config = EngineConfig()
    discs = compare_records(crm, report, profile, config, "EXACT_PAN", 1.0)
    assert len(discs) == 1
    assert discs[0].discrepancy_type == DiscrepancyType.FIELD_MISSING
    assert discs[0].field_name == "mobile"


def test_field_missing_email_bse():
    crm = CRMRecord(crm_client_id="C1", pan="A1", investor_name="N1", email="a@b.com")
    report = ReportRecord(
        source=RecordSource.BSE, raw_row_index=1, pan="A1", investor_name="N1",
        missing_fields=["email"]
    )
    profile = SourceProfileConfig(compare=["email"])
    config = EngineConfig()
    discs = compare_records(crm, report, profile, config, "EXACT_PAN", 1.0)
    assert len(discs) == 1
    assert discs[0].discrepancy_type == DiscrepancyType.FIELD_MISSING


def test_field_empty_status_cams():
    crm = CRMRecord(crm_client_id="C1", pan="A1", investor_name="N1", investor_status=InvestorStatus.ACTIVE)
    report = ReportRecord(
        source=RecordSource.CAMS, raw_row_index=1, pan="A1", investor_name="N1",
        empty_fields=["investor_status"]
    )
    profile = SourceProfileConfig(compare=["investor_status"])
    config = EngineConfig()
    discs = compare_records(crm, report, profile, config, "EXACT_PAN", 1.0)
    assert len(discs) == 1
    assert discs[0].discrepancy_type == DiscrepancyType.FIELD_EMPTY
    assert "blank/empty" in discs[0].explanation


def test_field_empty_mobile_cams():
    crm = CRMRecord(crm_client_id="C1", pan="A1", investor_name="N1", mobile="9876543210")
    report = ReportRecord(
        source=RecordSource.CAMS, raw_row_index=1, pan="A1", investor_name="N1",
        empty_fields=["mobile"]
    )
    profile = SourceProfileConfig(compare=["mobile"])
    config = EngineConfig()
    discs = compare_records(crm, report, profile, config, "EXACT_PAN", 1.0)
    assert len(discs) == 1
    assert discs[0].discrepancy_type == DiscrepancyType.FIELD_EMPTY


def test_field_empty_email_nse():
    crm = CRMRecord(crm_client_id="C1", pan="A1", investor_name="N1", email="a@b.com")
    report = ReportRecord(
        source=RecordSource.NSE, raw_row_index=1, pan="A1", investor_name="N1",
        empty_fields=["email"]
    )
    profile = SourceProfileConfig(compare=["email"])
    config = EngineConfig()
    discs = compare_records(crm, report, profile, config, "EXACT_PAN", 1.0)
    assert len(discs) == 1
    assert discs[0].discrepancy_type == DiscrepancyType.FIELD_EMPTY


# 2. STATUS_MISMATCH Tests
def test_status_mismatch_active_inactive():
    crm = CRMRecord(crm_client_id="C1", pan="A1", investor_name="N1", investor_status=InvestorStatus.ACTIVE)
    report = ReportRecord(
        source=RecordSource.CAMS, raw_row_index=1, pan="A1", investor_name="N1",
        investor_status=InvestorStatus.INACTIVE
    )
    profile = SourceProfileConfig(compare=["investor_status"])
    config = EngineConfig()
    discs = compare_records(crm, report, profile, config, "EXACT_PAN", 1.0)
    assert len(discs) == 1
    assert discs[0].discrepancy_type == DiscrepancyType.STATUS_MISMATCH


def test_status_mismatch_active_suspended():
    crm = CRMRecord(crm_client_id="C1", pan="A1", investor_name="N1", investor_status=InvestorStatus.ACTIVE)
    report = ReportRecord(
        source=RecordSource.CAMS, raw_row_index=1, pan="A1", investor_name="N1",
        investor_status=InvestorStatus.SUSPENDED
    )
    profile = SourceProfileConfig(compare=["investor_status"])
    config = EngineConfig()
    discs = compare_records(crm, report, profile, config, "EXACT_PAN", 1.0)
    assert len(discs) == 1
    assert discs[0].discrepancy_type == DiscrepancyType.STATUS_MISMATCH


def test_status_mismatch_inactive_unknown():
    crm = CRMRecord(crm_client_id="C1", pan="A1", investor_name="N1", investor_status=InvestorStatus.INACTIVE)
    report = ReportRecord(
        source=RecordSource.CAMS, raw_row_index=1, pan="A1", investor_name="N1",
        investor_status=InvestorStatus.UNKNOWN
    )
    profile = SourceProfileConfig(compare=["investor_status"])
    config = EngineConfig()
    discs = compare_records(crm, report, profile, config, "EXACT_PAN", 1.0)
    assert len(discs) == 1
    assert discs[0].discrepancy_type == DiscrepancyType.STATUS_MISMATCH


# 3. INCOMPLETE_CRM_RECORD Tests
def test_incomplete_crm_suppressed(tmp_path: Path):
    crm_path = tmp_path / "crm.csv"
    # Create CRM record that has PAN, but missing mobile, email, kyc, fatca
    df_data = pd.DataFrame({
        "PAN": ["CMSPJ2820B"],
        "Investor Name": ["Incomplete CRM Client"],
        "Client ID": ["CRM001"],
        "Mobile": [None],
        "Email": [None],
        "KYC Status": ["UNKNOWN"],
        "FATCA Status": ["UNKNOWN"]
    })
    df_data.to_csv(crm_path, index=False)

    config = EngineConfig(output_directory=tmp_path)
    config.validation.suppress_missing_in_report_for_incomplete_crm = True
    engine = ReconciliationEngine(config)
    result = engine.run(crm_path, [])
    
    assert len(result.discrepancies) == 1
    assert result.discrepancies[0].discrepancy_type == DiscrepancyType.INCOMPLETE_CRM_RECORD
    assert result.discrepancies[0].severity == "MEDIUM"


def test_incomplete_crm_not_suppressed(tmp_path: Path):
    crm_path = tmp_path / "crm.csv"
    df_data = pd.DataFrame({
        "PAN": ["CMSPJ2820B"],
        "Investor Name": ["Incomplete CRM Client"],
        "Client ID": ["CRM001"],
        "Mobile": [None],
        "Email": [None],
        "KYC Status": ["UNKNOWN"],
        "FATCA Status": ["UNKNOWN"]
    })
    df_data.to_csv(crm_path, index=False)

    config = EngineConfig(output_directory=tmp_path)
    config.validation.suppress_missing_in_report_for_incomplete_crm = False
    engine = ReconciliationEngine(config)
    result = engine.run(crm_path, [])
    
    assert len(result.discrepancies) == 1
    assert result.discrepancies[0].discrepancy_type == DiscrepancyType.MISSING_IN_REPORT
    assert result.discrepancies[0].severity == "HIGH"


def test_incomplete_crm_multiple_mixed(tmp_path: Path):
    crm_path = tmp_path / "crm.csv"
    df_data = pd.DataFrame({
        "PAN": ["CMSPJ2820B", "ABCDE1234F"],
        "Investor Name": ["Incomplete CRM Client", "Normal Client"],
        "Client ID": ["CRM001", "CRM002"],
        "Mobile": [None, "9876543210"],
        "Email": [None, "normal@gmail.com"],
        "KYC Status": ["UNKNOWN", "VERIFIED"],
        "FATCA Status": ["UNKNOWN", "COMPLIANT"]
    })
    df_data.to_csv(crm_path, index=False)

    config = EngineConfig(output_directory=tmp_path)
    config.validation.suppress_missing_in_report_for_incomplete_crm = True
    engine = ReconciliationEngine(config)
    result = engine.run(crm_path, [])
    
    types = [d.discrepancy_type for d in result.discrepancies]
    assert DiscrepancyType.INCOMPLETE_CRM_RECORD in types
    assert DiscrepancyType.MISSING_IN_REPORT in types
    assert len(result.discrepancies) == 2


# 4. Minor Account Detection Tests
def test_minor_account_tax_status_on_behalf_of_minor():
    crm = CRMRecord(crm_client_id="C1", pan="A1", investor_name="N1", tax_status="ON BEHALF OF MINOR", is_minor_account=True)
    assert crm.is_minor_account is True
    assert crm.tax_status == "ON BEHALF OF MINOR"


def test_minor_account_tax_status_minor_only():
    crm = CRMRecord(crm_client_id="C1", pan="A1", investor_name="N1", tax_status="MINOR", is_minor_account=True)
    assert crm.is_minor_account is True


def test_minor_account_tax_status_case_insensitive():
    parser = CAMSParser()
    raw = {"TAX STATUS": "minor account"}
    mapping = {"TAX STATUS": "tax_status"}
    tax_status, is_minor = parser.check_minor_account(raw, mapping)
    assert is_minor is True
    assert tax_status == "minor account"


def test_minor_account_tax_status_none():
    parser = CAMSParser()
    raw = {"TAX STATUS": None}
    mapping = {"TAX STATUS": "tax_status"}
    tax_status, is_minor = parser.check_minor_account(raw, mapping)
    assert is_minor is False


def test_minor_account_individual():
    parser = CAMSParser()
    raw = {"TAX STATUS": "INDIVIDUAL"}
    mapping = {"TAX STATUS": "tax_status"}
    tax_status, is_minor = parser.check_minor_account(raw, mapping)
    assert is_minor is False
    assert tax_status == "INDIVIDUAL"


# 5. Status Comparison Skipping & Source Profile Awareness Tests
def test_source_profile_aware_status_skip_pdf_cas():
    crm = CRMRecord(crm_client_id="C1", pan="A1", investor_name="N1", investor_status=InvestorStatus.ACTIVE)
    report = ReportRecord(
        source=RecordSource.PDF_CAS, raw_row_index=1, pan="A1", investor_name="N1",
        investor_status=InvestorStatus.UNKNOWN
    )
    # Status (investor_status) is NOT in the compare fields
    profile = SourceProfileConfig(compare=["pan", "investor_name"])
    config = EngineConfig()
    discs = compare_records(crm, report, profile, config, "EXACT_PAN", 1.0)
    # Verify no STATUS_MISMATCH discrepancy is generated
    assert len(discs) == 0


def test_source_profile_aware_email_skip_bse():
    crm = CRMRecord(crm_client_id="C1", pan="A1", investor_name="N1", email="a@b.com")
    report = ReportRecord(
        source=RecordSource.BSE, raw_row_index=1, pan="A1", investor_name="N1",
        email=None
    )
    profile = SourceProfileConfig(compare=["pan", "investor_name"])
    config = EngineConfig()
    discs = compare_records(crm, report, profile, config, "EXACT_PAN", 1.0)
    assert len(discs) == 0


def test_source_profile_aware_fatca_skip_kfintech():
    crm = CRMRecord(crm_client_id="C1", pan="A1", investor_name="N1", fatca_status=FATCAStatus.COMPLIANT)
    report = ReportRecord(
        source=RecordSource.KFINTECH, raw_row_index=1, pan="A1", investor_name="N1",
        fatca_status=FATCAStatus.UNKNOWN
    )
    profile = SourceProfileConfig(compare=["pan", "investor_name"])
    config = EngineConfig()
    discs = compare_records(crm, report, profile, config, "EXACT_PAN", 1.0)
    assert len(discs) == 0


# 6. Audit Entry Tests
def test_audit_entry_skipped_comparisons_matched(tmp_path: Path):
    crm_path = tmp_path / "crm.csv"
    pd.DataFrame({
        "PAN": ["ABCDE1234F"], "Investor Name": ["Ramesh Sharma"], "Client ID": ["CRM01"]
    }).to_csv(crm_path, index=False)

    cams_path = tmp_path / "cams.csv"
    pd.DataFrame({
        "PAN": ["ABCDE1234F"], "Investor Name": ["Ramesh Sharma"]
    }).to_csv(cams_path, index=False)

    config = EngineConfig(output_directory=tmp_path)
    config.sources["CAMS"] = SourceProfileConfig(
        available_fields=["pan", "investor_name"],
        required_fields=["pan", "investor_name"],
        compare=["pan", "investor_name"]
    )
    engine = ReconciliationEngine(config)
    result = engine.run(crm_path, [cams_path])
    
    assert len(result.matched_audits) == 1
    audits = result.matched_audits[0].skipped_comparisons
    assert "STATUS_COMPARISON_SKIPPED" in audits
    assert "FATCA_COMPARISON_SKIPPED" in audits
    assert "EMAIL_COMPARISON_SKIPPED" in audits


def test_audit_entry_skipped_comparisons_discrepancy(tmp_path: Path):
    crm_path = tmp_path / "crm.csv"
    pd.DataFrame({
        "PAN": ["ABCDE1234F"], "Investor Name": ["Ramesh Sharma"], "Client ID": ["CRM01"]
    }).to_csv(crm_path, index=False)

    cams_path = tmp_path / "cams.csv"
    # Mismatched name
    pd.DataFrame({
        "PAN": ["ABCDE1234F"], "Investor Name": ["Ramesh Kumar Sharma"]
    }).to_csv(cams_path, index=False)

    config = EngineConfig(output_directory=tmp_path)
    config.sources["CAMS"] = SourceProfileConfig(
        available_fields=["pan", "investor_name"],
        required_fields=["pan", "investor_name"],
        compare=["pan", "investor_name"]
    )
    engine = ReconciliationEngine(config)
    result = engine.run(crm_path, [cams_path])
    
    assert len(result.discrepancies) == 1
    skipped = result.discrepancies[0].audit_trace.skipped_comparisons
    assert "STATUS_COMPARISON_SKIPPED" in skipped
    assert "FATCA_COMPARISON_SKIPPED" in skipped


# 7. Explainability Tests
def test_explainability_field_missing_status():
    exp = format_explanation("FIELD_MISSING", "investor_status", "ACTIVE", None, {"source": "CAMS"})
    assert exp == "Status column missing from CAMS source file. CRM value 'ACTIVE' could not be compared."


def test_explainability_field_empty_status():
    exp = format_explanation("FIELD_EMPTY", "investor_status", "ACTIVE", None, {"source": "CAMS"})
    assert exp == "Status column exists in CAMS but value is blank/empty. CRM value 'ACTIVE' could not be compared."


def test_explainability_incomplete_crm():
    exp = format_explanation("INCOMPLETE_CRM_RECORD", None, None, None, {"crm_client_id": "CRM01", "pan": "P1"})
    assert "incomplete" in exp
    assert "CRM Record Client ID 'CRM01'" in exp


# 8. Parsers Extraction Tests
def test_cams_parser_extracts_tax_status_and_minor(tmp_path: Path):
    cams_path = tmp_path / "cams.csv"
    pd.DataFrame({
        "PAN": ["A1"], "Investor Name": ["N1"], "Tax Status": ["ON BEHALF OF MINOR"]
    }).to_csv(cams_path, index=False)
    
    parser = CAMSParser()
    records = parser.parse(cams_path)
    assert len(records) == 1
    assert records[0].tax_status == "ON BEHALF OF MINOR"
    assert records[0].is_minor_account is True


def test_kfintech_parser_extracts_tax_status_and_minor(tmp_path: Path):
    kfin_path = tmp_path / "kfin.csv"
    pd.DataFrame({
        "PAN_NO": ["A1"], "Client Name": ["N1"], "Tax Status": ["MINOR"]
    }).to_csv(kfin_path, index=False)
    
    parser = KFintechParser()
    records = parser.parse(kfin_path)
    assert len(records) == 1
    assert records[0].tax_status == "MINOR"
    assert records[0].is_minor_account is True


def test_bse_parser_extracts_tax_status(tmp_path: Path):
    bse_path = tmp_path / "bse.csv"
    pd.DataFrame({
        "BSE_PAN": ["A1"], "BSE Client Name": ["N1"], "Tax Status": ["INDIVIDUAL"]
    }).to_csv(bse_path, index=False)
    
    parser = BSEParser()
    records = parser.parse(bse_path)
    assert len(records) == 1
    assert records[0].tax_status == "INDIVIDUAL"
    assert records[0].is_minor_account is False


def test_nse_parser_extracts_tax_status(tmp_path: Path):
    nse_path = tmp_path / "nse.csv"
    pd.DataFrame({
        "nse_pan": ["A1"], "nse_client_name": ["N1"], "Tax Status": ["INDIVIDUAL"]
    }).to_csv(nse_path, index=False)
    
    parser = NSEParser()
    records = parser.parse(nse_path)
    assert len(records) == 1
    assert records[0].tax_status == "INDIVIDUAL"


def test_pdf_cas_parser_extracts_email_and_tax_status(tmp_path: Path):
    parser = PDFCASParser()
    pdf_path = tmp_path / "mock.pdf"
    pdf_path.write_text("dummy pdf contents")
    # Mock extract_raw_blocks output
    blocks = [{"pan": "A1", "investor_name": "N1", "email": "a@b.com", "tax_status": "MINOR"}]
    with patch.object(PDFCASParser, "_extract_raw_blocks", return_value=blocks), \
         patch("pdfplumber.open"):
        # Pass a mock path
        records = parser.parse(pdf_path)
        
    assert len(records) == 1
    assert records[0].email == "a@b.com"
    assert records[0].tax_status == "MINOR"
    assert records[0].is_minor_account is True


def test_pdf_cas_parser_extracts_minor_account():
    parser = PDFCASParser()
    text = "PAN: ABCDE1234F\nName: Ramesh Sharma\nTax Status: ON BEHALF OF MINOR"
    blocks = parser._extract_raw_blocks(text)
    assert len(blocks) == 1
    assert blocks[0]["tax_status"] == "ON BEHALF OF MINOR"


def test_crm_parser_extracts_tax_status_and_minor(tmp_path: Path):
    crm_path = tmp_path / "crm.csv"
    pd.DataFrame({
        "PAN": ["A1"], "Investor Name": ["N1"], "Client ID": ["CRM01"], "Tax Status": ["MINOR"]
    }).to_csv(crm_path, index=False)
    
    parser = CRMParser()
    result = parser.parse_crm(crm_path)
    assert len(result.records) == 1
    assert result.records[0].tax_status == "MINOR"
    assert result.records[0].is_minor_account is True
