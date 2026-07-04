"""Unit tests for the NSEParser verifying NSE column mappings."""

from decimal import Decimal
from pathlib import Path

import pandas as pd

from mfrecon.core.domain import RecordSource
from mfrecon.parsers import NSEParser


def test_valid_nse_xlsx(tmp_path: Path) -> None:
    path = tmp_path / "nse_valid.xlsx"
    data = {
        "nse_pan": ["ABCDE1234F"],
        "nse_client_name": ["RAMESH KUMAR"],
        "Mobile": ["9876543210"],
        "Email": ["ramesh@gmail.com"],
        "Balance": [25000.00]
    }
    pd.DataFrame(data).to_excel(path, index=False)

    parser = NSEParser()
    result = parser.parse_report(path)

    assert len(result.records) == 1
    assert result.metadata.source == RecordSource.NSE
    assert result.records[0].pan == "ABCDE1234F"
    assert result.records[0].mobile == "9876543210"
    assert result.records[0].total_amount == Decimal("25000.00")
