"""Contact normalization functions for Mobile and Email fields."""

import re

from email_validator import EmailNotValidError, validate_email


def normalize_mobile(mobile: str) -> str:
    """
    Normalizes a mobile number to exactly 10 digits by stripping prefixes (+91, 91, 0)
    and rejects obvious placeholder or dummy numbers.

    Args:
        mobile: Raw mobile number string.

    Returns:
        str: Normalized 10-digit mobile number.

    Raises:
        ValueError: If the input is empty, doesn't normalize to 10 digits,
                    or matches obvious dummy patterns.
    """
    if not mobile:
        raise ValueError("Mobile number cannot be empty")

    # Retain only digits
    digits = re.sub(r"\D", "", mobile)

    # Strip country prefix (91 or leading 0) if it makes the string longer than 10 digits
    if len(digits) > 10:
        if digits.startswith("91"):
            digits = digits[2:]
        elif digits.startswith("0"):
            digits = digits[1:]

    # Check if we have exactly 10 digits now
    if len(digits) != 10:
        raise ValueError(f"Mobile number must normalize to exactly 10 digits: '{mobile}' (normalized: '{digits}')")

    # Reject obvious dummy numbers
    # 1. Repeating same digit (e.g. 0000000000, 9999999999)
    if len(set(digits)) == 1:
        raise ValueError(f"Mobile number is an obvious repeating dummy: '{mobile}'")

    # 2. Sequential placeholder numbers (excluding valid test case 9876543210)

    if digits in ("1234567890", "0123456789"):
        raise ValueError(f"Mobile number is a placeholder dummy: '{mobile}'")

    return digits


def normalize_email(email: str) -> str:
    """
    Normalizes and validates email addresses.

    Args:
        email: Raw email string.

    Returns:
        str: Normalized lowercase email address.

    Raises:
        ValueError: If email is empty or invalid.
    """
    if not email:
        raise ValueError("Email cannot be empty")

    cleaned = email.strip().lower()

    try:
        # Perform syntax validation using email-validator
        validation = validate_email(cleaned, check_deliverability=False)
        return validation.normalized
    except EmailNotValidError as e:
        raise ValueError(f"Invalid email format: '{email}'") from e
