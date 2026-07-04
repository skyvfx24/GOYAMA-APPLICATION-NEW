"""Tests for mfrecon.utils hashing, logging, and facade integrations."""

from pathlib import Path

import pandas as pd
import pytest

from mfrecon.core.config import EngineConfig
from mfrecon.core.exceptions import FileAccessError
from mfrecon.facade import ReconciliationEngine
from mfrecon.utils.hash import calculate_sha256


def test_calculate_sha256(tmp_path: Path) -> None:
    """Verifies that calculate_sha256 computes correct checksums."""
    test_file = tmp_path / "hello.txt"
    test_file.write_text("Hello, Reconciliation Engine!", encoding="utf-8")

    checksum = calculate_sha256(test_file)
    assert len(checksum) == 64

    with pytest.raises(FileAccessError):
        calculate_sha256(tmp_path / "missing.txt")

def test_engine_facade_mock_run(tmp_path: Path) -> None:
    """Tests facade execution with config mappings and mock files."""
    crm_file = tmp_path / "crm_mock.csv"

    crm_data = pd.DataFrame({
        "PAN": ["ABCDE1234F"],
        "Investor Name": ["Ramesh Sharma"],
        "Client ID": ["CRM001"]
    })
    crm_data.to_csv(crm_file, index=False, encoding="utf-8")

    cams_file = tmp_path / "cams_mock.csv"
    cams_data = pd.DataFrame({
        "PAN": ["ABCDE1234F"],
        "Investor Name": ["Ramesh Sharma"],
        "Folio Number": ["F123"]
    })
    cams_data.to_csv(cams_file, index=False, encoding="utf-8")

    config = EngineConfig(output_directory=tmp_path, configure_logging=True)

    engine = ReconciliationEngine(config)
    result = engine.run(
        crm_file_path=crm_file,
        report_file_paths=[cams_file]
    )


    assert result.metadata.crm_file_hash == calculate_sha256(crm_file)
    assert result.metadata.report_file_hashes[cams_file.name] == calculate_sha256(cams_file)
    assert len(result.discrepancies) == 0
    assert result.excel_report_path == str(tmp_path / f"discrepancies_{engine.run_id}.xlsx")
    assert result.csv_report_path == str(tmp_path / f"discrepancies_{engine.run_id}.csv")
    assert result.json_report_path == str(tmp_path / f"discrepancies_{engine.run_id}.json")

    # Verify log outputs were written
    log_dir = tmp_path / "logs"
    assert (log_dir / "recon_debug.log").exists()
    assert (log_dir / "audit_recon.jsonl").exists()
