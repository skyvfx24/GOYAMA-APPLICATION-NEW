# Integration Guide (API Reference)

This document describes the primary Python API classes and functions exposed by the `mfrecon` package.

---

## 1. `ReconciliationEngine`
The central facade orchestrator managing the ingestion, normalization, validation, matching, and report generation pipeline.

### Initialization
```python
from mfrecon import ReconciliationEngine, EngineConfig

# Initialize engine with EngineConfig
engine = ReconciliationEngine(config: EngineConfig)
```

### Methods
#### `run(crm_file_path: str | Path, report_file_paths: Sequence[str | Path]) -> ReconciliationResult`
Executes E2E reconciliation pipeline.

* **Parameters**:
  * `crm_file_path` (`str | Path`): File location of the internal CRM master CSV/Excel.
  * `report_file_paths` (`Sequence[str | Path]`): Iterable sequence of external report CSV/Excel/PDF paths.
* **Returns**:
  * `ReconciliationResult`: Complete structured outputs and metrics payload.
* **Raises**:
  * `FileAccessError`: If files are missing, unreadable, or locked.
  * `ParserError`: If file content fails parsing structure checks.

#### `close() -> None`
Deregisters custom Loguru handlers created by the engine. Recommended in serverless or multi-threaded executions.

---

## 2. `EngineConfig`
A Pydantic validation configuration model loaded from files or parsed directly from dictionaries.

### Loaders
#### `load_config(yaml_path: Path) -> EngineConfig`
Loads config options from a YAML file.

#### `load_config_from_dict(data: dict[str, Any]) -> EngineConfig`
Validates and generates config objects from in-memory dictionary data blocks.

* **Example**:
  ```python
  from mfrecon import load_config_from_dict

  config = load_config_from_dict({
      "output_directory": "/tmp/reports",
      "configure_logging": True,
      "engine": {"amount_epsilon": 0.05}
  })
  ```

---

## 3. `ReconciliationResult`
The output container returned upon execution completion.

### Attributes
* `metadata` (`ReconciliationRunMetadata`): Ingestion counts, checksum records, execution date, and isolated file failures.
* `discrepancies` (`list[Discrepancy]`): List of mismatches containing:
  * `discrepancy_type`: e.g. `AMOUNT_MISMATCH`, `NAME_MISMATCH`.
  * `field_name`: Target field name showing differences.
  * `crm_value`: Recorded database value.
  * `report_value`: Mapped external report value.
  * `severity`: `CRITICAL`, `HIGH`, `MEDIUM`, or `LOW`.
  * `explanation`: Plain-English natural language mismatch explanation.
* `excel_report_path` (`str | None`): Absolute file location of generated spreadsheet.
* `csv_report_path` (`str | None`): Absolute CSV discrepancies directory path.
* `json_report_path` (`str | None`): Absolute JSON file path.
* `matched_audits` (`list[MatchedAudit]`): Audits trace collection for successfully matching items (resolving matching confidence routes and skipped validation compares).
