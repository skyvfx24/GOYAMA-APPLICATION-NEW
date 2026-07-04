"""Models and schemas representing the outputs of report generation."""

from typing import Any

from pydantic import BaseModel, Field


class ReportArtifact(BaseModel):
    """Represents a generated output report file."""

    report_type: str = Field(..., description="Format type: excel, csv, or json")
    file_path: str = Field(..., description="Absolute filesystem path to the report artifact")
    created_at: str = Field(..., description="ISO 8601 UTC timestamp of creation")


class ReportGenerationResult(BaseModel):
    """Execution summary output representing the results of a reporting layer run."""

    generated_files: list[ReportArtifact] = Field(
        default_factory=list, description="List of generated report files"
    )
    summary: str = Field(..., description="Plain English executive summary statement")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Metadata logs and processing statistics"
    )
