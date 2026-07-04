"""CRM master file parser implementation for CSV and Excel files."""

import hashlib
import re
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger
from pydantic import BaseModel, Field, ValidationError

from mfrecon.core.domain import CRMRecord, FATCAStatus, InvestorStatus, KYCStatus, ReportRecord
from mfrecon.core.exceptions import FileAccessError, ParserError, SchemaMismatchError
from mfrecon.parsers.base import BaseParser
from mfrecon.utils.hash import calculate_sha256

DEFAULT_ALIASES = {
    "pan": ["pan", "pannumber", "panno", "permanentaccountnumber", "pancardnumber", "pancard"],
    "investor_name": ["name", "investorname", "clientname", "fullname", "customername"],
    "mobile": ["mobile", "mobilenumber", "contactnumber", "phone", "phonenumber"],
    "email": ["email", "emailaddress"],
    "kyc_status": ["kyc", "kycstatus", "kyccompliance"],
    "fatca_status": ["fatca", "fatcastatus", "fatcacompliance"],
    "investor_status": ["status", "investorstatus", "clientstatus", "currentstatus"],
    "total_amount": ["amount", "totalamount", "balance", "holdingbalance"],
    "crm_client_id": ["crmclientid", "clientid", "crmid", "id"],
    "tax_status": ["tax_status", "taxstatus", "taxability", "taxcategory", "tax_status_desc"],
    "date_of_birth": ["date_of_birth", "dob", "birth_date", "birthdate"],
    "bank_name": ["bank_name", "bankname", "bank"],
    "bank_account": ["bank_account", "bank_account_number", "account_no", "account_number", "bank_ac", "ac_no", "ac_number"],
    "ifsc": ["ifsc", "ifsc_code", "ifsccode"],
    "registered_address": ["registered_address", "address", "residence_address"],
    "mode_of_holding": ["mode_of_holding", "holding_mode", "mode", "holding_type"],
    "nominee_1": ["nominee", "nominee_1", "nominee_name", "nominee1"],
    "nominee_relation": ["nominee_relation", "nominee_relation_percentage", "relation", "nominee_relationship"],
    "distributor_arn": ["distributor_arn", "arn", "distributor", "broker_code", "broker_arn"]
}

class HeaderMapper:
    """Handles mapping of varied file column headers to standard domain fields."""

    def __init__(self, aliases: dict[str, list[str]] | None = None) -> None:
        """
        Initializes HeaderMapper with a dictionary of field aliases.

        Args:
            aliases: Dict mapping target field names to lists of alias strings.
        """
        self.aliases = aliases or DEFAULT_ALIASES

    def _normalize(self, value: str) -> str:
        """Removes whitespace and non-alphanumeric characters, converts to lowercase."""
        return re.sub(r"[^a-z0-9]+", "", value.strip().lower())

    def map_headers(self, columns: list[str]) -> dict[str, str]:
        """
        Maps source column names to standardized domain keys.

        Args:
            columns: List of columns found in the parsed file.

        Returns:
            Dict[str, str]: Mapping from source column name -> target domain field name.

        Raises:
            SchemaMismatchError: If mandatory fields (pan, investor_name) cannot be resolved.
        """
        mapping: dict[str, str] = {}
        normalized_cols = {self._normalize(col): col for col in columns}

        for target_field, alias_list in self.aliases.items():
            for alias in alias_list:
                normalized_alias = self._normalize(alias)
                if normalized_alias in normalized_cols:
                    source_col = normalized_cols[normalized_alias]
                    mapping[source_col] = target_field
                    break

        # Validate that required fields are mapped
        mapped_targets = set(mapping.values())
        missing_fields = []
        if "pan" not in mapped_targets:
            missing_fields.append("PAN")
        if "investor_name" not in mapped_targets:
            missing_fields.append("Investor Name")

        if missing_fields:
            logger.error(f"Failed to map required headers. Missing: {missing_fields}")
            raise SchemaMismatchError(
                f"Missing required columns: {', '.join(missing_fields)}"
            )

        return mapping


class CRMParseMetadata(BaseModel):
    """Execution metrics and file details for a CRM parsing operation."""
    total_rows: int = Field(..., description="Total rows detected in the source file")
    parsed_rows: int = Field(..., description="Rows parsed successfully into CRMRecord instances")
    failed_rows: int = Field(..., description="Rows failing validation and isolated to DLQ")
    file_hash: str = Field(..., description="SHA-256 integrity checksum of the parsed file")
    file_name: str = Field(..., description="Original name of the parsed file")


class CRMParseResult(BaseModel):
    """Complete result payload returned by the CRMParser."""
    records: list[CRMRecord] = Field(..., description="Successfully parsed and validated CRM records")
    validation_failures: list[dict[str, Any]] = Field(
        ...,
        description="Isolated rows failing validation with index, reason, and raw data"
    )
    metadata: CRMParseMetadata = Field(..., description="Parsing run metadata stats")


class CRMParser(BaseParser):
    """Parser class for loading and validating CRM Master files."""

    def __init__(self, header_mapper: HeaderMapper | None = None) -> None:
        """
        Initializes the CRMParser.

        Args:
            header_mapper: Custom HeaderMapper instance. Uses defaults if None.
        """
        self.header_mapper = header_mapper or HeaderMapper()

    def parse(self, file_path: Path) -> list[ReportRecord]:
        """
        Standard parser interface implementation.
        CRM parsing produces CRMParseResult rather than simple ReportRecords.
        This base method raises NotImplementedError; use parse_crm instead.
        """
        raise NotImplementedError("CRMParser uses parse_crm to return CRMParseResult objects.")

    def parse_crm(self, file_path: Path, sheet_name: str | None = None) -> CRMParseResult:
        """
        Parses and validates a CRM file (CSV or Excel formats).

        Args:
            file_path: Path to the target CRM file.
            sheet_name: Specific sheet name to read (Excel files only).

        Returns:
            CRMParseResult: Ingestion results container.

        Raises:
            FileAccessError: If the file is missing or unreadable.
            ParserError: If parsing fails completely or columns cannot be resolved.
        """
        self.check_file_exists(file_path)

        # Check for empty file
        if file_path.stat().st_size == 0:
            logger.error(f"CRM parser failed: file {file_path.name} is empty.")
            raise ParserError(f"CRM file is empty: {file_path.name}")

        # Compute file hash
        file_hash = calculate_sha256(file_path)
        suffix = file_path.suffix.lower()

        # Ingest file into pandas DataFrame
        df: pd.DataFrame
        try:
            if suffix == ".csv":
                try:
                    df = self._read_csv(file_path)
                except Exception as csv_err:
                    # Check if file has ZIP signature indicating Excel XLSX/XLS format
                    try:
                        with file_path.open("rb") as f:
                            sig = f.read(2)
                        if sig == b"PK":
                            logger.info(f"File {file_path.name} has Excel signature despite .csv extension. Falling back to Excel reader.")
                            df = self._read_excel(file_path, sheet_name)
                        else:
                            raise csv_err
                    except Exception:
                        raise csv_err
            elif suffix in (".xlsx", ".xls"):
                df = self._read_excel(file_path, sheet_name)
            else:
                logger.error(f"Unsupported CRM file extension: {suffix}")
                raise ParserError(f"Unsupported file type: {suffix}")
        except Exception as e:
            if not isinstance(e, ParserError):
                logger.error(f"Pandas failed to read file: {e}")
                if isinstance(e, (PermissionError, FileNotFoundError, OSError)):
                    raise FileAccessError(f"Access denied or file unreadable: {e}") from e
                raise ParserError(f"Failed to read file: {e}") from e
            raise

        total_rows = len(df)
        if total_rows == 0:
            # File has headers but 0 rows
            return CRMParseResult(
                records=[],
                validation_failures=[],
                metadata=CRMParseMetadata(
                    total_rows=0,
                    parsed_rows=0,
                    failed_rows=0,
                    file_hash=file_hash,
                    file_name=file_path.name
                )
            )

        # Auto-combine split name columns (First/Middle/Last) and split address/bank columns
        df = self.combine_split_columns(df)

        # Execute header mapping
        columns = [str(col) for col in df.columns]
        header_mapping = self.header_mapper.map_headers(columns)

        # Rename columns to standardized names and convert dataframe to dictionary list
        df_mapped = df.rename(columns=header_mapping)
        raw_rows = df.to_dict(orient="records")
        mapped_rows = df_mapped.to_dict(orient="records")

        records: list[CRMRecord] = []
        validation_failures: list[dict[str, Any]] = []

        for idx, mapped_row in enumerate(mapped_rows):
            row_number = idx + 2  # 1-indexed plus header row offset
            raw_data = raw_rows[idx]

            # Null values cleanup in pandas (NaN -> None)
            cleaned_row = {k: (None if pd.isna(v) else v) for k, v in mapped_row.items()}

            # Keep only standard fields
            domain_data = {
                k: v for k, v in cleaned_row.items()
                if k in ("pan", "investor_name", "mobile", "email", "kyc_status",
                         "fatca_status", "investor_status", "total_amount", "crm_client_id", "tax_status",
                         "date_of_birth", "bank_name", "bank_account", "ifsc", "registered_address",
                         "mode_of_holding", "nominee_1", "nominee_relation", "distributor_arn")
            }

            tax_status_val, is_minor = self.check_minor_account(raw_data, header_mapping)
            domain_data["tax_status"] = tax_status_val
            domain_data["is_minor_account"] = is_minor


            # Inject placeholder client id if missing (since it's a required field in CRMRecord model)
            if "crm_client_id" not in domain_data or domain_data["crm_client_id"] is None:
                domain_data["crm_client_id"] = f"AUTO_GEN_{uuid_like(idx)}"

            # Force string format on string fields to coerce floats/ints from Excel
            string_fields = ("pan", "investor_name", "mobile", "email", "crm_client_id", "tax_status",
                             "date_of_birth", "bank_name", "bank_account", "ifsc", "registered_address",
                             "mode_of_holding", "nominee_1", "nominee_relation", "distributor_arn")
            for field in string_fields:
                if field in domain_data and domain_data[field] is not None:
                    val = domain_data[field]
                    if isinstance(val, float):
                        if pd.isna(val):
                            domain_data[field] = None
                        elif val.is_integer():
                            domain_data[field] = str(int(val))
                        else:
                            domain_data[field] = str(val)
                    elif isinstance(val, (int, Decimal)):
                        domain_data[field] = str(val)
                    else:
                        val_str = str(val).strip()
                        if val_str == "" or val_str.lower() in ("nan", "none", "n/a", "-"):
                            domain_data[field] = None
                        else:
                            domain_data[field] = val_str

            # Convert total_amount to Decimal safely
            if "total_amount" in domain_data and domain_data["total_amount"] is not None:
                try:
                    amt_str = str(domain_data["total_amount"]).replace(",", "").strip()
                    domain_data["total_amount"] = Decimal(amt_str)
                except (ValueError, TypeError, ArithmeticError):
                    pass

            # Check mandatory values
            if not domain_data.get("pan") or not domain_data.get("investor_name"):
                missing = []
                if not domain_data.get("pan"):
                    missing.append("PAN")
                if not domain_data.get("investor_name"):
                    missing.append("Investor Name")

                validation_failures.append({
                    "row_number": row_number,
                    "reason": f"Missing required fields: {', '.join(missing)}",
                    "raw_data": raw_data
                })
                continue

            # Parse Enums or fall back to UNKNOWN
            for field, enum_cls in (
                ("kyc_status", KYCStatus),
                ("fatca_status", FATCAStatus),
                ("investor_status", InvestorStatus)
            ):
                if field in domain_data and domain_data[field] is not None:
                    # Save raw KYC string before normalising to enum
                    if field == "kyc_status":
                        domain_data["kyc_status_raw"] = str(domain_data[field]).strip()
                    domain_data[field] = self.resolve_enum_status(domain_data[field], enum_cls)
                else:
                    domain_data[field] = enum_cls.UNKNOWN

            # Run Pydantic model validation
            try:
                crm_record = CRMRecord.model_validate(domain_data)
                records.append(crm_record)
            except ValidationError as e:
                reasons = [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
                validation_failures.append({
                    "row_number": row_number,
                    "reason": "; ".join(reasons),
                    "raw_data": raw_data
                })

        metadata = CRMParseMetadata(
            total_rows=total_rows,
            parsed_rows=len(records),
            failed_rows=len(validation_failures),
            file_hash=file_hash,
            file_name=file_path.name
        )

        logger.info(
            f"CRM Parsing Complete: {file_path.name}. Total: {total_rows}, "
            f"Parsed: {len(records)}, Failed: {len(validation_failures)}"
        )

        return CRMParseResult(
            records=records,
            validation_failures=validation_failures,
            metadata=metadata
        )

    def _read_csv(self, file_path: Path) -> pd.DataFrame:
        """Reads CSV file trying multiple standard encodings."""
        encodings = ["utf-8", "latin-1", "cp1252"]
        for encoding in encodings:
            try:
                # Read CSV and strip column names
                df = pd.read_csv(file_path, encoding=encoding)
                df.columns = df.columns.str.strip()
                return df
            except UnicodeDecodeError:
                continue
        raise ParserError(f"Could not decode CSV file {file_path.name} using standard encodings.")

    def _read_excel(self, file_path: Path, sheet_name: str | None = None) -> pd.DataFrame:
        """Reads Excel file auto-detecting first sheet if none specified."""
        try:
            excel_file = pd.ExcelFile(file_path)
        except Exception as e:
            raise ParserError(f"Failed to load Excel file structure: {e}") from e

        if not sheet_name:
            # Auto-detect worksheet: choose the first sheet
            sheet_name = excel_file.sheet_names[0]
            logger.debug(f"Auto-selected worksheet: '{sheet_name}'")

        try:
            df = excel_file.parse(sheet_name=sheet_name)
            df.columns = df.columns.astype(str).str.strip()
            return df
        except Exception as e:
            raise ParserError(f"Failed to parse sheet '{sheet_name}' in {file_path.name}: {e}") from e


def uuid_like(index: int) -> str:
    """Generates a reproducible 8-character hash based on row index."""
    h = hashlib.md5(str(index).encode())
    return h.hexdigest()[:8]
