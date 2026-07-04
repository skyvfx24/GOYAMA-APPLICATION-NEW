import datetime
from decimal import Decimal

import pytest

from mfrecon.normalizers.date_amount import normalize_amount, normalize_date


def test_normalize_date_date_objects():
    d = datetime.date(2026, 6, 13)
    assert normalize_date(d) == d

    dt = datetime.datetime(2026, 6, 13, 10, 30)
    assert normalize_date(dt) == d


def test_normalize_date_strings():
    expected = datetime.date(2026, 6, 13)
    assert normalize_date("2026-06-13") == expected
    assert normalize_date("13-06-2026") == expected
    assert normalize_date("13/06/2026") == expected
    assert normalize_date("13-Jun-2026") == expected
    assert normalize_date("13-JUN-2026") == expected
    assert normalize_date("13-jun-2026") == expected
    assert normalize_date("13-June-2026") == expected
    assert normalize_date("2026/06/13") == expected
    assert normalize_date("Jun 13, 2026") == expected
    assert normalize_date("13 Jun 2026") == expected


def test_normalize_date_excel_serial():
    # 45000 -> 2023-03-15
    assert normalize_date(45000) == datetime.date(2023, 3, 15)
    assert normalize_date("45000") == datetime.date(2023, 3, 15)
    # 59 -> 1900-02-28
    assert normalize_date(59) == datetime.date(1900, 2, 28)
    # 61 -> 1900-03-01
    assert normalize_date(61) == datetime.date(1900, 3, 1)


def test_normalize_date_invalid():
    with pytest.raises(ValueError, match="Unable to parse date"):
        normalize_date("invalid-date-string")
    with pytest.raises(ValueError, match="Date value cannot be empty"):
        normalize_date("")
    with pytest.raises(ValueError, match="Date value cannot be None"):
        # Since signature takes Any, we must handle None
        normalize_date(None)


def test_normalize_amount_valid():
    assert normalize_amount("12,345.67") == Decimal("12345.67")
    assert normalize_amount(" 100.0 ") == Decimal("100.0")
    assert normalize_amount(100.5) == Decimal("100.5")
    assert normalize_amount(123) == Decimal("123")
    assert normalize_amount(Decimal("500.25")) == Decimal("500.25")
    assert normalize_amount("") == Decimal("0.00")
    assert normalize_amount(None) == Decimal("0.00")


def test_normalize_amount_invalid():
    with pytest.raises(ValueError, match="Invalid amount format"):
        normalize_amount("abc")
    with pytest.raises(ValueError, match="Invalid amount format"):
        normalize_amount("12.34.56")
