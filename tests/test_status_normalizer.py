from mfrecon.core.domain import FATCAStatus, InvestorStatus, KYCStatus
from mfrecon.normalizers.status import (
    normalize_fatca_status,
    normalize_investor_status,
    normalize_kyc_status,
)


def test_normalize_kyc_status():
    assert normalize_kyc_status("KYC VERIFIED") == KYCStatus.VERIFIED
    assert normalize_kyc_status("VERIFIED") == KYCStatus.VERIFIED
    assert normalize_kyc_status("ok") == KYCStatus.VERIFIED
    assert normalize_kyc_status("compliant") == KYCStatus.VERIFIED
    assert normalize_kyc_status("y") == KYCStatus.VERIFIED
    assert normalize_kyc_status("YES") == KYCStatus.VERIFIED
    assert normalize_kyc_status("verified - kyc compliant") == KYCStatus.VERIFIED

    assert normalize_kyc_status("PENDING") == KYCStatus.PENDING
    assert normalize_kyc_status("in progress") == KYCStatus.PENDING
    assert normalize_kyc_status("under process") == KYCStatus.PENDING
    assert normalize_kyc_status("submitted") == KYCStatus.PENDING
    assert normalize_kyc_status("processing") == KYCStatus.PENDING

    assert normalize_kyc_status("failed") == KYCStatus.FAILED
    assert normalize_kyc_status("rejected") == KYCStatus.FAILED
    assert normalize_kyc_status("invalid") == KYCStatus.FAILED
    assert normalize_kyc_status("no") == KYCStatus.FAILED

    assert normalize_kyc_status("exempt") == KYCStatus.EXEMPT
    assert normalize_kyc_status("PAN EXEMPT") == KYCStatus.EXEMPT
    assert normalize_kyc_status("kyc exempt") == KYCStatus.EXEMPT

    assert normalize_kyc_status("something-random") == KYCStatus.UNKNOWN
    assert normalize_kyc_status(None) == KYCStatus.UNKNOWN


def test_normalize_fatca_status():
    assert normalize_fatca_status("compliant") == FATCAStatus.COMPLIANT
    assert normalize_fatca_status("fatca compliant") == FATCAStatus.COMPLIANT
    assert normalize_fatca_status("yes") == FATCAStatus.COMPLIANT
    assert normalize_fatca_status("y") == FATCAStatus.COMPLIANT

    assert normalize_fatca_status("non_compliant") == FATCAStatus.NON_COMPLIANT
    assert normalize_fatca_status("NON-COMPLIANT") == FATCAStatus.NON_COMPLIANT
    assert normalize_fatca_status("no") == FATCAStatus.NON_COMPLIANT
    assert normalize_fatca_status("not compliant") == FATCAStatus.NON_COMPLIANT

    assert normalize_fatca_status("pending") == FATCAStatus.PENDING
    assert normalize_fatca_status("under process") == FATCAStatus.PENDING

    assert normalize_fatca_status("random") == FATCAStatus.UNKNOWN
    assert normalize_fatca_status(None) == FATCAStatus.UNKNOWN


def test_normalize_investor_status():
    assert normalize_investor_status("active") == InvestorStatus.ACTIVE
    assert normalize_investor_status("live") == InvestorStatus.ACTIVE
    assert normalize_investor_status("yes") == InvestorStatus.ACTIVE
    assert normalize_investor_status("active status") == InvestorStatus.ACTIVE

    assert normalize_investor_status("inactive") == InvestorStatus.INACTIVE
    assert normalize_investor_status("closed") == InvestorStatus.INACTIVE
    assert normalize_investor_status("n") == InvestorStatus.INACTIVE

    assert normalize_investor_status("suspended") == InvestorStatus.SUSPENDED
    assert normalize_investor_status("blocked") == InvestorStatus.SUSPENDED
    assert normalize_investor_status("frozen") == InvestorStatus.SUSPENDED

    assert normalize_investor_status("random") == InvestorStatus.UNKNOWN
    assert normalize_investor_status(None) == InvestorStatus.UNKNOWN
