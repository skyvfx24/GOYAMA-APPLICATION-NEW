"""
Error Handling Example for Mutual Fund Reconciliation Engine.

Highlights handling FileAccessError, ParserError, ConfigurationError, 
and inspecting parser warnings/failures in custom integrations.
"""

from pathlib import Path
from mfrecon import ReconciliationEngine, EngineConfig
from mfrecon.core.exceptions import (
    ConfigurationError,
    FileAccessError,
    ParserError,
    MFReconException
)

def run_error_handling_demo() -> None:
    # 1. Catching Configuration errors
    print("--- 1. Testing Configuration Validation ---")
    try:
        # Pass bad data types to verify ConfigurationError mapping
        from mfrecon import load_config_from_dict
        load_config_from_dict({
            "engine": {"amount_epsilon": "NOT_A_FLOAT"}
        })
    except ConfigurationError as e:
        print(f"Caught expected config validation error: {e}")

    # 2. Catching File Access errors
    print("\n--- 2. Testing Missing Files ---")
    config = EngineConfig(output_directory=Path("./error_outputs"), configure_logging=False)
    engine = ReconciliationEngine(config)

    try:
        # Pass a missing file path to verify FileAccessError
        engine.run(Path("missing_crm_file.csv"), [])
    except FileAccessError as e:
        print(f"Caught expected file access error: {e}")

    # 3. Catching Ingestion Parser errors
    print("\n--- 3. Testing Corrupted Ingestion file ---")
    corrupt_file = Path("corrupt_crm.xlsx")
    corrupt_file.write_text("CORRUPTED FILE CONTENTS", encoding="utf-8")

    try:
        # Ingest corrupt excel to verify wrapped ParserError
        engine.run(crm_file_path=corrupt_file, report_file_paths=[])
    except ParserError as e:
        print(f"Caught expected parse error: {e}")
    finally:
        if corrupt_file.exists():
            corrupt_file.unlink()

    # 4. Standard generic exception catch-all
    print("\n--- 4. Generic Exception Wrapper ---")
    try:
        # Invoke standard pipeline run
        engine.run(Path("another_missing.csv"), [])
    except MFReconException as e:
        print(f"Caught generic reconciliation engine base exception: {e}")

if __name__ == "__main__":
    run_error_handling_demo()
