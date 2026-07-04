# Client Handover Document

## Mutual Fund Reconciliation Engine v1.0.0

This document summarizes the deliverables, packaging, and execution instructions for the **Mutual Fund Reconciliation Engine** package developed for Goyama Financial Services.

---

## 1. Project Overview

The **Mutual Fund Reconciliation Engine** is a high-performance Python library designed to automate reconciliation of CRM master contact datasets against external broker statements. It supports CAMS, KFintech, BSE, NSE, and PDF Consolidated Account Statements (CAS).

### Core Features
- **Flexible File Parsing**: Automatic source detection, isolation of corrupt parser files, and non-blocking PDF decryption error handling.
- **Normalization Layer**: Streamlined cleanup of PAN identifiers, mobile/email contacts, and KYC/FATCA status mappings.
- **Schema Validation**: Ensures column mappings and checks required fields prior to comparison matching.
- **Discrepancy Engine**: Exact PAN/Folio alignment with optional fuzzy name checking, tolerance thresholds (for date offsets and INR amounts), and comprehensive explainability generation.
- **Multi-Format Export**: Produces executive dashboard Excel workbooks, flat row-streamed CSV databases, and JSON stats files.
- **Safe Application Logging**: Isolated `mfrecon` namespace logging that is opt-in and does not interfere with the client's host framework.

---

## 2. Installation

Verify Python 3.12+ is installed, and execute:

```powershell
# Navigate to the workspace folder and run the build utility
python -m build

# Install the built wheel distribution
pip install .
```

To run development tests:
```powershell
pip install -r requirements.txt
python -m pytest
```

---

## 3. Running CLI

The CLI is registered globally as `mfrecon` upon installation, or can be run via:
```powershell
python -m mfrecon.cli run --crm <crm_master> --reports <reports_list> --output <output_directory>
```

### CLI Command Options
- `--crm`: Path to CRM Excel/CSV spreadsheet.
- `--reports`: Space-separated list of external CAMS, KFintech, BSE, NSE, or PDF statements.
- `--config`: Optional path to custom configuration YAML (defaults to `recon_config.yaml`).
- `--output`: Redirect directory path for final reports.

### Example Run
```powershell
python -m mfrecon.cli run --crm sample_run/input/crm_master.xlsx --reports sample_run/input/cams_report.xlsx sample_run/input/cas_statement.pdf --output sample_run/output
```

---

## 4. Integration Example

Use the engine directly inside host systems using Python:

```python
from pathlib import Path
from mfrecon import ReconciliationEngine, EngineConfig, load_config_from_dict

# Define configuration settings dictionary
config = load_config_from_dict({
    "output_directory": "./client_outputs",
    "configure_logging": True,
    "matching": {
        "enable_fuzzy_matching": True,
        "fuzzy_threshold": 0.88,
        "engine": {
            "amount_epsilon": 0.02,
            "date_days_tolerance": 2
        }
    }
})

# Instantiate and execute E2E flow
engine = ReconciliationEngine(config)
try:
    result = engine.run(
        crm_file_path=Path("sample_run/input/crm_master.xlsx"),
        report_file_paths=[Path("sample_run/input/cams_report.xlsx")]
    )
    print(f"Reconciliation Success. Report saved to: {result.excel_report_path}")
finally:
    engine.close()  # Cleanup resources and logger handlers
```

---

## 5. Folder Structure

The code repository is structured as follows:

```
d:\pythonenginecrm/
├── mfrecon/                      # Core package source directory
│   ├── __init__.py               # Root imports exposing API exports
│   ├── cli.py                    # Argparse command line utility
│   ├── facade.py                 # ReconciliationEngine facade coordinator
│   ├── core/                     # Domain, Configuration, Exceptions, and Interface definitions
│   ├── engine/                   # Reconciler, RecordMatcher, Discrepancy Compiler, and Explainability
│   ├── normalizers/              # Identity, Contact, Status, Date/Amount, and Pipeline normalizations
│   ├── parsers/                  # Base, CAMS, KFintech, BSE, NSE, PDF CAS, and Registry parsers
│   ├── reporters/                # Excel, CSV, JSON, Summary, and Template exporters
│   ├── utils/                    # SHA-256 and Logging setup utilities
│   └── validators/               # Validation Result, Rules, Schema, and Duplicate detectors
├── docs/                         # Detailed system manuals and guides
├── examples/                     # Scripts showing client integration styles
├── releases/                     # Handover packaged ZIP archives
├── sample_run/                   # Sandbox execution folder
│   ├── input/                    # CRM & report files landing folder
│   ├── output/                   # Outputs landing folder
│   └── README.md                 # Sample run guidelines
├── tests/                        # 151 unit test files covering E2E edge cases
├── pyproject.toml                # Project build requirements and entry point
├── requirements.txt              # Package dependencies
├── smoke_test.py                 # Quick installation check script
├── release_checklist.md          # Completed release checklist
├── walkthrough.md                # E2E validation walk-through guide
└── zip_phase8.py                 # Packaging python script
```

---

## 6. Support & Troubleshooting

- **Decryption Failures**: If PDF statements require password encryption, specify password settings in `recon_config.yaml` or programmatically. Files failing decryption are logged to `failed_files` metadata without halting E2E runs.
- **Header Mismatches**: The parser checks standard columns. If columns are renamed, configure source profiles mappings inside `recon_config.yaml`.
- **System Memory Overhead**: For large datasets, the CSV reporter uses memory-efficient streaming to buffer discrepancies to file incrementally.
- **Log Management**: Log handlers are registered only if `configure_logging: true` is requested. Always invoke `engine.close()` inside a `finally` block or context manager to release active file descriptors and logger locks.
