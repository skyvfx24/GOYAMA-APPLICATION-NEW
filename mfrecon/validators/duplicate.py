"""Duplicate detection checking for exact and conflicting record duplicates."""

from typing import Any

from mfrecon.core.domain import CRMRecord


class DuplicateDetector:
    """Identifies exact and conflicting duplicate records by PAN (+ Folio/CRM ID where available)."""

    def process(self, records: list[Any]) -> tuple[list[Any], list[Any], list[dict[str, Any]]]:
        """
        Processes records to identify duplicates.

        Args:
            records: List of validated CRMRecord or ReportRecord.

        Returns:
            tuple: (valid_records, invalid_records, validation_failures)
                where duplicate records are separated into invalid_records and validation_failures.
        """
        # Group records by source-specific duplicate key
        grouped: dict[tuple[Any, ...], list[Any]] = {}
        for rec in records:
            key: tuple[Any, ...]
            if isinstance(rec, CRMRecord):
                key = (rec.pan, rec.crm_client_id)
            else:
                folio = getattr(rec, "folio_number", None)
                key = (
                    (rec.pan, str(folio).strip())
                    if folio is not None and str(folio).strip() != ""
                    else (rec.pan,)
                )
            grouped.setdefault(key, []).append(rec)


        valid_records: list[Any] = []
        invalid_records: list[Any] = []
        validation_failures: list[dict[str, Any]] = []

        # Comparable fields to identify conflicts
        comparable_fields = [
            "investor_name",
            "mobile",
            "email",
            "kyc_status",
            "fatca_status",
            "investor_status",
            "last_transaction_date",
            "total_amount",
        ]

        for _, group in grouped.items():
            # First occurrence in group is clean
            valid_records.append(group[0])

            # Subsequent occurrences are duplicates
            for duplicate_rec in group[1:]:
                invalid_records.append(duplicate_rec)
                row_num = getattr(duplicate_rec, "raw_row_index", 0)
                source = str(getattr(duplicate_rec, "source", "CRM"))

                # Check for conflicts
                conflicts = []
                for field in comparable_fields:
                    val1 = getattr(group[0], field, None)
                    val2 = getattr(duplicate_rec, field, None)
                    if val1 != val2:
                        conflicts.append(field)

                if conflicts:
                    failure_type = "CONFLICTING_DUPLICATE"
                    msg = (
                        f"Conflicting duplicate record found for PAN '{duplicate_rec.pan}'. "
                        f"Conflict in fields: {', '.join(conflicts)}."
                    )
                else:
                    failure_type = "EXACT_DUPLICATE"
                    msg = f"Exact duplicate record found for PAN '{duplicate_rec.pan}'."

                validation_failures.append({
                    "row_number": row_num,
                    "source": source,
                    "failure_type": failure_type,
                    "field_name": "pan",
                    "message": msg,
                    "raw_data": duplicate_rec.model_dump()
                })

        return valid_records, invalid_records, validation_failures
