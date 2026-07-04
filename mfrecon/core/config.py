"""Configuration models and loaders for parsing and validating engine settings from YAML."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError

from mfrecon.core.exceptions import ConfigurationError, FileAccessError


class SourceProfileConfig(BaseModel):
    """Configuration profile defining parsing, validation, and comparison settings for a source."""
    available_fields: list[str] = Field(
        default_factory=list,
        description="List of fields extracted from this source file"
    )
    required_fields: list[str] = Field(
        default_factory=list,
        description="Mandatory fields which cannot be empty during validation"
    )
    compare: list[str] = Field(
        default_factory=list,
        description="Fields compared against CRM records during reconciliation"
    )
    validations: list[str] = Field(
        default_factory=list,
        description="Validation rules executed on data rows from this source"
    )


class EngineSettingsConfig(BaseModel):
    """Execution options for engine behavior (run mode, tolerances)."""
    run_mode: str = Field(default="STRICT", description="Execution mode: STRICT or TOLERANT")
    amount_epsilon: float = Field(default=0.01, description="Tolerance for holding balance checks in INR")
    date_days_tolerance: int = Field(default=3, description="Allowed transaction date offset in days")


class MatchingConfig(BaseModel):
    """Rules and thresholds controlling record alignment."""
    primary_key: str = Field(default="pan", description="Primary unique key for records alignment")
    enable_fuzzy_matching: bool = Field(default=False, description="Enable fuzzy name checking fallback")
    fuzzy_threshold: float = Field(default=0.90, description="Minimum Levenshtein similarity distance threshold")
    fuzzy_secondary_keys: list[str] = Field(
        default_factory=list,
        description="Fields checked to verify a secondary fuzzy match"
    )
    source_overrides: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional source overrides for fuzzy matching settings"
    )


class ValidationConfig(BaseModel):
    """Validation bounds and mandated value sets."""
    require_pan: bool = Field(default=True, description="Strict checking of PAN requirements")
    validate_kyc_status: bool = Field(default=True, description="Validate KYC compliance status")
    validate_fatca_status: bool = Field(default=True, description="Validate FATCA compliance status")
    allowed_kyc_statuses: list[str] = Field(
        default_factory=list,
        description="List of acceptable verification KYC states"
    )
    allowed_fatca_statuses: list[str] = Field(
        default_factory=list,
        description="List of acceptable FATCA verification states"
    )
    suppress_missing_in_report_for_incomplete_crm: bool = Field(
        default=False,
        description="Generate INCOMPLETE_CRM_RECORD instead of MISSING_IN_REPORT"
    )


class ReportingConfig(BaseModel):
    """File format layouts and severity configuration mapping."""
    default_output_formats: list[str] = Field(
        default_factory=list,
        description="Standard formats exported (excel, csv, json)"
    )
    formats: list[str] | None = Field(
        default=None,
        description="Standard formats exported override (excel, csv, json)"
    )
    redact_sensitive_fields: bool = Field(default=True, description="Mask sensitive details in output reports")
    severity_mappings: dict[str, str] = Field(
        default_factory=dict,
        description="Discrepancy type string mapped to severity outputs"
    )


class EngineConfig(BaseModel):
    """Parent configuration object wrapping all sub-module option trees."""
    output_directory: Path = Field(
        default=Path("outputs"),
        description="Directory where discrepancy outputs should be saved"
    )
    configure_logging: bool = Field(
        default=False,
        description="Opt-in flag for library logging configuration"
    )
    engine: EngineSettingsConfig = Field(default_factory=EngineSettingsConfig)
    matching: MatchingConfig = Field(default_factory=MatchingConfig)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    reporting: ReportingConfig = Field(default_factory=ReportingConfig)
    sources: dict[str, SourceProfileConfig] = Field(default_factory=dict)


def load_config(yaml_path: Path) -> EngineConfig:
    """
    Loads, parses, and validates the configuration from a YAML file.

    Args:
        yaml_path: The filesystem path to the recon_config.yaml file.

    Returns:
        EngineConfig: A validated, strongly-typed engine configuration object.

    Raises:
        FileAccessError: If the target file does not exist or cannot be read.
        ConfigurationError: If the YAML is invalid or fails Pydantic schema checks.
    """
    if not yaml_path.exists():
        raise FileAccessError(f"Configuration file not found at: {yaml_path}")

    try:
        with yaml_path.open(encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)
    except (yaml.YAMLError, OSError) as e:
        raise ConfigurationError(f"Failed to read or parse YAML syntax: {e}") from e

    if raw_data is None:
        raw_data = {}

    try:
        return EngineConfig.model_validate(raw_data)
    except ValidationError as e:
        raise ConfigurationError(f"Configuration validation failed: {e}") from e


def load_config_from_dict(data: dict[str, Any]) -> EngineConfig:
    """
    Loads, parses, and validates the configuration from a dictionary.

    Args:
        data: The configuration dictionary.

    Returns:
        EngineConfig: A validated, strongly-typed engine configuration object.

    Raises:
        ConfigurationError: If validation fails.
    """
    try:
        return EngineConfig.model_validate(data)
    except ValidationError as e:
        raise ConfigurationError(f"Configuration validation failed: {e}") from e

