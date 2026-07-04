from mfrecon.core.domain import FATCAStatus, InvestorStatus, KYCStatus
from mfrecon.validators.rules import (
    validate_email_format,
    validate_fatca_status,
    validate_investor_status,
    validate_kyc_status,
    validate_mobile_format,
    validate_pan_format,
)


def test_validate_pan_format():
    assert validate_pan_format("ABCDE1234F") is True
    assert validate_pan_format("abcde1234f") is False  # Regex matches uppercase only
    assert validate_pan_format("ABCDE12345") is False
    assert validate_pan_format("ABCDE123F") is False
    assert validate_pan_format("") is False
    assert validate_pan_format(None) is False


def test_validate_email_format():
    assert validate_email_format("ramesh@gmail.com") is True
    assert validate_email_format("ramesh.kumar+tag@domain.co.in") is True
    assert validate_email_format("ramesh@") is False
    assert validate_email_format("@gmail.com") is False
    assert validate_email_format("ramesh gmail.com") is False
    assert validate_email_format("") is False
    assert validate_email_format(None) is False


def test_validate_mobile_format():
    assert validate_mobile_format("9876543210") is True
    assert validate_mobile_format("987654321") is False  # 9 digits
    assert validate_mobile_format("98765432101") is False  # 11 digits
    assert validate_mobile_format("9999999999") is False  # Repeating dummy
    assert validate_mobile_format("1234567890") is False  # Placeholder sequential dummy
    assert validate_mobile_format("0123456789") is False  # Placeholder sequential dummy
    assert validate_mobile_format("abcdefghij") is False  # Non-digits
    assert validate_mobile_format("") is False
    assert validate_mobile_format(None) is False


def test_validate_kyc_status():
    assert validate_kyc_status(KYCStatus.VERIFIED) is True
    assert validate_kyc_status(KYCStatus.EXEMPT) is True
    assert validate_kyc_status(KYCStatus.PENDING) is True
    assert validate_kyc_status(KYCStatus.FAILED) is False
    assert validate_kyc_status(KYCStatus.UNKNOWN) is False
    assert validate_kyc_status(None) is False


def test_validate_fatca_status():
    assert validate_fatca_status(FATCAStatus.COMPLIANT) is True
    assert validate_fatca_status(FATCAStatus.NON_COMPLIANT) is True
    assert validate_fatca_status(FATCAStatus.PENDING) is True
    assert validate_fatca_status(FATCAStatus.UNKNOWN) is False
    assert validate_fatca_status(None) is False


def test_validate_investor_status():
    assert validate_investor_status(InvestorStatus.ACTIVE) is True
    assert validate_investor_status(InvestorStatus.INACTIVE) is True
    assert validate_investor_status(InvestorStatus.SUSPENDED) is True
    assert validate_investor_status(InvestorStatus.UNKNOWN) is False
    assert validate_investor_status(None) is False
