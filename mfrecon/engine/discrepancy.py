"""Discrepancy calculation and generation for aligned records."""

from datetime import UTC, datetime
from decimal import Decimal

from mfrecon.core.config import EngineConfig, SourceProfileConfig
from mfrecon.core.domain import AuditTrace, CRMRecord, Discrepancy, DiscrepancyType, ReportRecord
from mfrecon.engine.explainability import format_explanation


def get_skipped_audit_note(field_name: str) -> str:
    """Helper to convert standard field names to standard skipped audit notes."""
    mapping = {
        "pan": "PAN_COMPARISON_SKIPPED",
        "investor_name": "NAME_COMPARISON_SKIPPED",
        "mobile": "MOBILE_COMPARISON_SKIPPED",
        "email": "EMAIL_COMPARISON_SKIPPED",
        "kyc_status": "KYC_COMPARISON_SKIPPED",
        "fatca_status": "FATCA_COMPARISON_SKIPPED",
        "investor_status": "STATUS_COMPARISON_SKIPPED",
        "last_transaction_date": "DATE_COMPARISON_SKIPPED",
        "total_amount": "AMOUNT_COMPARISON_SKIPPED",
        "date_of_birth": "DOB_COMPARISON_SKIPPED",
        "bank_name": "BANK_COMPARISON_SKIPPED",
        "bank_account": "BANK_ACCOUNT_COMPARISON_SKIPPED",
        "ifsc": "IFSC_COMPARISON_SKIPPED",
        "registered_address": "ADDRESS_COMPARISON_SKIPPED",
        "mode_of_holding": "MODE_OF_HOLDING_COMPARISON_SKIPPED",
        "nominee_1": "NOMINEE_COMPARISON_SKIPPED",
        "nominee_relation": "NOMINEE_RELATION_COMPARISON_SKIPPED",
        "distributor_arn": "DISTRIBUTOR_ARN_COMPARISON_SKIPPED",
    }
    return mapping.get(field_name.lower().strip(), f"{field_name.upper()}_COMPARISON_SKIPPED")


def compare_records(
    crm: CRMRecord,
    report: ReportRecord,
    profile: SourceProfileConfig,
    config: EngineConfig,
    match_route: str,
    confidence: float
) -> list[Discrepancy]:
    """
    Evaluates field-level differences between a CRM Record and a Report Record
    based on the source profile's comparable list.
    """
    discrepancies: list[Discrepancy] = []
    skipped_comparisons: list[str] = []

    # Mappable standard comparable keys
    standard_fields = [
        "pan",
        "investor_name",
        "mobile",
        "email",
        "kyc_status",
        "fatca_status",
        "investor_status",
        "last_transaction_date",
        "total_amount",
        "date_of_birth",
        "bank_name",
        "bank_account",
        "ifsc",
        "registered_address",
        "mode_of_holding",
        "nominee_1",
        "nominee_relation",
        "distributor_arn"
    ]

    compare_fields = [f.strip().lower() for f in profile.compare]

    # Trace skipped fields based on source profile omissions
    for field in standard_fields:
        if field not in compare_fields:
            skipped_comparisons.append(get_skipped_audit_note(field))

    # Construct the AuditTrace shared by all discrepancies generated in this check
    timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    audit_trace = AuditTrace(
        matching_route=match_route,
        match_confidence=confidence,
        evaluation_timestamp=timestamp,
        reconciler_version="1.0.0",
        rule_evaluated=f"SourceProfile: {report.source}",
        skipped_comparisons=skipped_comparisons
    )

    source_info = {
        "file_name": getattr(report, "file_name", "N/A"),
        "file_id": getattr(report, "file_id", "N/A"),
        "raw_row_index": str(report.raw_row_index),
        "folio_number": report.folio_number if report.folio_number else "N/A"
    }

    # Execute checks
    for field in compare_fields:
        crm_val = getattr(crm, field, None)
        report_val = getattr(report, field, None)

        has_mismatch = False
        disc_type: DiscrepancyType | None = None

        # Check missing or empty first
        if hasattr(report, "missing_fields") and field in report.missing_fields:
            has_mismatch = True
            disc_type = DiscrepancyType.FIELD_MISSING
        elif hasattr(report, "empty_fields") and field in report.empty_fields:
            has_mismatch = True
            disc_type = DiscrepancyType.FIELD_EMPTY
        else:
            if field == "pan":
                if crm_val != report_val:
                    has_mismatch = True
                    disc_type = DiscrepancyType.PAN_MISMATCH
            elif field == "investor_name":
                if crm_val != report_val:
                    has_mismatch = True
                    disc_type = DiscrepancyType.NAME_MISMATCH
            elif field == "mobile":
                if crm_val != report_val:
                    has_mismatch = True
                    disc_type = DiscrepancyType.MOBILE_MISMATCH
            elif field == "email":
                if crm_val != report_val:
                    has_mismatch = True
                    disc_type = DiscrepancyType.EMAIL_MISMATCH
            elif field == "kyc_status":
                if crm_val != report_val:
                    has_mismatch = True
                    disc_type = DiscrepancyType.KYC_MISMATCH
            elif field == "fatca_status":
                if crm_val != report_val:
                    has_mismatch = True
                    disc_type = DiscrepancyType.FATCA_MISMATCH
            elif field == "investor_status":
                if crm_val != report_val:
                    has_mismatch = True
                    disc_type = DiscrepancyType.STATUS_MISMATCH
            elif field == "last_transaction_date":
                # Compare dates checking day offset tolerance
                if crm_val is not None and report_val is not None:
                    days_diff = abs((crm_val - report_val).days)
                    if days_diff > config.engine.date_days_tolerance:
                        has_mismatch = True
                        disc_type = DiscrepancyType.DATE_MISMATCH
                elif crm_val != report_val:
                    has_mismatch = True
                    disc_type = DiscrepancyType.DATE_MISMATCH
            elif field == "total_amount":
                # Compare Decimals checking amount epsilon limit
                c_amt = crm_val if isinstance(crm_val, Decimal) else Decimal("0.00")
                r_amt = report_val if isinstance(report_val, Decimal) else Decimal("0.00")
                if abs(c_amt - r_amt) > Decimal(str(config.engine.amount_epsilon)):
                    has_mismatch = True
                    disc_type = DiscrepancyType.AMOUNT_MISMATCH
            elif field == "date_of_birth":
                if crm_val != report_val:
                    has_mismatch = True
                    disc_type = DiscrepancyType.DOB_MISMATCH
            elif field == "bank_name":
                if crm_val != report_val:
                    has_mismatch = True
                    disc_type = DiscrepancyType.BANK_MISMATCH
            elif field == "bank_account":
                if crm_val != report_val:
                    has_mismatch = True
                    disc_type = DiscrepancyType.BANK_ACCOUNT_MISMATCH
            elif field == "ifsc":
                if crm_val != report_val:
                    has_mismatch = True
                    disc_type = DiscrepancyType.IFSC_MISMATCH
            elif field == "registered_address":
                if crm_val != report_val:
                    has_mismatch = True
                    disc_type = DiscrepancyType.ADDRESS_MISMATCH
            elif field == "mode_of_holding":
                if crm_val != report_val:
                    has_mismatch = True
                    disc_type = DiscrepancyType.MODE_OF_HOLDING_MISMATCH
            elif field == "nominee_1":
                if crm_val != report_val:
                    has_mismatch = True
                    disc_type = DiscrepancyType.NOMINEE_MISMATCH
            elif field == "nominee_relation":
                if crm_val != report_val:
                    has_mismatch = True
                    disc_type = DiscrepancyType.NOMINEE_RELATION_MISMATCH
            elif field == "distributor_arn":
                if crm_val != report_val:
                    has_mismatch = True
                    disc_type = DiscrepancyType.DISTRIBUTOR_ARN_MISMATCH

        if has_mismatch and disc_type:
            severity = config.reporting.severity_mappings.get(disc_type.value, "HIGH")
            # For INCOMPLETE_CRM_RECORD or FIELD_MISSING, set default severity if not defined
            if disc_type == DiscrepancyType.FIELD_MISSING:
                severity = config.reporting.severity_mappings.get(disc_type.value, "MEDIUM")
            elif disc_type == DiscrepancyType.FIELD_EMPTY:
                severity = config.reporting.severity_mappings.get(disc_type.value, "MEDIUM")

            explanation = format_explanation(
                discrepancy_type=disc_type.value,
                field_name=field,
                crm_val=crm_val,
                report_val=report_val,
                extra_info={
                    "date_days_tolerance": config.engine.date_days_tolerance,
                    "source": report.source.value
                }
            )

            discrepancies.append(Discrepancy(
                discrepancy_type=disc_type,
                pan=report.pan,
                field_name=field,
                crm_value=str(crm_val) if crm_val is not None else None,
                report_value=str(report_val) if report_val is not None else None,
                severity=severity,
                explanation=explanation,
                source_info=source_info,
                audit_trace=audit_trace
            ))

    return discrepancies

