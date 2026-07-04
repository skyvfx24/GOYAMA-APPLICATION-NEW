#!/usr/bin/env python
"""
Smoke test to verify that the Mutual Fund Reconciliation Engine package
is properly installed and that key classes/functions can be imported and initialized.
"""

import sys
from pathlib import Path

# Add project root to sys.path so mfrecon is importable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def main() -> None:
    print("Executing smoke test...")
    try:
        # Import package exports
        from mfrecon import (
            ReconciliationEngine,
            EngineConfig,
            load_config,
            load_config_from_dict,
            ReconciliationResult,
        )
        print("Successfully imported package components:")
        print(f"  - ReconciliationEngine: {ReconciliationEngine}")
        print(f"  - EngineConfig: {EngineConfig}")
        print(f"  - load_config: {load_config}")
        print(f"  - load_config_from_dict: {load_config_from_dict}")
        print(f"  - ReconciliationResult: {ReconciliationResult}")

        # Initialize Default Engine Config
        config = EngineConfig()
        print(f"Successfully created EngineConfig: output_directory='{config.output_directory}'")

        # Load config from a dictionary to verify loader function
        sample_dict = {
            "configure_logging": True,
            "matching": {
                "fuzzy_threshold": 0.92,
                "engine": {
                    "amount_epsilon": 0.05
                }
            }
        }
        loaded_config = load_config_from_dict(sample_dict)
        assert loaded_config.configure_logging is True
        assert loaded_config.matching.fuzzy_threshold == 0.92
        print("Successfully validated load_config_from_dict()")

        # Create ReconciliationEngine instance
        engine = ReconciliationEngine(config)
        print(f"Successfully initialized ReconciliationEngine. Run ID: '{engine.run_id}'")

        print("\n=============================================")
        print("      SMOKE TEST COMPLETED SUCCESSFULLY!      ")
        print("=============================================\n")
        sys.exit(0)

    except Exception as e:
        print(f"\nSmoke test failed with exception: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
