# Quick Start Guide

Get up and running with the **Mutual Fund Reconciliation Engine** (mfrecon) using the Command Line Interface (CLI) or as a programmatic library integration.

---

## 1. Command Line Interface (CLI)

The CLI exposes the `run` command to run reconciliation on local CSV and Excel spreadsheets.

### Basic CLI Command Execution
Execute a reconciliation run using a CRM Master CSV file and transaction report files:

```bash
mfrecon run \
  --crm path/to/crm_master.csv \
  --reports path/to/cams_report.xlsx path/to/kfintech.csv \
  --output ./outputs
```

### Advanced Run using Custom Config YAML
Provide a specific settings configuration YAML block to customize matching rules:

```bash
mfrecon run \
  --crm crm_master.xlsx \
  --reports cams.xlsx kfintech.csv \
  --config recon_config.yaml \
  --output ./custom_outputs
```

---

## 2. Programmatic Integration

You can integrate the reconciliation engine directly into your Python scripts or web servers (e.g. Django, FastAPI):

```python
from pathlib import Path
from mfrecon import ReconciliationEngine, EngineConfig, load_config

# 1. Initialize configuration (Default settings or loaded from YAML)
config = load_config(Path("recon_config.yaml"))
config.output_directory = Path("./reconciliation_reports")

# 2. Instantiate the orchestrator engine
engine = ReconciliationEngine(config)

# 3. Trigger E2E reconciliation pipeline
result = engine.run(
    crm_file_path=Path("crm_master.csv"),
    report_file_paths=[
        Path("reports/cams.xlsx"),
        Path("reports/kfintech.xlsx")
    ]
)

# 4. View generated report filesystem locations
print("Reconciliation complete!")
print(f"Run ID: {result.metadata.run_id}")
print(f"Excel Report: {result.excel_report_path}")
print(f"CSV Report  : {result.csv_report_path}")
print(f"JSON Report : {result.json_report_path}")
```
