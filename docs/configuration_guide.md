# Configuration Guide

The Mutual Fund Reconciliation Engine utilizes a YAML-based configuration layout to determine parsing columns, data validations, fuzzy matching policies, transaction day tolerances, and report severities.

---

## Sample Configuration File (`recon_config.yaml`)

```yaml
output_directory: "outputs"
configure_logging: false

# Execution and mathematical check settings
engine:
  run_mode: "STRICT"                # STRICT (raise immediately) or TOLERANT (isolated validation)
  amount_epsilon: 0.01              # Holding balance match tolerance delta (in INR)
  date_days_tolerance: 3            # Transaction day offset allowance window

# Record alignment rules
matching:
  primary_key: "pan"
  enable_fuzzy_matching: false
  fuzzy_threshold: 0.90
  fuzzy_secondary_keys:
    - "mobile"
    - "email"
  source_overrides:
    CAMS:
      fuzzy_threshold: 0.85

# KYC and FATCA validation policies
validation:
  require_pan: true
  validate_kyc_status: true
  validate_fatca_status: true
  allowed_kyc_statuses:
    - "VERIFIED"
    - "EXEMPT"
  allowed_fatca_statuses:
    - "COMPLIANT"

# Exporter settings
reporting:
  default_output_formats:
    - "excel"
    - "csv"
    - "json"
  formats: null                     # Null defaults to default_output_formats list
  redact_sensitive_fields: true
  severity_mappings:
    EMAIL_MISMATCH: "MEDIUM"
    AMOUNT_MISMATCH: "HIGH"

# Source-specific column layouts and validations
sources:
  CRM:
    available_fields:
      - "pan"
      - "investor_name"
      - "mobile"
      - "email"
      - "total_amount"
    required_fields:
      - "pan"
      - "investor_name"
    compare:
      - "pan"
      - "investor_name"
    validations:
      - "pan_format"
      - "email_format"

  CAMS:
    available_fields:
      - "pan"
      - "investor_name"
      - "mobile"
      - "total_amount"
    required_fields:
      - "pan"
    compare:
      - "pan"
      - "investor_name"
      - "total_amount"
    validations:
      - "pan_format"
```

---

## Configuration Categories

### 1. Engine settings
* `run_mode`: Configures fail-fast parsing rules vs continuous ingestion pipeline.
* `amount_epsilon`: Numerical tolerance check. Recommended default is `0.01` (1 Paisa) to avoid minor rounding mismatches.
* `date_days_tolerance`: Date proximity tolerance. Crucial for matching bank statements with CRM logs.

### 2. Matching Settings
* `enable_fuzzy_matching`: Uses Jaro-Winkler/Levenshtein string distances to match names if PAN is absent or mismatching. Must be coupled with `fuzzy_secondary_keys` (like mobile/email) to prevent false positives.

### 3. Sources (Source Profiles)
Enables source-specific reconciliation rules framework. If a report source profile does not list a field (e.g. CAMS missing email), the engine skips comparison for that field, preventing false-positive mismatch discrepancy alerts (e.g. email mismatch).
