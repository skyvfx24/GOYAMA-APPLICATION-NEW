"""Report parsing result schemas defining structural extraction outputs."""

from typing import Any

from pydantic import BaseModel, Field

from mfrecon.core.domain import RecordSource, ReportRecord


class ReportParseMetadata(BaseModel):
    """Extraction stats and identifier logs for an AMC report run."""
    source: RecordSource = Field(..., description="Report origin source AMC enum")
    file_name: str = Field(..., description="Original name of the ingested file")
    file_hash: str = Field(..., description="SHA-256 fingerprint checksum of the file")
    total_rows: int = Field(..., description="Total records loaded from report")
    parsed_rows: int = Field(..., description="Rows validated and converted to domain records")
    failed_rows: int = Field(..., description="Rows failed and captured to DLQ logs")


class ReportParseResult(BaseModel):
    """Payload representing parsing and validation statistics of an AMC report file."""
    records: list[ReportRecord] = Field(..., description="Successfully parsed and validated ReportRecord instances")
    validation_failures: list[dict[str, Any]] = Field(
        ...,
        description="Isolated rows failing validation checks with row indices and failure reasons"
    )
    metadata: ReportParseMetadata = Field(..., description="Metadata metrics for verification logs")
