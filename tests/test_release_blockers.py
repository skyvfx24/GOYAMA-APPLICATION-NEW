"""Comprehensive unit tests for release blockers: logging isolation, path types, exception wrapping, and config loading."""

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import loguru
import pandas as pd
import pytest

from mfrecon import (
    EngineConfig,
    ReconciliationEngine,
    ReconciliationResult,
    load_config,
    load_config_from_dict,
)
from mfrecon.core.exceptions import ConfigurationError, FileAccessError, ParserError


# 1. Package Root Namespace Tests
def test_package_root_namespace_exports() -> None:
    """Verifies that the core classes and loader functions are correctly exposed at the root namespace."""
    assert ReconciliationEngine is not None
    assert EngineConfig is not None
    assert load_config is not None
    assert load_config_from_dict is not None
    assert ReconciliationResult is not None


# 2. Config Dictionary Loader Tests
def test_config_loader_from_dict_success() -> None:
    """Verifies load_config_from_dict successfully parses a valid dictionary configuration."""
    config_dict = {
        "output_directory": "outputs_test",
        "configure_logging": True,
        "engine": {
            "run_mode": "TOLERANT",
            "amount_epsilon": 0.05,
            "date_days_tolerance": 5,
        },
    }
    config = load_config_from_dict(config_dict)
    assert isinstance(config, EngineConfig)
    assert config.output_directory == Path("outputs_test")
    assert config.configure_logging is True
    assert config.engine.run_mode == "TOLERANT"
    assert config.engine.amount_epsilon == 0.05
    assert config.engine.date_days_tolerance == 5


def test_config_loader_from_dict_invalid() -> None:
    """Verifies load_config_from_dict raises a wrapped ConfigurationError on schema validation mismatch."""
    invalid_dict = {
        "engine": {
            "amount_epsilon": "not-a-float",  # triggers schema validation error
        }
    }
    with pytest.raises(ConfigurationError) as exc_info:
        load_config_from_dict(invalid_dict)
    assert "Configuration validation failed" in str(exc_info.value)


# Helper function to generate test CSV files
def _create_csv(path: Path, data: dict[str, list[Any]]) -> None:
    pd.DataFrame(data).to_csv(path, index=False, encoding="utf-8")


# 3. Path Handling Tests
def test_run_with_string_paths(tmp_path: Path) -> None:
    """Verifies the facade run method correctly supports path parameters passed as string objects."""
    crm_file = tmp_path / "crm_string.csv"
    _create_csv(crm_file, {
        "PAN": ["ABCDE1234F"],
        "Investor Name": ["Ramesh Kumar"],
        "Client ID": ["CRM001"],
    })

    cams_file = tmp_path / "cams_string.csv"
    _create_csv(cams_file, {
        "PAN": ["ABCDE1234F"],
        "Investor Name": ["Ramesh Kumar"],
        "Folio Number": ["999"],
    })

    config = EngineConfig(output_directory=tmp_path, configure_logging=False)
    engine = ReconciliationEngine(config)

    # Call facade with raw strings
    result = engine.run(str(crm_file), [str(cams_file)])
    assert isinstance(result, ReconciliationResult)
    assert result.excel_report_path is not None
    assert Path(result.excel_report_path).exists()


def test_run_with_mixed_paths(tmp_path: Path) -> None:
    """Verifies the facade run method correctly supports mixed string and Path objects."""
    crm_file = tmp_path / "crm_mixed.csv"
    _create_csv(crm_file, {
        "PAN": ["ABCDE1234F"],
        "Investor Name": ["Ramesh Kumar"],
        "Client ID": ["CRM001"],
    })

    cams_file = tmp_path / "cams_mixed.csv"
    _create_csv(cams_file, {
        "PAN": ["ABCDE1234F"],
        "Investor Name": ["Ramesh Kumar"],
    })

    config = EngineConfig(output_directory=tmp_path, configure_logging=False)
    engine = ReconciliationEngine(config)

    # Mixed inputs: crm is str, cams is Path
    result = engine.run(str(crm_file), [cams_file])
    assert isinstance(result, ReconciliationResult)
    assert result.csv_report_path is not None
    assert Path(result.csv_report_path).exists()


# 4. CRM Ingestion Error Wrapping Tests
def test_crm_missing_file_raises_file_access_error(tmp_path: Path) -> None:
    """Verifies that a missing CRM file raises a clean FileAccessError instead of a raw OSError."""
    config = EngineConfig(output_directory=tmp_path, configure_logging=False)
    engine = ReconciliationEngine(config)
    missing_path = tmp_path / "non_existent_crm.csv"

    with pytest.raises(FileAccessError) as exc_info:
        engine.run(missing_path, [])
    assert "CRM master file does not exist" in str(exc_info.value)


def test_crm_empty_file_raises_parser_error(tmp_path: Path) -> None:
    """Verifies that an empty CRM file raises a clean ParserError."""
    config = EngineConfig(output_directory=tmp_path, configure_logging=False)
    engine = ReconciliationEngine(config)

    crm_empty = tmp_path / "crm_empty.csv"
    crm_empty.touch()  # creates a 0-byte empty file

    with pytest.raises(ParserError) as exc_info:
        engine.run(crm_empty, [])
    assert "CRM file is empty" in str(exc_info.value)


def test_crm_corrupt_file_raises_parser_error(tmp_path: Path) -> None:
    """Verifies that a corrupt CRM Excel file raises a wrapped ParserError and tracebacks are handled."""
    config = EngineConfig(output_directory=tmp_path, configure_logging=False)
    engine = ReconciliationEngine(config)

    crm_corrupt = tmp_path / "crm_corrupt.xlsx"
    crm_corrupt.write_text("THIS IS NOT A VALID EXCEL FILE STRUCTURE", encoding="utf-8")

    with pytest.raises(ParserError) as exc_info:
        engine.run(crm_corrupt, [])
    assert "Excel file format cannot be determined" in str(exc_info.value) or "Failed to read file" in str(exc_info.value)


def test_crm_invalid_schema_raises_parser_error(tmp_path: Path) -> None:
    """Verifies that a CRM file with missing columns raises a clean SchemaMismatchError/ParserError."""
    config = EngineConfig(output_directory=tmp_path, configure_logging=False)
    engine = ReconciliationEngine(config)

    crm_bad_schema = tmp_path / "crm_bad_schema.csv"
    # missing Client ID / investor name completely
    _create_csv(crm_bad_schema, {
        "BAD_COLUMN": [1, 2, 3]
    })

    with pytest.raises(ParserError) as exc_info:
        engine.run(crm_bad_schema, [])
    assert "Missing required columns" in str(exc_info.value) or "Column resolution failed" in str(exc_info.value)



def test_crm_locked_file_permission_raises_file_access_error(tmp_path: Path) -> None:
    """Verifies that a locked CRM file (triggering PermissionError) raises a clean wrapped error."""
    config = EngineConfig(output_directory=tmp_path, configure_logging=False)
    engine = ReconciliationEngine(config)

    crm_locked = tmp_path / "crm_locked.csv"
    _create_csv(crm_locked, {
        "PAN": ["ABCDE1234F"],
        "Investor Name": ["Ramesh Kumar"],
        "Client ID": ["CRM001"],
    })

    # Mock open function to throw PermissionError on file access
    with patch("builtins.open", side_effect=PermissionError("File locked by another process")), pytest.raises(FileAccessError):
        engine.run(crm_locked, [])


# 5. Logging Isolation and Safety Tests
def test_opt_in_logging_disabled(tmp_path: Path) -> None:
    """Verifies that when configure_logging is False, no loguru handlers are added."""
    initial_handlers_count = len(loguru.logger._core.handlers)  # type: ignore

    config = EngineConfig(output_directory=tmp_path, configure_logging=False)
    engine = ReconciliationEngine(config)

    final_handlers_count = len(loguru.logger._core.handlers)  # type: ignore
    assert final_handlers_count == initial_handlers_count

    engine.close()


def test_opt_in_logging_enabled_and_deregistered(tmp_path: Path) -> None:
    """Verifies that when configure_logging is True, custom handlers are added, then deregistered on close."""
    initial_handlers_count = len(loguru.logger._core.handlers)  # type: ignore

    config = EngineConfig(output_directory=tmp_path, configure_logging=True)
    engine = ReconciliationEngine(config)

    added_handlers_count = len(loguru.logger._core.handlers)  # type: ignore
    assert added_handlers_count > initial_handlers_count

    # Cleanup manually
    engine.close()
    cleaned_handlers_count = len(loguru.logger._core.handlers)  # type: ignore
    assert cleaned_handlers_count == initial_handlers_count


def test_existing_application_log_handlers_preserved(tmp_path: Path) -> None:
    """Verifies that configuring library logging does not remove pre-existing application log handlers."""
    # Register a dummy handler representing host application configuration
    dummy_log_records: list[Any] = []
    dummy_handler_id = loguru.logger.add(dummy_log_records.append, level="INFO")

    try:
        # Configure engine logging
        config = EngineConfig(output_directory=tmp_path, configure_logging=True)
        engine = ReconciliationEngine(config)

        # Log some message
        loguru.logger.info("Host application message")

        # Verify host handler still received the log
        assert any("Host application message" in record for record in dummy_log_records)
        engine.close()
    finally:
        loguru.logger.remove(dummy_handler_id)


def test_library_logging_isolation(tmp_path: Path) -> None:
    """Verifies that library handlers configure filters to isolate only mfrecon logging statements."""
    config = EngineConfig(output_directory=tmp_path, configure_logging=True)
    engine = ReconciliationEngine(config)

    # Log statement outside the library namespace
    loguru.logger.info("External logging test message")

    # Clean handlers and write files
    engine.close()

    debug_log_path = tmp_path / "logs" / "recon_debug.log"
    json_log_path = tmp_path / "logs" / "audit_recon.jsonl"

    assert debug_log_path.exists()
    assert json_log_path.exists()

    # Verify that external logging message is NOT captured in isolated library files
    debug_content = debug_log_path.read_text(encoding="utf-8")
    assert "External logging test message" not in debug_content

    # Verify that JSON log does not capture external message
    with json_log_path.open("r", encoding="utf-8") as f:
        json_lines = [json.loads(line) for line in f if line.strip()]
    for line in json_lines:
        text = line.get("record", {}).get("message", "")
        assert "External logging test message" not in text
