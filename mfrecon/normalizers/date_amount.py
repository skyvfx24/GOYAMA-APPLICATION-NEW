"""Date and Amount normalization functions."""

import datetime
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any


def normalize_date(val: Any) -> date:
    """
    Normalizes multiple input types and date format strings (including Excel serial dates)
    into standard Python datetime.date objects.

    Args:
        val: Input representation of a date (date, datetime, str, int, float).

    Returns:
        date: Standardized Python date object.

    Raises:
        ValueError: If input is empty, null, or format cannot be parsed.
    """
    if val is None:
        raise ValueError("Date value cannot be None")

    # If already a datetime or date, extract and return date portion
    if isinstance(val, datetime.datetime):
        return val.date()
    if isinstance(val, date):
        return val

    val_str = str(val).strip()
    if not val_str:
        raise ValueError("Date value cannot be empty")

    # Check for Excel serial date representation (integer or float string)
    try:
        if re.match(r"^\d+(?:\.\d+)?$", val_str):
            serial_val = float(val_str)
            # Safe boundary check for Excel serial dates (years 1900 to 2173)
            if 1 <= serial_val <= 100000:
                days = int(serial_val)
                # Excel leap year bug adjustment (Excel incorrectly thinks 1900 was a leap year)
                if days < 60:
                    return date(1899, 12, 31) + datetime.timedelta(days=days)
                return date(1899, 12, 30) + datetime.timedelta(days=days)
    except Exception:
        pass

    # Try standard string date formats
    formats = [
        "%Y-%m-%d",      # YYYY-MM-DD
        "%d-%m-%Y",      # DD-MM-YYYY
        "%d/%m/%Y",      # DD/MM/YYYY
        "%d-%b-%Y",      # DD-Mon-YYYY (e.g. 13-Jun-2026)
        "%d-%B-%Y",      # DD-Month-YYYY
        "%Y/%m/%d",      # YYYY/MM/DD
        "%b %d, %Y",     # Mon DD, YYYY (e.g. Jun 13, 2026)
        "%d %b %Y",      # DD Mon YYYY
    ]

    for fmt in formats:
        try:
            dt = datetime.datetime.strptime(val_str, fmt)
            return dt.date()
        except ValueError:
            continue

    # Try case-insensitive strptime for formats containing short-month name variations
    for fmt in formats:
        if "%b" in fmt or "%B" in fmt:
            try:
                # Convert first letter of month to capitalized (e.g. JUN -> Jun)
                # But since month names can be anywhere, strptime case-insensitivity depends on locale.
                # In Python on Windows, strptime is generally locale-dependent.
                # To be bulletproof, try title-casing the string
                dt = datetime.datetime.strptime(val_str.title(), fmt)
                return dt.date()
            except ValueError:
                continue

    raise ValueError(f"Unable to parse date: '{val}'")


def normalize_amount(val: Any) -> Decimal:
    """
    Converts raw amounts to Decimal objects by stripping spaces and commas.

    Args:
        val: Input representation of amount (str, float, int, Decimal).

    Returns:
        Decimal: Normalized Decimal value preserving exact scale/precision.

    Raises:
        ValueError: If input is invalid.
    """
    if val is None:
        return Decimal("0.00")

    if isinstance(val, Decimal):
        return val

    val_str = str(val).replace(",", "").strip()
    if not val_str:
        return Decimal("0.00")

    try:
        return Decimal(val_str)
    except InvalidOperation as e:
        raise ValueError(f"Invalid amount format: '{val}'") from e
