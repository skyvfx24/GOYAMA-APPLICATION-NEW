"""Unit tests for the PDFCASParser verifying pdfplumber text extractions and decryptions."""

from decimal import Decimal
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from mfrecon.core.exceptions import ParserError, PDFDecryptionError
from mfrecon.parsers import PDFCASParser


class MockPage:
    """Mock representing a single PDF page returned by pdfplumber."""
    def __init__(self, text: str) -> None:
        self.text = text

    def extract_text(self) -> str:
        return self.text


class MockPDF:
    """Mock representing the PDF document context manager in pdfplumber."""
    def __init__(self, pages: list[MockPage]) -> None:
        self.pages = pages

    def __enter__(self) -> "MockPDF":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass


@patch("pdfplumber.open")
def test_valid_pdf_cas_parsing(mock_open: Any, tmp_path: Path) -> None:
    """Verifies that a valid CAS PDF can extract PAN, Name, Mobile, and Amount."""
    mock_text = """
    Investor Name: RAMESH KUMAR
    PAN: ABCDE1234F
    Mobile: 919876543210
    Amount: 150000.50
    Folio Number: 12345/67
    """
    mock_open.return_value = MockPDF([MockPage(mock_text)])

    test_pdf = tmp_path / "cas.pdf"
    test_pdf.write_bytes(b"%PDF-1.4")

    parser = PDFCASParser()
    result = parser.parse_report(test_pdf)

    assert len(result.records) == 1
    assert len(result.validation_failures) == 0
    assert result.records[0].pan == "ABCDE1234F"
    assert result.records[0].investor_name == "RAMESH KUMAR"
    assert result.records[0].mobile == "9876543210"  # prefix stripped
    assert result.records[0].total_amount == Decimal("150000.50")
    assert result.records[0].folio_number == "12345/67"


@patch("pdfplumber.open")
def test_pdf_password_protected(mock_open: Any, tmp_path: Path) -> None:
    """Verifies that decryption password failures raise PDFDecryptionError."""
    # Force exception representing decryption failure
    mock_open.side_effect = Exception("password required or incorrect password")

    test_pdf = tmp_path / "protected.pdf"
    test_pdf.write_bytes(b"%PDF-1.4")

    parser = PDFCASParser()
    with pytest.raises(PDFDecryptionError):
        parser.parse_report(test_pdf)


@patch("pdfplumber.open")
def test_pdf_corrupt_structure(mock_open: Any, tmp_path: Path) -> None:
    """Verifies that general structural corruption raises ParserError."""
    mock_open.side_effect = Exception("Corrupt PDF Header structure")

    test_pdf = tmp_path / "corrupt.pdf"
    test_pdf.write_bytes(b"%PDF-1.4")

    parser = PDFCASParser()
    with pytest.raises(ParserError):
        parser.parse_report(test_pdf)


@patch("pdfplumber.open")
def test_pdf_multi_page(mock_open: Any, tmp_path: Path) -> None:
    """Verifies multi-page parsing extracts records from all page text streams."""
    page1 = MockPage("Investor Name: RAMESH KUMAR\nPAN: ABCDE1234F")
    page2 = MockPage("Investor Name: SITA SHARMA\nPAN: XYZWP5678Q")
    mock_open.return_value = MockPDF([page1, page2])

    test_pdf = tmp_path / "multipage.pdf"
    test_pdf.write_bytes(b"%PDF-1.4")

    parser = PDFCASParser()
    result = parser.parse_report(test_pdf)

    assert len(result.records) == 2
    assert result.records[0].pan == "ABCDE1234F"
    assert result.records[1].pan == "XYZWP5678Q"


@patch("pdfplumber.open")
def test_pdf_row_validation_failures(mock_open: Any, tmp_path: Path) -> None:
    """Verifies that incomplete text groups (e.g. missing name) go to failures DLQ."""
    mock_text = """
    PAN: ABCDE1234F
    Mobile: 9876543210
    """
    mock_open.return_value = MockPDF([MockPage(mock_text)])

    test_pdf = tmp_path / "partial.pdf"
    test_pdf.write_bytes(b"%PDF-1.4")

    parser = PDFCASParser()
    result = parser.parse_report(test_pdf)

    assert len(result.records) == 0
    assert len(result.validation_failures) == 1
    assert "Missing required fields" in result.validation_failures[0]["reason"]
