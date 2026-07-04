"""Validation result models and metadata definitions."""

from typing import Any

from pydantic import BaseModel, Field


class ValidationMetadata(BaseModel):
    """Metadata representing validation run statistics."""
    total_records: int = Field(..., description="Total count of records validated")
    valid_records: int = Field(..., description="Count of successfully validated records")
    invalid_records: int = Field(..., description="Count of records failing validation")
    duplicate_records: int = Field(..., description="Count of duplicate records identified and skipped")

class ValidationResult(BaseModel):
    """Container payload returning cleaned records and tracked failures."""
    valid_records: list[Any] = Field(default_factory=list, description="List of validated records")
    invalid_records: list[Any] = Field(default_factory=list, description="List of records failing validation")
    validation_failures: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Detailed row-by-row failure logging dicts (DLQ payload)"
    )
    metadata: ValidationMetadata = Field(..., description="Validation statistics summary")
