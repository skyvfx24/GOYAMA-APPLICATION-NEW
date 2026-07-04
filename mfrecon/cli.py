"""Command Line Interface (CLI) for the Mutual Fund Reconciliation Engine."""

import argparse
import sys
from pathlib import Path

from loguru import logger

from mfrecon.core.config import EngineConfig, load_config
from mfrecon.core.exceptions import MFReconException
from mfrecon.facade import ReconciliationEngine


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """
    Parses command line arguments.

    Args:
        args: Optional list of argument strings. Defaults to sys.argv[1:].

    Returns:
        argparse.Namespace: Parsed CLI namespace arguments.
    """
    parser = argparse.ArgumentParser(
        description="Mutual Fund Reconciliation Engine CLI Utility for Goyama Financial Services."
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="CLI Command choice")

    run_parser = subparsers.add_parser("run", help="Initiate reconciliation execution pipeline")
    run_parser.add_argument(
        "--crm",
        required=True,
        help="Absolute or relative path to the CRM Master dataset file (Excel/CSV)"
    )
    run_parser.add_argument(
        "--reports",
        required=True,
        nargs="+",
        help="One or more space-separated paths to external report files (CAMS, KFintech, BSE, NSE, CAS PDF)"
    )
    run_parser.add_argument(
        "--config",
        help="Optional path to the recon_config.yaml configuration settings"
    )
    run_parser.add_argument(
        "--output",
        help="Optional override path to redirect output reports directory"
    )

    return parser.parse_args(args)


def run_reconciliation(args: argparse.Namespace) -> int:
    """
    Executes the reconciliation process using parsed arguments.

    Args:
        args: The parsed command-line arguments.

    Returns:
        int: The system exit code (0 for success, 1 for custom exception, 2 for other errors).
    """
    try:
        # Load configuration (optional file load or default object)
        if args.config:
            config_path = Path(args.config)
            config = load_config(config_path)
            logger.info(f"Loaded YAML configuration settings from: {config_path}")
        else:
            config = EngineConfig()
            logger.info("Using default engine configuration settings.")

        # Override output directory if requested
        if args.output:
            config.output_directory = Path(args.output)
            logger.info(f"Overriding output directory path: {config.output_directory}")

        # Enforce configure_logging=True for CLI execution to show logging traces
        config.configure_logging = True

        # Run E2E Engine
        engine = ReconciliationEngine(config)
        logger.info(f"Starting CLI Reconciliation execution. Run ID: {engine.run_id}")

        result = engine.run(
            crm_file_path=Path(args.crm),
            report_file_paths=[Path(p) for p in args.reports]
        )

        logger.info("Reconciliation run completed successfully.")
        print("\n==================================================")
        print("         RECONCILIATION PIPELINE SUCCESS          ")
        print("==================================================")
        print(f"Excel Report Path: {result.excel_report_path}")
        print(f"CSV Report Path  : {result.csv_report_path}")
        print(f"JSON Report Path : {result.json_report_path}")
        print("==================================================\n")

        # Cleanup log handlers
        engine.close()
        return 0

    except MFReconException as e:
        logger.error(f"Reconciliation engine failed with custom error: {e}")
        print(f"\nReconciliation Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        logger.exception(f"Reconciliation engine failed with unexpected system error: {e}")
        print(f"\nUnexpected System Error: {e}", file=sys.stderr)
        return 2


def main(args: list[str] | None = None) -> None:
    """
    CLI script entry point invoking parsing and execution.

    Args:
        args: Optional list of argument strings. Defaults to sys.argv[1:].
    """
    parsed_args = parse_args(args)
    if parsed_args.command == "run":
        exit_code = run_reconciliation(parsed_args)
        sys.exit(exit_code)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
