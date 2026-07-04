"""Unit tests for the BSEParser verifying column mapping rules."""

from decimal import Decimal
from pathlib import Path

import pandas as pd

from mfrecon.core.domain import RecordSource
from mfrecon.parsers import BSEParser


def test_valid_bse_csv(tmp_path: Path) -> None:
    path = tmp_path / "bse_valid.csv"
    data = {
        "BSE_PAN": ["ABCDE1234F"],
        "BSE Client Name": ["RAMESH KUMAR"],
        "Email": ["ramesh@gmail.com"],
        "Amount": [50000.75]
    }
    pd.DataFrame(data).to_csv(path, index=False)

    parser = BSEParser()
    result = parser.parse_report(path)

    assert len(result.records) == 1
    assert result.metadata.source == RecordSource.BSE
    assert result.records[0].pan == "ABCDE1234F"
    assert result.records[0].email == "ramesh@gmail.com"
    assert result.records[0].total_amount == Decimal("50000.75")
