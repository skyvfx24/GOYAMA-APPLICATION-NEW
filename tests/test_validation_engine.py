from decimal import Decimal

from mfrecon.core.config import SourceProfileConfig
from mfrecon.core.domain import CRMRecord, FATCAStatus, InvestorStatus, KYCStatus, RecordSource, ReportRecord
from mfrecon.validators.engine import ValidationEngine


def test_validation_engine_all_clean():
    engine = ValidationEngine()

    records = [
        CRMRecord(
            crm_client_id="CRM001",
            pan="ABCDE1234F",
            investor_name="Ramesh Sharma",
            mobile="9876543210",
            email="ramesh@gmail.com",
            kyc_status=KYCStatus.VERIFIED,
            fatca_status=FATCAStatus.COMPLIANT,
            investor_status=InvestorStatus.ACTIVE,
            total_amount=Decimal("150.00")
        ),
        CRMRecord(
            crm_client_id="CRM002",
            pan="VWXYZ9876A",
            investor_name="Suresh Kumar",
            mobile="9876543211",
            email="suresh@gmail.com",
            kyc_status=KYCStatus.EXEMPT,
            fatca_status=FATCAStatus.COMPLIANT,
            investor_status=InvestorStatus.ACTIVE,
            total_amount=Decimal("250.00")
        )
    ]

    profile = SourceProfileConfig(
        available_fields=["pan", "investor_name", "mobile", "email", "kyc_status", "fatca_status", "investor_status", "total_amount"],
        required_fields=["pan", "investor_name"],
        compare=["pan", "investor_name"],
        validations=["pan_format", "mobile_format", "email_format", "kyc_status", "fatca_status", "investor_status"]
    )

    result = engine.validate_records(records, profile)

    assert len(result.valid_records) == 2
    assert len(result.invalid_records) == 0
    assert len(result.validation_failures) == 0
    assert result.metadata.total_records == 2
    assert result.metadata.valid_records == 2
    assert result.metadata.invalid_records == 0
    assert result.metadata.duplicate_records == 0


def test_validation_engine_failures_and_duplicates():
    engine = ValidationEngine()

    # 1. Valid record
    rec1 = ReportRecord(
        source=RecordSource.CAMS,
        folio_number="123",
        raw_row_index=1,
        pan="ABCDE1234F",
        investor_name="Ramesh Sharma",
        mobile="9876543210",
        email="ramesh@gmail.com",
        kyc_status=KYCStatus.VERIFIED,
        fatca_status=FATCAStatus.COMPLIANT,
        investor_status=InvestorStatus.ACTIVE,
        total_amount=Decimal("150.00")
    )
    # 2. Invalid PAN format
    rec2 = ReportRecord(
        source=RecordSource.CAMS,
        folio_number="124",
        raw_row_index=2,
        pan="INVALIDPAN",  # Bad format
        investor_name="Suresh Kumar",
        mobile="9876543211",
        email="suresh@gmail.com",
        kyc_status=KYCStatus.VERIFIED,
        fatca_status=FATCAStatus.COMPLIANT,
        investor_status=InvestorStatus.ACTIVE,
        total_amount=Decimal("250.00")
    )
    # 3. Missing required field (investor_name)
    rec3 = ReportRecord(
        source=RecordSource.CAMS,
        folio_number="125",
        raw_row_index=3,
        pan="VWXYZ9876A",
        investor_name="   ",  # Missing
        mobile="9876543212",
        email="amit@gmail.com",
        kyc_status=KYCStatus.VERIFIED,
        fatca_status=FATCAStatus.COMPLIANT,
        investor_status=InvestorStatus.ACTIVE,
        total_amount=Decimal("350.00")
    )
    # 4. Duplicate of rec1 (exact duplicate)
    rec4 = ReportRecord(
        source=RecordSource.CAMS,
        folio_number="123",  # Same key as rec1: (ABCDE1234F, 123)
        raw_row_index=4,
        pan="ABCDE1234F",
        investor_name="Ramesh Sharma",
        mobile="9876543210",
        email="ramesh@gmail.com",
        kyc_status=KYCStatus.VERIFIED,
        fatca_status=FATCAStatus.COMPLIANT,
        investor_status=InvestorStatus.ACTIVE,
        total_amount=Decimal("150.00")
    )

    profile = SourceProfileConfig(
        available_fields=["pan", "investor_name", "mobile", "email", "kyc_status", "fatca_status", "investor_status", "total_amount"],
        required_fields=["pan", "investor_name"],
        compare=["pan", "investor_name"],
        validations=["pan_format", "mobile_format", "email_format"]
    )

    result = engine.validate_records([rec1, rec2, rec3, rec4], profile)

    assert len(result.valid_records) == 1
    assert result.valid_records[0].raw_row_index == 1

    assert len(result.invalid_records) == 3
    assert len(result.validation_failures) == 3

    # Check failure details
    failures_by_row = {f["row_number"]: f for f in result.validation_failures}

    assert failures_by_row[2]["failure_type"] == "INVALID_PAN_FORMAT"
    assert failures_by_row[3]["failure_type"] == "REQUIRED_FIELD_MISSING"
    assert failures_by_row[4]["failure_type"] == "EXACT_DUPLICATE"

    assert result.metadata.total_records == 4
    assert result.metadata.valid_records == 1
    assert result.metadata.invalid_records == 3
    assert result.metadata.duplicate_records == 1
