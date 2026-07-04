"""Structured logging configuration for the reconciliation library."""

import sys
from pathlib import Path
from typing import Any

from loguru import logger


def setup_logger(log_directory: Path, run_id: str) -> list[int]:
    """
    Configures the Loguru logger.

    Prints human-readable logs to sys.stderr, writes detailed debug traces to
    recon_debug.log, and writes structured JSON logs to audit_recon.jsonl.
    Only captures log records from within the mfrecon library.

    Args:
        log_directory: Directory path where logs should be written.
        run_id: Unique UUID associated with the reconciliation run.

    Returns:
        list[int]: List of handler IDs added.
    """
    log_directory.mkdir(parents=True, exist_ok=True)

    handler_ids = []

    def mfrecon_filter(record: Any) -> bool:
        return str(record.get("name", "")).startswith("mfrecon")

    # 1. Console handler for standard stdout/stderr
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    h1 = logger.add(
        sys.stderr,
        format=console_format,
        level="INFO",
        filter=mfrecon_filter
    )
    handler_ids.append(h1)

    # 2. File rotating handler for detailed debugging trace
    h2 = logger.add(
        str(log_directory / "recon_debug.log"),
        rotation="10 MB",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        enqueue=True,
        filter=mfrecon_filter
    )
    handler_ids.append(h2)

    # 3. Structured JSON lines audit trail
    h3 = logger.add(
        str(log_directory / "audit_recon.jsonl"),
        serialize=True,
        level="INFO",
        enqueue=True,
        filter=mfrecon_filter
    )
    handler_ids.append(h3)

    # Configure extra fields for contextual JSON logs
    logger.configure(extra={"run_id": run_id})

    return handler_ids

