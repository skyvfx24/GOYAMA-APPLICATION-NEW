"""Validation Engine implementation coordinating schema, rules, and duplicate checking."""

from typing import Any

from mfrecon.core.config import SourceProfileConfig
from mfrecon.validators.duplicate import DuplicateDetector
from mfrecon.validators.result import ValidationMetadata, ValidationResult
from mfrecon.validators.rules import (
    validate_email_format,
    validate_fatca_status,
    validate_investor_status,
    validate_kyc_status,
    validate_mobile_format,
    validate_pan_format,
)
from mfrecon.validators.schema import SchemaValidator


class ValidationEngine:
    """Executes validation checks on CRM and Report records using SourceProfile configurations."""

    def __init__(self) -> None:
        self.schema_validator = SchemaValidator()
        self.duplicate_detector = DuplicateDetector()

    def validate_records(self, records: list[Any], profile: SourceProfileConfig) -> ValidationResult:
        """
        Validates a list of records against a source configuration profile.

        Args:
            records: List of CRMRecord or ReportRecord.
            profile: SourceProfileConfig settings.

        Returns:
            ValidationResult: Cleaned valid records, invalid records, failures, and metadata stats.
        """
        total_records = len(records)
        passing_records: list[Any] = []
        invalid_records: list[Any] = []
        validation_failures: list[dict[str, Any]] = []

        required_fields = profile.required_fields
        available_fields = profile.available_fields
        rules_list = [rule.lower().strip() for rule in profile.validations]

        for record in records:
            record_failures: list[dict[str, Any]] = []
            row_num = getattr(record, "raw_row_index", 0)
            source = str(getattr(record, "source", "CRM"))

            # 1. Run Schema validation (required & available checks)
            schema_errs = self.schema_validator.validate(record, required_fields, available_fields)
            record_failures.extend(schema_errs)

            # 2. Run Configured field format validation rules
            # PAN validation
            if "pan_format" in rules_list and not validate_pan_format(record.pan):
                record_failures.append({
                    "row_number": row_num,
                    "source": source,
                    "failure_type": "INVALID_PAN_FORMAT",
                    "field_name": "pan",
                    "message": f"PAN '{record.pan}' failed regex formatting verification.",
                    "raw_data": record.model_dump()
                })

            # Mobile validation (if populated)
            if (
                "mobile_format" in rules_list
                and record.mobile is not None
                and not validate_mobile_format(record.mobile)
            ):
                record_failures.append({
                    "row_number": row_num,
                    "source": source,
                    "failure_type": "INVALID_MOBILE_FORMAT",
                    "field_name": "mobile",
                    "message": f"Mobile '{record.mobile}' is not a valid 10-digit number.",
                    "raw_data": record.model_dump()
                })

            # Email validation (if populated)
            if "email_format" in rules_list and record.email is not None and not validate_email_format(record.email):
                record_failures.append({
                    "row_number": row_num,
                    "source": source,
                    "failure_type": "INVALID_EMAIL_FORMAT",
                    "field_name": "email",
                    "message": f"Email '{record.email}' has invalid email syntax.",
                    "raw_data": record.model_dump()
                })

            # KYC status validation
            if (
                ("kyc_status" in rules_list or "kyc_status_format" in rules_list)
                and not validate_kyc_status(record.kyc_status)
            ):
                record_failures.append({
                    "row_number": row_num,
                    "source": source,
                    "failure_type": "INVALID_KYC_STATUS",
                    "field_name": "kyc_status",
                    "message": f"KYC status '{record.kyc_status}' is not in allowed KYC statuses.",
                    "raw_data": record.model_dump()
                })

            # FATCA status validation
            if (
                ("fatca_status" in rules_list or "fatca_status_format" in rules_list)
                and not validate_fatca_status(record.fatca_status)
            ):
                record_failures.append({
                    "row_number": row_num,
                    "source": source,
                    "failure_type": "INVALID_FATCA_STATUS",
                    "field_name": "fatca_status",
                    "message": f"FATCA status '{record.fatca_status}' is not in allowed FATCA statuses.",
                    "raw_data": record.model_dump()
                })

            # Investor status validation
            if (
                ("investor_status" in rules_list or "investor_status_format" in rules_list)
                and not validate_investor_status(record.investor_status)
            ):
                record_failures.append({
                    "row_number": row_num,
                    "source": source,
                    "failure_type": "INVALID_INVESTOR_STATUS",
                    "field_name": "investor_status",
                    "message": f"Investor status '{record.investor_status}' is invalid.",
                    "raw_data": record.model_dump()
                })

            if record_failures:
                invalid_records.append(record)
                validation_failures.extend(record_failures)
            else:
                passing_records.append(record)

        # 3. Process passing records to filter out duplicates
        valid_records, duplicate_invalid_records, duplicate_failures = self.duplicate_detector.process(passing_records)
        invalid_records.extend(duplicate_invalid_records)
        validation_failures.extend(duplicate_failures)
        duplicate_records_count = len(duplicate_invalid_records)

        metadata = ValidationMetadata(
            total_records=total_records,
            valid_records=len(valid_records),
            invalid_records=len(invalid_records),
            duplicate_records=duplicate_records_count
        )

        return ValidationResult(
            valid_records=valid_records,
            invalid_records=invalid_records,
            validation_failures=validation_failures,
            metadata=metadata
        )
