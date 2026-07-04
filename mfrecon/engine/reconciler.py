"""Core execution reconciler aligning records and generating comparison discrepancy matrices."""

import time
import uuid
from datetime import UTC, datetime
from typing import Any

from mfrecon.core.config import EngineConfig, SourceProfileConfig
from mfrecon.core.domain import AuditTrace, CRMRecord, Discrepancy, DiscrepancyType, MatchedAudit, ReportRecord, KYCStatus, FATCAStatus
from mfrecon.engine.discrepancy import compare_records, get_skipped_audit_note
from mfrecon.engine.explainability import format_explanation
from mfrecon.engine.matcher import RecordMatcher
from mfrecon.engine.result import ReconciliationMetadata, ReconciliationResult, ReconciliationStatistics


class ReconciliationEngine:
    """Orchestrates matching alignments and field comparison matrices on record sets."""

    def reconcile(
        self,
        crm_records: list[CRMRecord],
        report_records: list[ReportRecord],
        config: EngineConfig
    ) -> ReconciliationResult:
        """
        Executes end-to-end reconciliation between CRM master records and parsed report records.

        Args:
            crm_records: List of validated CRMRecord instances.
            report_records: List of validated ReportRecord instances.
            config: Engine configuration parameters.

        Returns:
            ReconciliationResult: Aligned record pairs, unmatched records, and discrepancies.
        """
        start_time = time.perf_counter()
        run_id = str(uuid.uuid4())

        discrepancies: list[Discrepancy] = []
        matched_records: list[tuple[CRMRecord, ReportRecord]] = []
        matched_audits: list[MatchedAudit] = []
        unmatched_reports: list[ReportRecord] = []
        unmatched_crms: list[CRMRecord] = []

        matched_crm_ids: set[str] = set()

        # Build indexed RecordMatcher for O(1) alignment checks
        matcher = RecordMatcher(crm_records)

        timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")

        # 1. Match Report records against CRM records
        for report in report_records:
            source_name = report.source.value
            # Resolve SourceProfileConfig
            profile = config.sources.get(source_name)
            if not profile:
                # Fallback profile if none configured
                profile = SourceProfileConfig(
                    available_fields=[
                        "pan", "investor_name", "mobile", "email",
                        "kyc_status", "fatca_status", "investor_status", "total_amount"
                    ],
                    required_fields=["pan", "investor_name"],
                    compare=[
                        "pan", "investor_name", "mobile", "email",
                        "kyc_status", "fatca_status", "investor_status", "total_amount"
                    ],
                    validations=["pan_format", "mobile_format", "email_format"]
                )

            # Resolve fuzzy matching configs
            enable_fuzzy, threshold, secondary_keys = self._resolve_matching_config(config, source_name)

            # Try to match record
            match_res = matcher.find_match(
                report_record=report,
                enable_fuzzy=enable_fuzzy,
                threshold=threshold,
                secondary_keys=secondary_keys
            )

            source_info = {
                "file_name": getattr(report, "file_name", "N/A"),
                "file_id": getattr(report, "file_id", "N/A"),
                "raw_row_index": str(report.raw_row_index),
                "folio_number": report.folio_number if report.folio_number else "N/A"
            }

            if match_res.match_type == "UNMATCHED":
                unmatched_reports.append(report)

                # Generate MISSING_IN_CRM discrepancy
                severity = config.reporting.severity_mappings.get(DiscrepancyType.MISSING_IN_CRM.value, "CRITICAL")
                explanation = format_explanation(
                    discrepancy_type=DiscrepancyType.MISSING_IN_CRM.value,
                    field_name=None,
                    crm_val=None,
                    report_val=None,
                    extra_info={"pan": report.pan, "folio_number": report.folio_number}
                )

                audit_trace = AuditTrace(
                    matching_route="UNMATCHED",
                    match_confidence=0.0,
                    evaluation_timestamp=timestamp,
                    reconciler_version="1.0.0",
                    rule_evaluated=f"SourceProfile: {source_name}",
                    skipped_comparisons=[]
                )

                discrepancies.append(Discrepancy(
                    discrepancy_type=DiscrepancyType.MISSING_IN_CRM,
                    pan=report.pan,
                    field_name=None,
                    crm_value=None,
                    report_value=None,
                    severity=severity,
                    explanation=explanation,
                    source_info=source_info,
                    audit_trace=audit_trace
                ))
            else:
                crm_rec = match_res.crm_record
                assert crm_rec is not None
                matched_records.append((crm_rec, report))
                matched_crm_ids.add(crm_rec.crm_client_id)

                # Collect successful match audit trace details
                standard_fields = [
                    "pan",
                    "investor_name",
                    "mobile",
                    "email",
                    "kyc_status",
                    "fatca_status",
                    "investor_status",
                    "last_transaction_date",
                    "total_amount"
                ]
                compare_fields = [f.strip().lower() for f in profile.compare]
                skipped_comparisons = [get_skipped_audit_note(f) for f in standard_fields if f not in compare_fields]

                matched_audits.append(MatchedAudit(
                    pan=report.pan,
                    route=match_res.matching_route,
                    confidence=match_res.confidence,
                    source=report.source.value,
                    timestamp=timestamp,
                    skipped_comparisons=skipped_comparisons
                ))

                # Run field comparisons
                field_discrepancies = compare_records(
                    crm=crm_rec,
                    report=report,
                    profile=profile,
                    config=config,
                    match_route=match_res.matching_route,
                    confidence=match_res.confidence
                )
                discrepancies.extend(field_discrepancies)

                # Flag fuzzy match warning discrepancy if aligned via fuzzy
                if match_res.match_type == "FUZZY_MATCH_WARNING":
                    severity = config.reporting.severity_mappings.get(
                        DiscrepancyType.FUZZY_MATCH_WARNING.value, "MEDIUM"
                    )
                    explanation = format_explanation(
                        discrepancy_type=DiscrepancyType.FUZZY_MATCH_WARNING.value,
                        field_name=None,
                        crm_val=None,
                        report_val=None,
                        extra_info={"confidence": match_res.confidence, "matching_route": match_res.matching_route}
                    )

                    audit_trace = AuditTrace(
                        matching_route=match_res.matching_route,
                        match_confidence=match_res.confidence,
                        evaluation_timestamp=timestamp,
                        reconciler_version="1.0.0",
                        rule_evaluated=f"SourceProfile: {source_name}",
                        skipped_comparisons=[]
                    )

                    discrepancies.append(Discrepancy(
                        discrepancy_type=DiscrepancyType.FUZZY_MATCH_WARNING,
                        pan=report.pan,
                        field_name=None,
                        crm_value=None,
                        report_value=None,
                        severity=severity,
                        explanation=explanation,
                        source_info=source_info,
                        audit_trace=audit_trace
                    ))

        # 2. Identify unmatched CRM records (missing in report)
        for crm in crm_records:
            if crm.crm_client_id not in matched_crm_ids:
                unmatched_crms.append(crm)

                # Check if incomplete CRM record
                is_incomplete = (
                    crm.pan is not None and crm.pan != "" and
                    (crm.mobile is None or crm.mobile == "") and
                    (crm.email is None or crm.email == "") and
                    (crm.kyc_status == KYCStatus.UNKNOWN or crm.kyc_status is None) and
                    (crm.fatca_status == FATCAStatus.UNKNOWN or crm.fatca_status is None)
                )

                if is_incomplete and getattr(config.validation, "suppress_missing_in_report_for_incomplete_crm", False):
                    disc_type = DiscrepancyType.INCOMPLETE_CRM_RECORD
                    default_sev = "MEDIUM"
                else:
                    disc_type = DiscrepancyType.MISSING_IN_REPORT
                    default_sev = "HIGH"

                severity = config.reporting.severity_mappings.get(disc_type.value, default_sev)
                explanation = format_explanation(
                    discrepancy_type=disc_type.value,
                    field_name=None,
                    crm_val=None,
                    report_val=None,
                    extra_info={"crm_client_id": crm.crm_client_id, "pan": crm.pan}
                )

                audit_trace = AuditTrace(
                    matching_route="UNMATCHED",
                    match_confidence=0.0,
                    evaluation_timestamp=timestamp,
                    reconciler_version="1.0.0",
                    rule_evaluated="CRM Master List",
                    skipped_comparisons=[]
                )

                discrepancies.append(Discrepancy(
                    discrepancy_type=disc_type,
                    pan=crm.pan,
                    field_name=None,
                    crm_value=None,
                    report_value=None,
                    severity=severity,
                    explanation=explanation,
                    source_info={"crm_client_id": crm.crm_client_id},
                    audit_trace=audit_trace
                ))

        elapsed_time = time.perf_counter() - start_time

        # Gather file names
        source_files = list({getattr(r, "file_name", "N/A") for r in report_records if hasattr(r, "file_name")})
        if not source_files:
            source_files = ["N/A"]

        # Aggregate unmatched records
        unmatched_records: list[Any] = []
        unmatched_records.extend(unmatched_reports)
        unmatched_records.extend(unmatched_crms)

        statistics = ReconciliationStatistics(
            total_records=len(crm_records) + len(report_records),
            matched_count=len(matched_records),
            unmatched_count=len(unmatched_records),
            discrepancy_count=len(discrepancies)
        )

        metadata = ReconciliationMetadata(
            run_id=run_id,
            execution_time=elapsed_time,
            source_files=source_files
        )

        return ReconciliationResult(
            matched_records=matched_records,
            unmatched_records=unmatched_records,
            discrepancies=discrepancies,
            statistics=statistics,
            metadata=metadata,
            matched_audits=matched_audits
        )

    def _resolve_matching_config(self, config: EngineConfig, source_name: str) -> tuple[bool, float, list[str]]:
        """Resolves matching settings using SourceProfile overrides if configured."""
        enable_fuzzy = config.matching.enable_fuzzy_matching
        threshold = config.matching.fuzzy_threshold
        secondary_keys = config.matching.fuzzy_secondary_keys

        overrides = config.matching.source_overrides.get(source_name)
        if overrides:
            enable_fuzzy = overrides.get("enable_fuzzy_matching", enable_fuzzy)
            threshold = overrides.get("fuzzy_threshold", threshold)
            secondary_keys = overrides.get("fuzzy_secondary_keys", secondary_keys)

        return enable_fuzzy, threshold, secondary_keys
