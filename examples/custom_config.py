"""
Custom Configuration Integration Example for Mutual Fund Reconciliation Engine.

Demonstrates overriding matching logic tolerances, fuzzy similarities, and source mappings.
"""

from pathlib import Path
from mfrecon import ReconciliationEngine, load_config_from_dict

# Minimal dummy files
crm_file = Path("custom_crm.csv")
crm_file.write_text("PAN,Investor Name,Client ID,Mobile\nABCDE1234F,Ramesh Sharma,CRM_003,9876543210\n", encoding="utf-8")

cams_file = Path("custom_cams.csv")
# PAN is different (XYZWP5678Q vs ABCDE1234F) but investor name is similar and mobile matches
cams_file.write_text("PAN,Investor Name,Mobile\nXYZWP5678Q,Ramesh K Sharma,9876543210\n", encoding="utf-8")

# 1. Setup Custom Matching Configurations with Fuzzy Fallbacks enabled
config = load_config_from_dict({
    "output_directory": "./custom_outputs",
    "configure_logging": False,
    "engine": {
        "amount_epsilon": 0.05,
        "date_days_tolerance": 5
    },
    "matching": {
        "primary_key": "pan",
        "enable_fuzzy_matching": True,       # Opt-in to fuzzy matching
        "fuzzy_threshold": 0.80,            # Require 80% similarity on name
        "fuzzy_secondary_keys": ["mobile"]  # Enforce exact mobile check to prevent false-positives
    }
})

try:
    engine = ReconciliationEngine(config)
    result = engine.run(crm_file_path=crm_file, report_file_paths=[cams_file])

    # 2. Check Audits to confirm the fuzzy match route was used
    print("Reconciliation complete!")
    if result.matched_audits:
        print(f"Matched {len(result.matched_audits)} records.")
        for audit in result.matched_audits:
            print(f" - Match route resolved: {audit.route}")
            print(f" - Similarity confidence: {audit.confidence * 100:.1f}%")
            print(f" - Evaluated Source     : {audit.source}")

finally:
    # Cleanup files
    if crm_file.exists():
        crm_file.unlink()
    if cams_file.exists():
        cams_file.unlink()
    import shutil
    if Path("./custom_outputs").exists():
        shutil.rmtree("./custom_outputs")
