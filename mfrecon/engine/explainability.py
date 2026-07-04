"""Explainability utilities for generating plain-English discrepancy explanations."""

from typing import Any


def format_explanation(
    discrepancy_type: str,
    field_name: str | None,
    crm_val: Any,
    report_val: Any,
    extra_info: dict[str, Any] | None = None
) -> str:
    """
    Generates a natural-language description detailing why a discrepancy occurred.

    Args:
        discrepancy_type: Code classification of discrepancy (e.g. AMOUNT_MISMATCH).
        field_name: Specific field under comparison.
        crm_val: Mismatch value recorded in CRM.
        report_val: Mismatch value recorded in Report.
        extra_info: Dict carrying execution context parameters (e.g. tolerances, keys).

    Returns:
        str: Human-readable explanation text.
    """
    if extra_info is None:
        extra_info = {}

    if discrepancy_type == "MISSING_IN_CRM":
        pan = extra_info.get("pan", "N/A")
        folio = extra_info.get("folio_number", "N/A")
        return f"Record with PAN '{pan}' and Folio '{folio}' is missing in CRM database."

    if discrepancy_type == "MISSING_IN_REPORT":
        client_id = extra_info.get("crm_client_id", "N/A")
        pan = extra_info.get("pan", "N/A")
        return f"CRM Client ID '{client_id}' with PAN '{pan}' is missing in the processed report files."

    if discrepancy_type == "FUZZY_MATCH_WARNING":
        confidence = float(extra_info.get("confidence", 0.0))
        route = extra_info.get("matching_route", "N/A")
        return (
            f"Fuzzy match warning: Record aligned via name similarity of {confidence * 100:.1f}% "
            f"using route '{route}'."
        )

    field_labels = {
        "investor_status": "Status",
        "kyc_status": "KYC Status",
        "fatca_status": "FATCA Status",
        "total_amount": "Total Amount",
        "investor_name": "Investor Name",
        "last_transaction_date": "Last Transaction Date",
        "mobile": "Mobile",
        "email": "Email",
        "pan": "PAN",
        "date_of_birth": "Date of Birth",
        "bank_name": "Bank Name",
        "bank_account": "Bank Account",
        "ifsc": "IFSC",
        "registered_address": "Registered Address",
        "mode_of_holding": "Mode of Holding",
        "nominee_1": "Nominee 1",
        "nominee_relation": "Nominee Relation",
        "distributor_arn": "Distributor (ARN)"
    }

    if discrepancy_type == "FIELD_MISSING":
        field_desc = str(field_name).replace("_", " ").title() if field_name else "Field"
        label = field_labels.get(field_name, field_desc)
        source = extra_info.get("source", "N/A")
        return f"{label} column missing from {source} source file. CRM value '{crm_val}' could not be compared."

    if discrepancy_type == "FIELD_EMPTY":
        field_desc = str(field_name).replace("_", " ").title() if field_name else "Field"
        label = field_labels.get(field_name, field_desc)
        source = extra_info.get("source", "N/A")
        return f"{label} column exists in {source} but value is blank/empty. CRM value '{crm_val}' could not be compared."

    if discrepancy_type == "INCOMPLETE_CRM_RECORD":
        client_id = extra_info.get("crm_client_id", "N/A")
        pan = extra_info.get("pan", "N/A")
        return f"CRM Record Client ID '{client_id}' with PAN '{pan}' is incomplete (missing contact info: mobile/email, and compliance status: KYC/FATCA) and is not present in processed reports."


    # Mismatch descriptions
    field_desc = str(field_name).replace("_", " ").title() if field_name else "Field"

    if discrepancy_type == "AMOUNT_MISMATCH":
        try:
            c_val = float(str(crm_val))
            r_val = float(str(report_val))
            return f"Amount mismatch detected. CRM value {c_val:.2f} differs from Report value {r_val:.2f}."
        except (ValueError, TypeError):
            pass

    if discrepancy_type == "DATE_MISMATCH":
        tolerance = extra_info.get("date_days_tolerance", 3)
        return (
            f"Transaction date mismatch detected: CRM value '{crm_val}' differs from "
            f"Report value '{report_val}' beyond configured tolerance of {tolerance} days."
        )

    return f"{field_desc} mismatch detected. CRM value '{crm_val}' differs from Report value '{report_val}'."
