"""Unit tests for the Mutual Fund Reconciliation Engine command line interface (CLI)."""

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mfrecon.cli import main, parse_args, run_reconciliation
from mfrecon.core.exceptions import FileAccessError


# 1. Argument Parsing Tests
def test_cli_parser_run_subcommand() -> None:
    """Verifies that the CLI argument parser resolves the 'run' subcommand and its arguments correctly."""
    args = parse_args(["run", "--crm", "crm_file.csv", "--reports", "rep1.csv", "rep2.csv"])
    assert args.command == "run"
    assert args.crm == "crm_file.csv"
    assert args.reports == ["rep1.csv", "rep2.csv"]
    assert args.config is None
    assert args.output is None


def test_cli_parser_run_with_config_and_output() -> None:
    """Verifies parser handles optional --config and --output override parameters."""
    args = parse_args([
        "run",
        "--crm", "crm_file.csv",
        "--reports", "rep1.csv",
        "--config", "recon_config.yaml",
        "--output", "./outputs"
    ])
    assert args.command == "run"
    assert args.crm == "crm_file.csv"
    assert args.reports == ["rep1.csv"]
    assert args.config == "recon_config.yaml"
    assert args.output == "./outputs"


def test_cli_parser_missing_required_crm() -> None:
    """Verifies that running without the required --crm argument raises a SystemExit exception."""
    with pytest.raises(SystemExit):
        parse_args(["run", "--reports", "rep1.csv"])


def test_cli_parser_missing_required_reports() -> None:
    """Verifies that running without the required --reports argument raises a SystemExit exception."""
    with pytest.raises(SystemExit):
        parse_args(["run", "--crm", "crm.csv"])


# 2. Execution and Exit Code Tests
@patch("mfrecon.cli.ReconciliationEngine")
@patch("mfrecon.cli.load_config")
def test_cli_run_success(mock_load_config: MagicMock, mock_engine_cls: MagicMock) -> None:
    """Verifies that a successful reconciliation run prints output and returns exit code 0."""
    # Set up mock config
    mock_config = MagicMock()
    mock_load_config.return_value = mock_config

    # Set up mock engine
    mock_engine = MagicMock()
    mock_engine.run_id = "test-cli-run-id"
    mock_result = MagicMock()
    mock_result.excel_report_path = "outputs/disc.xlsx"
    mock_result.csv_report_path = "outputs/csv"
    mock_result.json_report_path = "outputs/disc.json"
    mock_engine.run.return_value = mock_result
    mock_engine_cls.return_value = mock_engine

    # Run cli command args
    args = parse_args(["run", "--crm", "crm.csv", "--reports", "cams.csv", "--config", "config.yaml"])
    exit_code = run_reconciliation(args)

    assert exit_code == 0
    mock_load_config.assert_called_once_with(Path("config.yaml"))
    mock_engine.run.assert_called_once_with(
        crm_file_path=Path("crm.csv"),
        report_file_paths=[Path("cams.csv")]
    )
    mock_engine.close.assert_called_once()


@patch("mfrecon.cli.ReconciliationEngine")
def test_cli_run_output_override(mock_engine_cls: MagicMock) -> None:
    """Verifies that the CLI correctly overrides the output directory in configuration settings."""
    mock_engine = MagicMock()
    mock_engine.run_id = "test-run-id"
    mock_engine.run.return_value = MagicMock()
    mock_engine_cls.return_value = mock_engine

    args = parse_args(["run", "--crm", "crm.csv", "--reports", "cams.csv", "--output", "./custom_dir"])
    exit_code = run_reconciliation(args)

    assert exit_code == 0
    # Verify constructor was called with modified EngineConfig
    called_config = mock_engine_cls.call_args[0][0]
    assert called_config.output_directory == Path("./custom_dir")


@patch("mfrecon.cli.ReconciliationEngine")
def test_cli_run_custom_exception(mock_engine_cls: MagicMock) -> None:
    """Verifies that an engine custom MFReconException is caught, logged, and returns exit code 1."""
    mock_engine = MagicMock()
    mock_engine.run_id = "test-run-id"
    mock_engine.run.side_effect = FileAccessError("Missing file access")
    mock_engine_cls.return_value = mock_engine

    args = parse_args(["run", "--crm", "crm.csv", "--reports", "cams.csv"])
    exit_code = run_reconciliation(args)

    assert exit_code == 1


@patch("mfrecon.cli.ReconciliationEngine")
def test_cli_run_unexpected_exception(mock_engine_cls: MagicMock) -> None:
    """Verifies that an unexpected runtime crash returns exit code 2."""
    mock_engine = MagicMock()
    mock_engine.run_id = "test-run-id"
    mock_engine.run.side_effect = ZeroDivisionError("Math error")
    mock_engine_cls.return_value = mock_engine

    args = parse_args(["run", "--crm", "crm.csv", "--reports", "cams.csv"])
    exit_code = run_reconciliation(args)

    assert exit_code == 2


# 3. CLI Main Interface Entry Tests
@patch("mfrecon.cli.parse_args")
def test_cli_main_invalid_subcommand(mock_parse_args: MagicMock) -> None:
    """Verifies that running with an invalid subcommand choice falls back to sys.exit(0)."""
    mock_args = argparse.Namespace(command="invalid")
    mock_parse_args.return_value = mock_args

    with pytest.raises(SystemExit) as exc_info:
        main([])
    assert exc_info.value.code == 0


@patch("mfrecon.cli.run_reconciliation")
@patch("mfrecon.cli.parse_args")
def test_cli_main_run_success(mock_parse_args: MagicMock, mock_run_recon: MagicMock) -> None:
    """Verifies that running 'run' command through main correctly executes logic and exits 0."""
    mock_args = argparse.Namespace(command="run")
    mock_parse_args.return_value = mock_args
    mock_run_recon.return_value = 0

    with pytest.raises(SystemExit) as exc_info:
        main([])
    assert exc_info.value.code == 0
    mock_run_recon.assert_called_once_with(mock_args)
