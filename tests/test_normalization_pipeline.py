import datetime
from decimal import Decimal

from mfrecon.core.domain import CRMRecord, FATCAStatus, InvestorStatus, KYCStatus, RecordSource, ReportRecord
from mfrecon.normalizers.pipeline import NormalizationPipeline


def test_normalize_crm_record():
    pipeline = NormalizationPipeline()

    raw_record = CRMRecord(
        crm_client_id="CRM123",
        pan=" abcde-1234-f ",
        investor_name="Mr. Ramesh Kumar Sharma / Jt",
        mobile=" +91-9876543210 ",
        email=" Ramesh.K@Gmail.Com ",
        kyc_status=KYCStatus.UNKNOWN,  # Pydantic validates enums at initialization, but pipeline normalizes the string representation when converting
        fatca_status=FATCAStatus.UNKNOWN,
        investor_status=InvestorStatus.UNKNOWN,
        last_transaction_date=None,
        total_amount=Decimal("12345.67")
    )

    # Note: When instantiating CRMRecord, Pydantic will validate types (like converting total_amount to Decimal).
    # We will pass raw inputs that already pass the Pydantic type check, and use pipeline to sanitize them.
    # To test raw string status conversion, we can create a record with actual raw statuses if they are mapped via enums.
    # Let's verify enums mappings:
    raw_record.kyc_status = "kyc verified"  # type: ignore[assignment]
    raw_record.fatca_status = "compliant"  # type: ignore[assignment]
    raw_record.investor_status = "active"  # type: ignore[assignment]
    raw_record.last_transaction_date = "13-Jun-2026"  # type: ignore[assignment]

    normalized = pipeline.normalize_crm_record(raw_record)

    # Check normalization results
    assert normalized.crm_client_id == "CRM123"
    assert normalized.pan == "ABCDE1234F"
    assert normalized.investor_name == "RAMESH KUMAR SHARMA"
    assert normalized.mobile == "9876543210"
    assert normalized.email == "ramesh.k@gmail.com"
    assert normalized.kyc_status == KYCStatus.VERIFIED
    assert normalized.fatca_status == FATCAStatus.COMPLIANT
    assert normalized.investor_status == InvestorStatus.ACTIVE
    assert normalized.last_transaction_date == datetime.date(2026, 6, 13)
    assert normalized.total_amount == Decimal("12345.67")

    # Check that original object was not mutated
    assert raw_record.pan == " abcde-1234-f "
    assert raw_record.investor_name == "Mr. Ramesh Kumar Sharma / Jt"
    assert raw_record.mobile == " +91-9876543210 "
    assert raw_record.email == "Ramesh.K@gmail.com"
    assert raw_record.kyc_status == "kyc verified"


def test_normalize_report_record():
    pipeline = NormalizationPipeline()

    raw_record = ReportRecord(
        source=RecordSource.CAMS,
        folio_number="123456/78",
        raw_row_index=15,
        pan=" abcde-1234-f ",
        investor_name="Mr. Ramesh Kumar Sharma / Jt",
        mobile=" +91-9876543210 ",
        email=" Ramesh.K@Gmail.Com ",
        kyc_status=KYCStatus.UNKNOWN,
        fatca_status=FATCAStatus.UNKNOWN,
        investor_status=InvestorStatus.UNKNOWN,
        last_transaction_date=None,
        total_amount=Decimal("12345.67")
    )

    raw_record.kyc_status = "kyc verified"  # type: ignore[assignment]
    raw_record.fatca_status = "compliant"  # type: ignore[assignment]
    raw_record.investor_status = "active"  # type: ignore[assignment]
    raw_record.last_transaction_date = "13-Jun-2026"  # type: ignore[assignment]

    normalized = pipeline.normalize_report_record(raw_record)

    assert normalized.source == RecordSource.CAMS
    assert normalized.folio_number == "123456/78"
    assert normalized.raw_row_index == 15
    assert normalized.pan == "ABCDE1234F"
    assert normalized.investor_name == "RAMESH KUMAR SHARMA"
    assert normalized.mobile == "9876543210"
    assert normalized.email == "ramesh.k@gmail.com"
    assert normalized.kyc_status == KYCStatus.VERIFIED
    assert normalized.fatca_status == FATCAStatus.COMPLIANT
    assert normalized.investor_status == InvestorStatus.ACTIVE
    assert normalized.last_transaction_date == datetime.date(2026, 6, 13)
    assert normalized.total_amount == Decimal("12345.67")

    # Check that original object was not mutated
    assert raw_record.pan == " abcde-1234-f "


def test_pipeline_optional_fields():
    pipeline = NormalizationPipeline()

    raw_record = CRMRecord(
        crm_client_id="CRM123",
        pan="ABCDE1234F",
        investor_name="Ramesh Sharma",
        mobile=None,
        email=None,
        kyc_status=KYCStatus.UNKNOWN,
        fatca_status=FATCAStatus.UNKNOWN,
        investor_status=InvestorStatus.UNKNOWN,
        last_transaction_date=None,
        total_amount=Decimal("0.00")
    )

    normalized = pipeline.normalize_crm_record(raw_record)
    assert normalized.mobile is None
    assert normalized.email is None
    assert normalized.last_transaction_date is None
