"""Identity normalization functions for PAN and Name fields."""

import re


def normalize_pan(pan: str) -> str:
    """
    Normalizes a Permanent Account Number (PAN) by removing spaces, hyphens, and slashes,
    converting to uppercase, and validating against the standard 10-character format.

    Args:
        pan: Raw PAN string.

    Returns:
        str: Normalized 10-character PAN in uppercase.

    Raises:
        ValueError: If the input is empty or does not conform to the PAN format.
    """
    if not pan:
        raise ValueError("PAN cannot be empty")

    # Strip spaces, hyphens, slashes
    cleaned = re.sub(r"[\s\-/]", "", pan).upper()

    # Validate regex format
    if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$", cleaned):
        raise ValueError(f"Invalid PAN format: '{pan}' (normalized: '{cleaned}')")

    return cleaned


def normalize_name(name: str) -> str:
    """
    Normalizes investor names by removing common salutations, prefixes, and joint holder suffixes,
    collapsing multiple spaces, and converting to uppercase.

    Args:
        name: Raw name string.

    Returns:
        str: Normalized uppercase name.
    """
    if not name:
        return ""

    # Convert to uppercase and strip outer whitespace
    cleaned = name.upper().strip()

    # 1. Strip joint holder suffixes (Jt, Jt., Joint, Joint Holder, etc.)
    # Use word boundary patterns matching optional dots and not followed by alphanumeric chars
    joint_patterns = [
        r"\bJOINT\s+HOLDER(?!\w)",
        r"\bJOINT(?!\w)",
        r"\bJT\.?\s+HOLDER(?!\w)",
        r"\bJT\.?(?!\w)",
    ]
    for pattern in joint_patterns:
        cleaned = re.sub(pattern, "", cleaned)

    # 2. Strip salutations and prefixes/suffixes:
    # Mr, Mrs, Ms, Dr, Late, M/S, HUF
    prefix_patterns = [
        r"\bMR\.?\b",
        r"\bMRS\.?\b",
        r"\bMS\.?\b",
        r"\bDR\.?\b",
        r"\bLATE\b",
        r"\bM/S\.?\b",
        r"\bHUF\b",
    ]
    for pattern in prefix_patterns:
        cleaned = re.sub(pattern, "", cleaned)

    # 3. Clean up separators globally (commas, dashes, slashes, periods) by replacing with spaces
    cleaned = cleaned.replace(",", " ").replace("-", " ").replace("/", " ").replace(".", " ")

    # 4. Collapse spaces
    cleaned = re.sub(r"\s+", " ", cleaned)

    return cleaned.strip()
