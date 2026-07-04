"""Unit tests for the ParserRegistry class, checking registration and auto-detection logic."""

from pathlib import Path

import pandas as pd
import pytest

from mfrecon.core.exceptions import ParserError
from mfrecon.parsers import BaseParser, CAMSParser, ParserRegistry, PDFCASParser, default_registry


class MockCustomParser(BaseParser):
    def parse(self, file_path: Path):
        return []

def test_manual_registration_and_lookup() -> None:
    """Verifies that custom parsers can be registered and retrieved."""
    registry = ParserRegistry()
    registry.register("MOCK", MockCustomParser)

    parser = registry.get("MOCK")
    assert isinstance(parser, MockCustomParser)

def test_lookup_missing_parser_raises_error() -> None:
    """Verifies that requesting an unregistered parser raises ParserError."""
    registry = ParserRegistry()
    with pytest.raises(ParserError):
        registry.get("NON_EXISTENT")

def test_auto_detect_pdf_extension(tmp_path: Path) -> None:
    """Verifies that PDF files are auto-routed to the PDFCASParser."""
    pdf_file = tmp_path / "statement.pdf"
    pdf_file.touch()

    parser = default_registry.detect_parser(pdf_file)
    assert isinstance(parser, PDFCASParser)

def test_auto_detect_cams_csv(tmp_path: Path) -> None:
    """Verifies CAMS detection from CSV headers."""
    csv_file = tmp_path / "cams_report.csv"
    df = pd.DataFrame({"PAN": [], "Investor Name": [], "Folio Number": []})
    df.to_csv(csv_file, index=False)

    parser = default_registry.detect_parser(csv_file)
    assert isinstance(parser, CAMSParser)

def test_auto_detect_unsupported_type(tmp_path: Path) -> None:
    """Verifies that unsupported file formats raise ParserError."""
    text_file = tmp_path / "report.txt"
    text_file.touch()

    with pytest.raises(ParserError):
        default_registry.detect_parser(text_file)
