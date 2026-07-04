"""Tests for mfrecon.core.domain models and enums."""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from mfrecon.core.domain import (
    AuditTrace,
    CRMRecord,
    Discrepancy,
    DiscrepancyType,
    FATCAStatus,
    InvestorStatus,
    KYCStatus,
    RecordSource,
    ReportRecord,
)


def test_enums() -> None:
    """Verifies that all required enums have correct members."""
    assert KYCStatus.VERIFIED == "VERIFIED"
    assert FATCAStatus.COMPLIANT == "COMPLIANT"
    assert InvestorStatus.ACTIVE == "ACTIVE"
    assert DiscrepancyType.NAME_MISMATCH == "NAME_MISMATCH"
    assert RecordSource.CRM == "CRM"
    assert RecordSource.PDF_CAS == "PDF_CAS"

def test_crm_record_valid() -> None:
    """Tests creation of a valid CRMRecord."""
    record = CRMRecord(
        pan="ABCDE1234F",
        investor_name="RAMESH KUMAR",
        mobile="9876543210",
        email="ramesh@gmail.com",
        kyc_status=KYCStatus.VERIFIED,
        fatca_status=FATCAStatus.COMPLIANT,
        investor_status=InvestorStatus.ACTIVE,
        last_transaction_date=date(2026, 6, 13),
        total_amount=Decimal("150000.50"),
        crm_client_id="CRM_CLI_001"
    )
    assert record.pan == "ABCDE1234F"
    assert record.investor_name == "RAMESH KUMAR"
    assert record.crm_client_id == "CRM_CLI_001"

def test_crm_record_invalid_email() -> None:
    """Tests that an invalid email structure raises a Pydantic ValidationError."""
    with pytest.raises(ValidationError):
        CRMRecord(
            pan="ABCDE1234F",
            investor_name="RAMESH KUMAR",
            email="not-an-email",
            crm_client_id="CRM_CLI_001"
        )

def test_report_record_valid() -> None:
    """Tests creation of a valid ReportRecord."""
    record = ReportRecord(
        pan="ABCDE1234F",
        investor_name="RAMESH K SHARMA",
        source=RecordSource.CAMS,
        raw_row_index=42,
        folio_number="12345/67"
    )
    assert record.source == RecordSource.CAMS
    assert record.raw_row_index == 42
    assert record.folio_number == "12345/67"

def test_audit_trace_and_discrepancy() -> None:
    """Tests the relation between Discrepancy and AuditTrace."""
    trace = AuditTrace(
        matching_route="EXACT_PAN",
        match_confidence=1.0,
        evaluation_timestamp="2026-06-13T12:00:00Z",
        reconciler_version="1.0.0",
        rule_evaluated="pan_exact",
        skipped_comparisons=["email", "fatca_status"]
    )

    disc = Discrepancy(
        discrepancy_type=DiscrepancyType.NAME_MISMATCH,
        pan="ABCDE1234F",
        field_name="investor_name",
        crm_value="RAMESH KUMAR",
        report_value="RAMESH K SHARMA",
        severity="HIGH",
        explanation="Name similarity check was 82%, below threshold.",
        source_info={"row": "42", "file": "cams_june.csv"},
        audit_trace=trace
    )

    assert disc.discrepancy_type == DiscrepancyType.NAME_MISMATCH
    assert disc.audit_trace.skipped_comparisons == ["email", "fatca_status"]
