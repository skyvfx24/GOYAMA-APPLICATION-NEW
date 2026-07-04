import pytest

from mfrecon.normalizers.contact import normalize_email, normalize_mobile


def test_normalize_mobile_valid():
    assert normalize_mobile("+91-9876543210") == "9876543210"
    assert normalize_mobile("09876543210") == "9876543210"
    assert normalize_mobile("9876543210") == "9876543210"
    assert normalize_mobile("919876543210") == "9876543210"
    assert normalize_mobile(" +91 98765 43210 ") == "9876543210"
    assert normalize_mobile("9876-543-210") == "9876543210"
    assert normalize_mobile("+91 9876-543210") == "9876543210"

def test_normalize_mobile_invalid():
    with pytest.raises(ValueError, match="Mobile number must normalize to exactly 10 digits"):
        normalize_mobile("12345")
    with pytest.raises(ValueError, match="Mobile number must normalize to exactly 10 digits"):
        normalize_mobile("123456789012")
    with pytest.raises(ValueError, match="Mobile number cannot be empty"):
        normalize_mobile("")

def test_normalize_mobile_dummy():
    with pytest.raises(ValueError, match="obvious repeating dummy"):
        normalize_mobile("9999999999")
    with pytest.raises(ValueError, match="obvious repeating dummy"):
        normalize_mobile("0000000000")
    with pytest.raises(ValueError, match="placeholder dummy"):
        normalize_mobile("1234567890")
    with pytest.raises(ValueError, match="placeholder dummy"):
        normalize_mobile("0123456789")

def test_normalize_email_valid():
    assert normalize_email(" Ramesh.K@Gmail.Com ") == "ramesh.k@gmail.com"
    assert normalize_email("test@domain.co.in") == "test@domain.co.in"
    assert normalize_email("  user.name+tag@sub.domain-name.com  ") == "user.name+tag@sub.domain-name.com"

def test_normalize_email_invalid():
    with pytest.raises(ValueError, match="Invalid email format"):
        normalize_email("invalid-email")
    with pytest.raises(ValueError, match="Invalid email format"):
        normalize_email("test@")
    with pytest.raises(ValueError, match="Invalid email format"):
        normalize_email("@domain.com")
    with pytest.raises(ValueError, match="Email cannot be empty"):
        normalize_email("")
