"""
Simple Integration Example for Mutual Fund Reconciliation Engine.

Demonstrates programmatic engine runs using default and in-memory dictionary settings.
"""

from pathlib import Path
from mfrecon import ReconciliationEngine, load_config_from_dict

# 1. Prepare minimal dummy files for demonstration
crm_file = Path("simple_crm.csv")
crm_file.write_text("PAN,Investor Name,Client ID\nABCDE1234F,John Doe,CRM_001\n", encoding="utf-8")

cams_file = Path("simple_cams.csv")
cams_file.write_text("PAN,Investor Name,Folio Number\nABCDE1234F,John Doe,98765\n", encoding="utf-8")

# 2. Configure engine using inline dictionary parameters
config = load_config_from_dict({
    "output_directory": "./outputs",
    "configure_logging": True,
    "engine": {
        "run_mode": "TOLERANT",
        "amount_epsilon": 0.01
    }
})

try:
    # 3. Initialize the Engine
    engine = ReconciliationEngine(config)

    # 4. Trigger reconciliation E2E
    result = engine.run(crm_file_path=crm_file, report_file_paths=[cams_file])

    # 5. Review Output Report Locations
    print("Reconciliation executed successfully!")
    print(f"Run ID      : {result.metadata.run_id}")
    print(f"Excel Report: {result.excel_report_path}")
    print(f"CSV Report  : {result.csv_report_path}")
    print(f"JSON Report : {result.json_report_path}")

finally:
    # Clean up generated files
    if crm_file.exists():
        crm_file.unlink()
    if cams_file.exists():
        cams_file.unlink()
