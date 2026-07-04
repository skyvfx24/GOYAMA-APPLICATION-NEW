"""Facade entry point for the reconciliation engine."""

import contextlib
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from loguru import logger

from mfrecon.core.config import EngineConfig, SourceProfileConfig
from mfrecon.core.domain import (
    FileFailure,
    ReconciliationResult,
    ReconciliationRunMetadata,
)
from mfrecon.core.exceptions import FileAccessError, ParserError, PDFDecryptionError
from mfrecon.engine.reconciler import ReconciliationEngine as CoreReconciler
from mfrecon.normalizers.pipeline import NormalizationPipeline
from mfrecon.parsers import default_registry
from mfrecon.parsers.crm import CRMParser
from mfrecon.reporters.csv import CSVReporter
from mfrecon.reporters.excel import ExcelReporter
from mfrecon.reporters.json_reporter import JSONReporter
from mfrecon.utils.hash import calculate_sha256
from mfrecon.utils.logging import setup_logger
from mfrecon.validators.engine import ValidationEngine


class ReconciliationEngine:
    """
    Main facade class orchestrating the Mutual Fund Reconciliation Engine library.

    Provides programmatic access for CRM integrations to initiate runs.
    """

    def __init__(self, config: EngineConfig) -> None:
        """
        Initializes the ReconciliationEngine.

        Args:
            config: EngineConfig validation container loaded from config YAML.
        """
        self.config = config
        self.run_id = str(uuid.uuid4())
        self.log_handlers: list[int] = []

        # Configure logging for this reconciliation run session if opt-in enabled
        if self.config.configure_logging:
            log_dir = self.config.output_directory / "logs"
            self.log_handlers = setup_logger(log_directory=log_dir, run_id=self.run_id)
            logger.info(f"Reconciliation Engine initialized with Run ID: {self.run_id}")
        else:
            logger.info(f"Reconciliation Engine initialized (logging config disabled) with Run ID: {self.run_id}")

    def close(self) -> None:
        """Deregisters any log handlers configured by this engine instance."""
        if hasattr(self, "log_handlers"):
            for h_id in self.log_handlers:
                with contextlib.suppress(ValueError):
                    logger.remove(h_id)
            self.log_handlers = []

    def __del__(self) -> None:
        """Cleans up log handlers on garbage collection."""
        self.close()

    def run(
        self,
        crm_file_path: str | Path,
        report_file_paths: Sequence[str | Path]
    ) -> ReconciliationResult:
        """
        Orchestrates and executes the reconciliation run process.

        Args:
            crm_file_path: Path to the CRM Master dataset file (Excel/CSV).
            report_file_paths: List of paths to report files (CAMS, KFintech, BSE, NSE, CAS PDF).

        Returns:
            ReconciliationResult: Result mapping containing run details and discrepancies.

        Raises:
            FileAccessError: If the CRM Master file or any report file is missing or unreadable.
        """
        crm_path = Path(crm_file_path)
        report_paths = [Path(p) for p in report_file_paths]

        logger.info(f"Starting reconciliation execution. CRM file: {crm_path.name}")

        # Verify inputs and calculate checksums
        if not crm_path.exists():
            logger.error(f"CRM master file not found: {crm_path}")
            raise FileAccessError(f"CRM master file does not exist: {crm_path}")

        crm_hash = calculate_sha256(crm_path)
        logger.debug(f"CRM file SHA-256 calculated: {crm_hash}")

        # Setup standard output report file names
        excel_out = self.config.output_directory / f"discrepancies_{self.run_id}.xlsx"
        csv_out = self.config.output_directory / f"discrepancies_{self.run_id}.csv"
        json_out = self.config.output_directory / f"discrepancies_{self.run_id}.json"

        # Initialize core components
        crm_parser = CRMParser()
        norm_pipeline = NormalizationPipeline()
        validation_engine = ValidationEngine()
        core_reconciler = CoreReconciler()

        # 1. Parse, normalize, and validate CRM
        try:
            crm_parse_result = crm_parser.parse_crm(crm_path)
        except (FileAccessError, ParserError):
            raise
        except Exception as e:
            logger.error(f"Unexpected CRM Ingestion failure: {e}")
            raise ParserError(f"Failed to parse CRM file: {e}") from e

        # Normalize CRM records capturing any formatting failures
        normalized_crm_records = []
        crm_norm_failures = []
        for rec in crm_parse_result.records:
            try:
                norm_rec = norm_pipeline.normalize_crm_record(rec)
                normalized_crm_records.append(norm_rec)
            except ValueError as e:
                logger.warning(f"Normalization failed for CRM record: {e}")
                crm_norm_failures.append({
                    "row_number": 0,
                    "source": "CRM",
                    "failure_type": "NORMALIZATION_ERROR",
                    "field_name": "pan",
                    "message": f"Normalization failed: {e}",
                    "raw_data": rec.model_dump(),
                })

        crm_profile = self.config.sources.get("CRM") or SourceProfileConfig(
            available_fields=[
                "pan",
                "investor_name",
                "mobile",
                "email",
                "kyc_status",
                "fatca_status",
                "investor_status",
                "total_amount",
            ],
            required_fields=["pan", "investor_name"],
            compare=["pan", "investor_name"],
            validations=["pan_format", "mobile_format", "email_format"],
        )
        crm_validation_result = validation_engine.validate_records(normalized_crm_records, crm_profile)

        all_validation_failures = []
        all_validation_failures.extend(crm_validation_result.validation_failures)

        # Setup report variables
        report_records = []
        report_hashes = {}
        failed_files = []
        total_report_records = 0
        validation_failures_count = (
            len(crm_parse_result.validation_failures)
            + len(crm_norm_failures)
            + len(crm_validation_result.validation_failures)
        )

        # 2. Parse, normalize, and validate Report files
        for path in report_paths:
            if not path.exists():
                logger.error(f"Report file not found: {path}")
                raise FileAccessError(f"Report file does not exist: {path}")

            checksum = calculate_sha256(path)
            report_hashes[path.name] = checksum
            logger.debug(f"Report file {path.name} SHA-256: {checksum}")

            try:
                parser: Any = default_registry.detect_parser(path)
            except ParserError as e:
                logger.error(f"Parser detection failed for {path.name}: {e}")
                failed_files.append(
                    FileFailure(
                        file_name=path.name,
                        source="UNKNOWN",
                        failure_type="PARSER_DETECTION_ERROR",
                        message=str(e),
                    )
                )
                continue

            source_name = parser.source.value

            try:
                # Parse report file
                parse_result = parser.parse_report(path)
            except PDFDecryptionError as e:
                logger.error(f"PDF decryption failed for {path.name}: {e}")
                failed_files.append(
                    FileFailure(
                        file_name=path.name,
                        source=source_name,
                        failure_type="PDF_DECRYPTION_ERROR",
                        message=str(e),
                    )
                )
                continue
            except ParserError as e:
                logger.error(f"Report parsing failed for {path.name}: {e}")
                failed_files.append(
                    FileFailure(
                        file_name=path.name,
                        source=source_name,
                        failure_type="PARSER_ERROR",
                        message=str(e),
                    )
                )
                continue

            # Normalize report records capturing formatting failures
            normalized_report_recs = []
            report_norm_failures = []
            for rep_rec in parse_result.records:
                try:
                    norm_rep_rec = norm_pipeline.normalize_report_record(rep_rec)
                    object.__setattr__(norm_rep_rec, "file_name", path.name)
                    object.__setattr__(norm_rep_rec, "file_id", path.parent.name)
                    normalized_report_recs.append(norm_rep_rec)
                except ValueError as e:
                    logger.warning(f"Normalization failed for report record in {path.name}: {e}")
                    report_norm_failures.append({
                        "row_number": getattr(rep_rec, "raw_row_index", 0),
                        "source": source_name,
                        "failure_type": "NORMALIZATION_ERROR",
                        "field_name": "pan",
                        "message": f"Normalization failed: {e}",
                        "raw_data": rep_rec.model_dump(),
                    })

            # Validate report records
            profile = self.config.sources.get(source_name) or SourceProfileConfig(
                available_fields=["pan", "investor_name", "mobile", "email", "total_amount"],
                required_fields=["pan", "investor_name"],
                compare=["pan", "investor_name", "mobile", "total_amount"],
                validations=["pan_format", "mobile_format"],
            )
            report_validation_result = validation_engine.validate_records(normalized_report_recs, profile)

            # Accumulate report statistics
            report_records.extend(report_validation_result.valid_records)
            all_validation_failures.extend(report_validation_result.validation_failures)
            total_report_records += parse_result.metadata.total_rows
            validation_failures_count += (
                len(parse_result.validation_failures)
                + len(report_norm_failures)
                + len(report_validation_result.validation_failures)
            )

        # 3. Execute reconciliation engine
        recon_result = core_reconciler.reconcile(
            crm_records=crm_validation_result.valid_records,
            report_records=report_records,
            config=self.config,
        )

        timestamp_iso = datetime.now(UTC).isoformat().replace("+00:00", "Z")

        # Metadata metrics
        metadata = ReconciliationRunMetadata(
            run_id=self.run_id,
            timestamp=timestamp_iso,
            crm_file_hash=crm_hash,
            report_file_hashes=report_hashes,
            total_crm_records=crm_parse_result.metadata.total_rows,
            total_report_records=total_report_records,
            validation_failures_count=validation_failures_count,
            discrepancies_count=len(recon_result.discrepancies),
            failed_files=failed_files,
        )

        final_result = ReconciliationResult(
            metadata=metadata,
            discrepancies=recon_result.discrepancies,
            excel_report_path=None,
            csv_report_path=None,
            json_report_path=None,
            matched_audits=recon_result.matched_audits,
        )

        # Invoke configured report writers
        formats = self.config.reporting.formats
        if formats is None:
            formats = self.config.reporting.default_output_formats
        if not formats:
            formats = ["excel", "csv", "json"]

        formats_lower = [fmt.lower() for fmt in formats]

        if "excel" in formats_lower or "xlsx" in formats_lower:
            excel_reporter = ExcelReporter(output_dir=self.config.output_directory, run_id=self.run_id)
            excel_reporter.report(
                result=final_result,
                core_result=recon_result,
                all_validation_failures=all_validation_failures,
                file_path=excel_out,
                crm_path=crm_path
            )
            final_result.excel_report_path = str(excel_out)

        if "csv" in formats_lower:
            csv_reporter = CSVReporter(output_dir=self.config.output_directory, run_id=self.run_id)
            csv_reporter.report(
                result=final_result,
                core_result=recon_result
            )
            final_result.csv_report_path = str(csv_out)

        if "json" in formats_lower:
            json_reporter = JSONReporter(output_dir=self.config.output_directory, run_id=self.run_id)
            json_reporter.report(
                result=final_result,
                file_path=json_out
            )
            final_result.json_report_path = str(json_out)

        self.last_recon_result = recon_result
        self.last_validation_failures = all_validation_failures

        logger.info(f"Reconciliation session complete. Run ID: {self.run_id}")

        return final_result
