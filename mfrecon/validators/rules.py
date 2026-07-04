"""Field-level format and compliance validation rules."""

import re

from email_validator import EmailNotValidError, validate_email

from mfrecon.core.domain import FATCAStatus, InvestorStatus, KYCStatus


def validate_pan_format(pan: str | None) -> bool:
    """
    Validates that a PAN is present and conforms to the standard 10-character regex.

    Args:
        pan: Raw PAN string.

    Returns:
        bool: True if valid, False otherwise.
    """
    if not pan:
        return False
    return bool(re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", pan))


def validate_email_format(email: str | None) -> bool:
    """
    Validates that an email conforms to standard RFC syntax rules.

    Args:
        email: Raw email string.

    Returns:
        bool: True if valid, False otherwise.
    """
    if not email:
        return False
    try:
        validate_email(email.strip(), check_deliverability=False)
        return True
    except EmailNotValidError:
        return False


def validate_mobile_format(mobile: str | None) -> bool:
    """
    Validates that mobile is exactly 10 digits and not a dummy sequence.

    Args:
        mobile: Mapped mobile number.

    Returns:
        bool: True if valid, False otherwise.
    """
    if not mobile:
        return False
    # Check digits only and length
    if not re.match(r"^\d{10}$", mobile):
        return False
    # Reject repeating digits
    if len(set(mobile)) == 1:
        return False
    # Reject sequential placeholders
    return mobile not in ("1234567890", "0123456789")


def validate_kyc_status(status: KYCStatus | None) -> bool:
    """
    Validates that KYC status is in the allowed set: VERIFIED, EXEMPT, PENDING.

    Args:
        status: Investor KYCStatus enum.

    Returns:
        bool: True if valid, False otherwise.
    """
    if status is None:
        return False
    return status in (KYCStatus.VERIFIED, KYCStatus.EXEMPT, KYCStatus.PENDING)


def validate_fatca_status(status: FATCAStatus | None) -> bool:
    """
    Validates that FATCA status is in the allowed set: COMPLIANT, NON_COMPLIANT, PENDING.

    Args:
        status: Investor FATCAStatus enum.

    Returns:
        bool: True if valid, False otherwise.
    """
    if status is None:
        return False
    return status in (FATCAStatus.COMPLIANT, FATCAStatus.NON_COMPLIANT, FATCAStatus.PENDING)


def validate_investor_status(status: InvestorStatus | None) -> bool:
    """
    Validates that investor status matches allowed operational enums (excluding UNKNOWN).

    Args:
        status: InvestorStatus enum.

    Returns:
        bool: True if valid, False otherwise.
    """
    if status is None:
        return False
    return status in (InvestorStatus.ACTIVE, InvestorStatus.INACTIVE, InvestorStatus.SUSPENDED)
