"""
Batch Processing Integration Example for Mutual Fund Reconciliation Engine.

Demonstrates scanning directories for transaction reports, resolving files, 
and invoking batch executions while handling isolated parsing errors.
"""

import shutil
from pathlib import Path
from mfrecon import ReconciliationEngine, load_config_from_dict


def run_batch_reconciliation() -> None:
    # Set up folders
    reports_dir = Path("./reports_batch")
    reports_dir.mkdir(exist_ok=True)
    outputs_dir = Path("./batch_outputs")

    try:
        # Create dummy CRM file
        crm_file = Path("batch_crm.csv")
        crm_file.write_text("PAN,Investor Name,Client ID\nABCDE1234F,Alice Smith,CRM_002\n", encoding="utf-8")

        # Create some report files in the reports folder
        cams_report = reports_dir / "cams.csv"
        cams_report.write_text("PAN,Investor Name\nABCDE1234F,Alice Smith\n", encoding="utf-8")

        # Create a bad file (e.g. invalid empty file)
        corrupt_report = reports_dir / "corrupt_data.xlsx"
        corrupt_report.write_text("CORRUPTED TEXT EXCEL", encoding="utf-8")

        # 1. Scan the reports folder for PDF, CSV, Excel files
        supported_suffixes = {".csv", ".xlsx", ".xls", ".pdf"}
        batch_files = [
            file_path for file_path in reports_dir.iterdir()
            if file_path.is_file() and file_path.suffix.lower() in supported_suffixes
        ]

        print(f"Found {len(batch_files)} potential reports to reconcile in batch.")

        # 2. Setup engine config
        config = load_config_from_dict({
            "output_directory": str(outputs_dir),
            "configure_logging": False
        })
        engine = ReconciliationEngine(config)

        # 3. Trigger reconciliation run
        # Note: corrupted files (like corrupt_report) will be isolated automatically
        # in result.metadata.failed_files rather than crashing the execution.
        result = engine.run(crm_file_path=crm_file, report_file_paths=batch_files)

        print("\n--- Batch Run Results ---")
        print(f"Processed CRM Records: {result.metadata.total_crm_records}")
        print(f"Processed Report Records: {result.metadata.total_report_records}")
        print(f"Discrepancies Found: {result.metadata.discrepancies_count}")
        print(f"Successful Audits: {len(result.matched_audits)}")

        # Print failures details
        if result.metadata.failed_files:
            print(f"\nIdentified {len(result.metadata.failed_files)} file failures during batch:")
            for failure in result.metadata.failed_files:
                print(f" - File: {failure.file_name} | Type: {failure.failure_type} | Error: {failure.message}")

    finally:
        # Clean up batch directories
        if reports_dir.exists():
            shutil.rmtree(reports_dir)
        if Path("batch_crm.csv").exists():
            Path("batch_crm.csv").unlink()
        if outputs_dir.exists():
            shutil.rmtree(outputs_dir)


if __name__ == "__main__":
    run_batch_reconciliation()
