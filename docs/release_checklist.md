# Release Validation Checklist (v1.0.0)

This checklist provides the verification criteria and manual/automated checks required to approve the release candidate of the **Mutual Fund Reconciliation Engine** package.

---

## 1. Package Installation & Namespace
- `[x]` Run `python -m build` to compile the library without packaging errors.
- `[x]` Confirm wheel `dist/mfrecon-1.0.0-py3-none-any.whl` and source tarball `dist/mfrecon-1.0.0.tar.gz` are generated.
- `[x]` Install the package locally via `pip install .` and verify the package is registered.
- `[x]` Run `python -c "import mfrecon; print(mfrecon.__all__)"` and confirm the output prints:
  `['ReconciliationEngine', 'EngineConfig', 'load_config', 'load_config_from_dict', 'ReconciliationResult']`.

---

## 2. Command Line Interface (CLI)
- `[x]` Run `mfrecon --help` and verify help usage instruction options print correctly.
- `[x]` Execute the CLI with string file paths:
  `mfrecon run --crm crm.csv --reports cams.csv kfintech.csv --output ./outputs`
- `[x]` Verify the console displays progress logs, run ID, and file paths.
- `[x]` Confirm exit codes:
  * `0` on successful reconciliation execution.
  * `1` on custom engine exception (e.g. missing files).
  * `2` on unexpected syntax/command line parsing failures.

---

## 3. Configuration & Loader
- `[x]` Verify loading of configuration YAML settings using `load_config(yaml_path)`.
- `[x]` Verify loading of in-memory dictionaries using `load_config_from_dict(config_dict)`.
- `[x]` Verify that invalid configuration values (e.g. `amount_epsilon` set to string) raise a wrapped `ConfigurationError`.

---

## 4. Report Generation Outputs
- `[x]` Run reconciliation and verify the output folder contains:
  * Excel spreadsheet: `discrepancies_{run_id}.xlsx` (containing Summary, Discrepancies, Missing In CRM, Missing In Report, Exact Duplicates, Conflicting Duplicates, Failed Files, and Audit Summary sheets).
  * CSV files: `discrepancies.csv`, `matched.csv`, `unmatched.csv`, `failed_files.csv`.
  * JSON document: `discrepancies_{run_id}.json` (matching statistics schema).
- `[x]` Load the Excel file and verify:
  * Gridlines are enabled on all worksheets.
  * Auto auto-fit column widths are applied.
  * Header fill is styled as sleek dark blue (`#1F4E79`).
  * Zebra striping is applied to even data rows.
  * Tables have freeze panes set to `"A2"`.

---

## 5. Error Wrapping & Decryption Isolation
- `[x]` Run reconciliation on a corrupt or missing CRM master file and confirm the engine raises wrapped Custom Exceptions (`FileAccessError` or `ParserError`) rather than exposing raw pandas/openpyxl tracebacks.
- `[x]` Run reconciliation on a batch of files where one PDF CAS file is password-protected/encrypted and key is incorrect. Verify:
  * Execution does not halt and continues for the remaining files.
  * The decryption failure is isolated and listed inside `failed_files` metadata logs.

---

## 6. Logging Safety & Namespace Isolation
- `[x]` Verify that when `configure_logging: false` (default), no custom Loguru handlers are registered.
- `[x]` Verify that when `configure_logging: true`, the library configures handlers (stderr console, debug file, JSON line audit trail) that ONLY capture statements originating from the `"mfrecon"` namespace.
- `[x]` Verify that pre-existing host application handlers are preserved intact and receive engine output logs.
- `[x]` Verify that library handlers are cleanly removed from Loguru when the engine is closed or garbage collected, preventing handler leaks.
