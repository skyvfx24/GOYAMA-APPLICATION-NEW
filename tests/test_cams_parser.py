"""Unit tests for the CAMSParser checking formatting mapping and DLQ capturing."""

from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest

from mfrecon.core.domain import KYCStatus, RecordSource
from mfrecon.core.exceptions import ParserError
from mfrecon.parsers import CAMSParser


def test_valid_cams_csv(tmp_path: Path) -> None:
    path = tmp_path / "cams_valid.csv"
    data = {
        "PAN": ["ABCDE1234F"],
        "Investor Name": ["RAMESH KUMAR"],
        "Folio Number": ["9876543/21"],
        "Total Amount": [75000.50],
        "KYC Status": ["VERIFIED"]
    }
    pd.DataFrame(data).to_csv(path, index=False)

    parser = CAMSParser()
    result = parser.parse_report(path)

    assert len(result.records) == 1
    assert result.metadata.source == RecordSource.CAMS
    assert result.records[0].pan == "ABCDE1234F"
    assert result.records[0].folio_number == "9876543/21"
    assert result.records[0].total_amount == Decimal("75000.50")
    assert result.records[0].kyc_status == KYCStatus.VERIFIED

def test_cams_validation_failure_captured(tmp_path: Path) -> None:
    path = tmp_path / "cams_bad.csv"
    data = {
        "PAN": [""],  # Missing PAN
        "Investor Name": ["RAMESH KUMAR"]
    }
    pd.DataFrame(data).to_csv(path, index=False)

    parser = CAMSParser()
    result = parser.parse_report(path)

    assert len(result.records) == 0
    assert len(result.validation_failures) == 1
    assert "Missing required fields" in result.validation_failures[0]["reason"]

def test_cams_empty_file_error(tmp_path: Path) -> None:
    path = tmp_path / "empty.csv"
    path.touch()

    parser = CAMSParser()
    with pytest.raises(ParserError):
        parser.parse_report(path)
