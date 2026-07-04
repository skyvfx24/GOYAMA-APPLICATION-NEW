"""Unit tests for the KFintechParser verifying standard field mapping schemas."""

from decimal import Decimal
from pathlib import Path

import pandas as pd

from mfrecon.core.domain import RecordSource
from mfrecon.parsers import KFintechParser


def test_valid_kfintech_excel(tmp_path: Path) -> None:
    path = tmp_path / "kfin_valid.xlsx"
    data = {
        "PAN_NO": ["ABCDE1234F"],
        "Client Name": ["SITA SHARMA"],
        "Folio": ["12345/67"],
        "Amount": [120000.00]
    }
    pd.DataFrame(data).to_excel(path, index=False)

    parser = KFintechParser()
    result = parser.parse_report(path)

    assert len(result.records) == 1
    assert result.metadata.source == RecordSource.KFINTECH
    assert result.records[0].pan == "ABCDE1234F"
    assert result.records[0].investor_name == "SITA SHARMA"
    assert result.records[0].total_amount == Decimal("120000.00")

def test_kfintech_row_failure_captured(tmp_path: Path) -> None:
    path = tmp_path / "kfin_bad.csv"
    data = {
        "PAN_NO": ["ABCDE1234F"],
        "Client Name": [""]  # Missing Name
    }
    pd.DataFrame(data).to_csv(path, index=False)

    parser = KFintechParser()
    result = parser.parse_report(path)

    assert len(result.records) == 0
    assert len(result.validation_failures) == 1
