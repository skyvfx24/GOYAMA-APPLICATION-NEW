import pytest

from mfrecon.normalizers.identity import normalize_name, normalize_pan


def test_normalize_pan_valid():
    assert normalize_pan("ABCDE1234F") == "ABCDE1234F"
    assert normalize_pan("abcde1234f") == "ABCDE1234F"
    assert normalize_pan("ABCDE-1234-F") == "ABCDE1234F"
    assert normalize_pan("ABCDE/1234/F") == "ABCDE1234F"
    assert normalize_pan(" ABCDE 1234 F ") == "ABCDE1234F"
    assert normalize_pan("AbCdE-1234-f") == "ABCDE1234F"

def test_normalize_pan_invalid():
    with pytest.raises(ValueError, match="Invalid PAN format"):
        normalize_pan("ABCD1234F")
    with pytest.raises(ValueError, match="Invalid PAN format"):
        normalize_pan("ABCDEF1234F")
    with pytest.raises(ValueError, match="Invalid PAN format"):
        normalize_pan("ABCDE12345")
    with pytest.raises(ValueError, match="Invalid PAN format"):
        normalize_pan("12345ABCDE")
    with pytest.raises(ValueError, match="PAN cannot be empty"):
        normalize_pan("")

def test_normalize_name_salutations():
    assert normalize_name("Mr. Ramesh Kumar Sharma") == "RAMESH KUMAR SHARMA"
    assert normalize_name("Mrs. Ramesh Kumar Sharma") == "RAMESH KUMAR SHARMA"
    assert normalize_name("Ms Ramesh Kumar") == "RAMESH KUMAR"
    assert normalize_name("Dr. Ramesh Sharma") == "RAMESH SHARMA"
    assert normalize_name("Late Ramesh Sharma") == "RAMESH SHARMA"
    assert normalize_name("M/S Ramesh Sharma") == "RAMESH SHARMA"
    assert normalize_name("M/s Ramesh Sharma") == "RAMESH SHARMA"

def test_normalize_name_joint_holders():
    assert normalize_name("Ramesh Kumar Sharma / Joint") == "RAMESH KUMAR SHARMA"
    assert normalize_name("Ramesh Kumar Sharma / Joint Holder") == "RAMESH KUMAR SHARMA"
    assert normalize_name("Ramesh Kumar Sharma / Jt") == "RAMESH KUMAR SHARMA"
    assert normalize_name("Ramesh Kumar Sharma Jt. Holder") == "RAMESH KUMAR SHARMA"
    assert normalize_name("Ramesh Kumar Sharma HUF") == "RAMESH KUMAR SHARMA"
    assert normalize_name("Late Ramesh Kumar Sharma / Jt. Holder") == "RAMESH KUMAR SHARMA"

def test_normalize_name_edge_cases():
    assert normalize_name("   ") == ""
    assert normalize_name("") == ""
    assert normalize_name("Huffman") == "HUFFMAN"  # "HUF" is inside word, word boundary regex prevents stripping
    assert normalize_name("Dr. Huffman HUF") == "HUFFMAN"
    assert normalize_name("Mr. Jt. Joint HUF") == ""
    assert normalize_name("Ramesh - Kumar, Sharma / Jt.") == "RAMESH KUMAR SHARMA"
