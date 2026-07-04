"""Reconciliation result schemas and statistics models."""

from typing import Any

from pydantic import BaseModel, Field

from mfrecon.core.domain import Discrepancy, MatchedAudit


class ReconciliationStatistics(BaseModel):
    """Execution statistics capturing matches and mismatches counts."""
    total_records: int = Field(..., description="Total count of input records evaluated")
    matched_count: int = Field(..., description="Count of successfully matched records")
    unmatched_count: int = Field(..., description="Count of unmatched records")
    discrepancy_count: int = Field(..., description="Total count of discrepancies generated")

class ReconciliationMetadata(BaseModel):
    """Metadata detailing the reconciliation run parameters."""
    run_id: str = Field(..., description="Unique UUID representing this execution run")
    execution_time: float = Field(..., description="Reconciliation execution duration in seconds")
    source_files: list[str] = Field(default_factory=list, description="Names of source files evaluated")

class ReconciliationResult(BaseModel):
    """Container payload returning matched records, unmatched records, and discrepancies."""
    matched_records: list[tuple[Any, Any]] = Field(
        default_factory=list,
        description="List of matched (CRMRecord, ReportRecord) tuples"
    )
    unmatched_records: list[Any] = Field(
        default_factory=list,
        description="Records (CRMRecord or ReportRecord) that could not be matched"
    )
    discrepancies: list[Discrepancy] = Field(
        default_factory=list,
        description="Aggregated field-level discrepancies"
    )
    statistics: ReconciliationStatistics = Field(..., description="Run statistics")
    metadata: ReconciliationMetadata = Field(..., description="Run metadata settings")
    matched_audits: list[MatchedAudit] = Field(
        default_factory=list,
        description="List of audit traces for successfully matched records"
    )

