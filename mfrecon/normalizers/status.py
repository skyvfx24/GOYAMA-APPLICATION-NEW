"""Status normalizers for KYC, FATCA, and Investor statuses."""

from mfrecon.core.domain import FATCAStatus, InvestorStatus, KYCStatus


def normalize_kyc_status(status: str | None) -> KYCStatus:
    """
    Normalizes raw KYC status strings into standard KYCStatus enums.

    Args:
        status: Raw KYC status representation.

    Returns:
        KYCStatus: Normalized KYC status.
    """
    if not status:
        return KYCStatus.UNKNOWN

    val = str(status).strip().upper()

    # Map verified statuses
    if val in ("VERIFIED", "KYC VERIFIED", "OK", "COMPLIANT", "Y", "YES", "KYC COMPLIANT", "VERIFIED - KYC COMPLIANT"):
        return KYCStatus.VERIFIED

    # Map pending statuses
    if val in ("PENDING", "IN PROGRESS", "UNDER PROCESS", "SUBMITTED", "PROCESSING"):
        return KYCStatus.PENDING

    # Map failed statuses
    if val in ("FAILED", "REJECTED", "NOT VERIFIED", "INVALID", "NO", "N"):
        return KYCStatus.FAILED

    # Map exempt statuses
    if val in ("EXEMPT", "KYC EXEMPT", "PAN EXEMPT"):
        return KYCStatus.EXEMPT

    return KYCStatus.UNKNOWN


def normalize_fatca_status(status: str | None) -> FATCAStatus:
    """
    Normalizes raw FATCA status strings into standard FATCAStatus enums.

    Args:
        status: Raw FATCA status representation.

    Returns:
        FATCAStatus: Normalized FATCA status.
    """
    if not status:
        return FATCAStatus.UNKNOWN

    val = str(status).strip().upper()

    # Map compliant statuses
    if val in ("COMPLIANT", "FATCA COMPLIANT", "YES", "Y", "OK"):
        return FATCAStatus.COMPLIANT

    # Map non-compliant statuses
    if val in ("NON_COMPLIANT", "NON-COMPLIANT", "NO", "N", "NOT COMPLIANT"):
        return FATCAStatus.NON_COMPLIANT

    # Map pending statuses
    if val in ("PENDING", "UNDER PROCESS", "PROCESSING"):
        return FATCAStatus.PENDING

    return FATCAStatus.UNKNOWN


def normalize_investor_status(status: str | None) -> InvestorStatus:
    """
    Normalizes raw investor status strings into standard InvestorStatus enums.

    Args:
        status: Raw investor status representation.

    Returns:
        InvestorStatus: Normalized investor status.
    """
    if not status:
        return InvestorStatus.UNKNOWN

    val = str(status).strip().upper()

    # Map active statuses
    if val in ("ACTIVE", "LIVE", "Y", "YES", "ACTIVE STATUS"):
        return InvestorStatus.ACTIVE

    # Map inactive statuses
    if val in ("INACTIVE", "CLOSED", "NO", "N"):
        return InvestorStatus.INACTIVE

    # Map suspended statuses
    if val in ("SUSPENDED", "BLOCKED", "FROZEN"):
        return InvestorStatus.SUSPENDED

    return InvestorStatus.UNKNOWN
