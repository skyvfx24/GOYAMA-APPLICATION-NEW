"""Schema validation checking for required and available fields."""

from decimal import Decimal
from typing import Any

from mfrecon.core.domain import FATCAStatus, InvestorStatus, KYCStatus


class SchemaValidator:
    """Validates records against SourceProfile available and required fields configuration."""

    def validate(self, record: Any, required_fields: list[str], available_fields: list[str]) -> list[dict[str, Any]]:
        """
        Validates record presence of required fields and unexpected populated fields.

        Args:
            record: CRMRecord or ReportRecord.
            required_fields: List of mandatory fields.
            available_fields: List of allowed fields.

        Returns:
            list[dict[str, Any]]: Aggregated validation failures.
        """
        failures: list[dict[str, Any]] = []
        row_num = getattr(record, "raw_row_index", 0)
        source = str(getattr(record, "source", "CRM"))

        # 1. Validate required fields are not missing/empty
        for field in required_fields:
            val = getattr(record, field, None)
            if val is None or (isinstance(val, str) and not val.strip()):
                failures.append({
                    "row_number": row_num,
                    "source": source,
                    "failure_type": "REQUIRED_FIELD_MISSING",
                    "field_name": field,
                    "message": f"Required field '{field}' is missing or empty.",
                    "raw_data": record.model_dump()
                })

        # 2. Validate all populated fields exist in available_fields
        # Standard record field keys to inspect
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
        ]

        for field in standard_fields:
            val = getattr(record, field, None)
            is_populated = False

            if val is not None:
                if isinstance(val, str) and not val.strip():
                    pass
                elif field == "total_amount" and val == Decimal("0.00"):
                    # Check if total_amount is explicitly in available_fields to determine if unexpected
                    pass
                elif val in (KYCStatus.UNKNOWN, FATCAStatus.UNKNOWN, InvestorStatus.UNKNOWN):
                    pass
                else:
                    is_populated = True

            if is_populated and field not in available_fields:
                failures.append({
                    "row_number": row_num,
                    "source": source,
                    "failure_type": "UNEXPECTED_FIELD",
                    "field_name": field,
                    "message": f"Field '{field}' is populated but not listed in available_fields for this source.",
                    "raw_data": record.model_dump()
                })

        return failures
