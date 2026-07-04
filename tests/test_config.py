"""Tests for config loading and validation mechanisms."""

from pathlib import Path

import pytest

from mfrecon.core.config import load_config
from mfrecon.core.exceptions import ConfigurationError, FileAccessError


def test_load_config_valid(tmp_path: Path) -> None:
    """Tests configuration parser loading a valid YAML file."""
    yaml_content = """
engine:
  run_mode: "STRICT"
  amount_epsilon: 0.05
  date_days_tolerance: 5

matching:
  primary_key: "pan"
  enable_fuzzy_matching: true
  fuzzy_threshold: 0.95
  fuzzy_secondary_keys:
    - "mobile"

validation:
  require_pan: true
  validate_kyc_status: false

reporting:
  default_output_formats: ["json"]

sources:
  CAMS:
    available_fields: ["pan", "email"]
    required_fields: ["pan"]
    compare: ["pan", "email"]
    validations: ["pan_format"]
"""
    config_file = tmp_path / "recon_config.yaml"
    config_file.write_text(yaml_content, encoding="utf-8")

    config = load_config(config_file)

    assert config.engine.run_mode == "STRICT"
    assert config.engine.amount_epsilon == 0.05
    assert config.engine.date_days_tolerance == 5
    assert config.matching.enable_fuzzy_matching is True
    assert config.matching.fuzzy_threshold == 0.95
    assert config.matching.fuzzy_secondary_keys == ["mobile"]
    assert config.validation.require_pan is True
    assert config.validation.validate_kyc_status is False
    assert config.reporting.default_output_formats == ["json"]
    assert "CAMS" in config.sources
    assert config.sources["CAMS"].compare == ["pan", "email"]

def test_load_config_invalid_yaml(tmp_path: Path) -> None:
    """Tests configuration parser handles invalid YAML formatting."""
    config_file = tmp_path / "invalid_yaml.yaml"
    config_file.write_text("{invalid: yaml: config", encoding="utf-8")

    with pytest.raises(ConfigurationError):
        load_config(config_file)

def test_load_config_validation_error(tmp_path: Path) -> None:
    """Tests that schema mismatches or invalid fields trigger ConfigurationError."""
    yaml_content = """
engine:
  amount_epsilon: "not-a-number"
"""
    config_file = tmp_path / "invalid_config.yaml"
    config_file.write_text(yaml_content, encoding="utf-8")

    with pytest.raises(ConfigurationError):
        load_config(config_file)

def test_load_config_not_found() -> None:
    """Tests that loading a non-existent configuration file triggers FileAccessError."""
    with pytest.raises(FileAccessError):
        load_config(Path("non_existent_file.yaml"))
