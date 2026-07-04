from datetime import date
from decimal import Decimal

from mfrecon.core.config import EngineConfig, SourceProfileConfig
from mfrecon.core.domain import (
    CRMRecord,
    DiscrepancyType,
    FATCAStatus,
    InvestorStatus,
    KYCStatus,
    RecordSource,
    ReportRecord,
)
from mfrecon.engine.discrepancy import compare_records


def test_compare_records_all_equal():
    crm = CRMRecord(
        crm_client_id="C1",
        pan="ABCDE1234F",
        investor_name="RAMESH SHARMA",
        mobile="9876543210",
        email="ramesh@gmail.com",
        kyc_status=KYCStatus.VERIFIED,
        fatca_status=FATCAStatus.COMPLIANT,
        investor_status=InvestorStatus.ACTIVE,
        last_transaction_date=date(2026, 6, 13),
        total_amount=Decimal("100.00")
    )
    report = ReportRecord(
        source=RecordSource.CAMS,
        folio_number="F123",
        raw_row_index=1,
        pan="ABCDE1234F",
        investor_name="RAMESH SHARMA",
        mobile="9876543210",
        email="ramesh@gmail.com",
        kyc_status=KYCStatus.VERIFIED,
        fatca_status=FATCAStatus.COMPLIANT,
        investor_status=InvestorStatus.ACTIVE,
        last_transaction_date=date(2026, 6, 13),
        total_amount=Decimal("100.00")
    )

    profile = SourceProfileConfig(
        available_fields=["pan", "investor_name", "mobile", "email", "kyc_status", "fatca_status", "investor_status", "last_transaction_date", "total_amount"],
        required_fields=["pan", "investor_name"],
        compare=["pan", "investor_name", "mobile", "email", "kyc_status", "fatca_status", "investor_status", "last_transaction_date", "total_amount"]
    )

    config = EngineConfig()

    res = compare_records(crm, report, profile, config, "EXACT_PAN", 1.0)
    assert len(res) == 0


def test_compare_records_mismatches():
    crm = CRMRecord(
        crm_client_id="C1",
        pan="ABCDE1234F",
        investor_name="RAMESH SHARMA",
        mobile="9876543210",
        email="ramesh@gmail.com",
        kyc_status=KYCStatus.VERIFIED,
        fatca_status=FATCAStatus.COMPLIANT,
        investor_status=InvestorStatus.ACTIVE,
        last_transaction_date=date(2026, 6, 10),
        total_amount=Decimal("100.00")
    )
    # Differences: name, mobile, date (beyond tolerance 3 days), amount (beyond epsilon 0.01)
    report = ReportRecord(
        source=RecordSource.CAMS,
        folio_number="F123",
        raw_row_index=1,
        pan="ABCDE1234F",
        investor_name="SURESH KUMAR",
        mobile="9876543211",
        email="ramesh@gmail.com",
        kyc_status=KYCStatus.VERIFIED,
        fatca_status=FATCAStatus.COMPLIANT,
        investor_status=InvestorStatus.ACTIVE,
        last_transaction_date=date(2026, 6, 15), # 5 days difference (tolerance is 3)
        total_amount=Decimal("105.00") # 5.00 difference (epsilon is 0.01)
    )

    profile = SourceProfileConfig(
        available_fields=["pan", "investor_name", "mobile", "email", "kyc_status", "fatca_status", "investor_status", "last_transaction_date", "total_amount"],
        required_fields=["pan", "investor_name"],
        compare=["pan", "investor_name", "mobile", "email", "kyc_status", "fatca_status", "investor_status", "last_transaction_date", "total_amount"]
    )

    config = EngineConfig()
    config.engine.date_days_tolerance = 3
    config.engine.amount_epsilon = 0.01

    res = compare_records(crm, report, profile, config, "EXACT_PAN", 1.0)

    # We expect mismatches in: name, mobile, last_transaction_date, total_amount
    assert len(res) == 4
    mismatches = {d.discrepancy_type for d in res}
    assert DiscrepancyType.NAME_MISMATCH in mismatches
    assert DiscrepancyType.MOBILE_MISMATCH in mismatches
    assert DiscrepancyType.DATE_MISMATCH in mismatches
    assert DiscrepancyType.AMOUNT_MISMATCH in mismatches
