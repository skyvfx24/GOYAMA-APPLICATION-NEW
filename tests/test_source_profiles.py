from decimal import Decimal

from mfrecon.core.config import EngineConfig, SourceProfileConfig
from mfrecon.core.domain import CRMRecord, DiscrepancyType, FATCAStatus, KYCStatus, RecordSource, ReportRecord
from mfrecon.engine.reconciler import ReconciliationEngine


def test_source_profile_aware_comparisons_cas_pdf():
    # PDF_CAS doesn't compare email/fatca/kyc, even if they mismatch!
    reconciler = ReconciliationEngine()

    crm = CRMRecord(
        crm_client_id="C1",
        pan="ABCDE1234F",
        investor_name="RAMESH SHARMA",
        mobile="9876543210",
        email="ramesh@gmail.com",
        kyc_status=KYCStatus.VERIFIED,
        fatca_status=FATCAStatus.COMPLIANT,
        total_amount=Decimal("100.00")
    )
    # Differences: email (different), kyc_status (different)
    # But for PDF_CAS profile, we only configure compare: [pan, investor_name, mobile, total_amount]
    report = ReportRecord(
        source=RecordSource.PDF_CAS,
        folio_number="F123",
        raw_row_index=1,
        pan="ABCDE1234F",
        investor_name="RAMESH SHARMA",
        mobile="9876543210",
        email="mismatch@gmail.com",  # mismatched
        kyc_status=KYCStatus.FAILED,  # mismatched
        fatca_status=FATCAStatus.UNKNOWN,
        total_amount=Decimal("100.00")
    )

    config = EngineConfig()
    # Configure PDF_CAS profile specifically
    config.sources["PDF_CAS"] = SourceProfileConfig(
        available_fields=["pan", "investor_name", "mobile", "total_amount"],
        required_fields=["pan", "investor_name"],
        compare=["pan", "investor_name", "mobile", "total_amount"],
        validations=["pan_format", "mobile_format"]
    )

    result = reconciler.reconcile([crm], [report], config)

    # We expect 0 discrepancies because the mismatched fields (email, kyc) are bypassed in PDF_CAS profile compare list!
    assert result.statistics.discrepancy_count == 0
    assert len(result.discrepancies) == 0

    # Ensure bypassed fields are logged in audit_trace skipped_comparisons list
    # Look at matched records tuple
    assert len(result.matched_records) == 1
    # Check that skipped comparisons contains 'email', 'kyc_status', 'fatca_status', 'investor_status', 'last_transaction_date'
    # Wait, skipped comparisons can be checked in any discrepancy generated, but since there are 0, we can also check comparison logic or trace.
    # Let's generate a mismatch in name to check skipped_comparisons array:
    report.investor_name = "SURESH KUMAR"
    result_with_mismatch = reconciler.reconcile([crm], [report], config)
    assert len(result_with_mismatch.discrepancies) == 1
    disc = result_with_mismatch.discrepancies[0]
    assert disc.discrepancy_type == DiscrepancyType.NAME_MISMATCH
    assert "EMAIL_COMPARISON_SKIPPED" in disc.audit_trace.skipped_comparisons
    assert "KYC_COMPARISON_SKIPPED" in disc.audit_trace.skipped_comparisons
    assert "FATCA_COMPARISON_SKIPPED" in disc.audit_trace.skipped_comparisons
