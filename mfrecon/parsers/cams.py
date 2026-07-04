"""Parser implementation for CAMS mutual fund report files."""

from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger
from pydantic import ValidationError

from mfrecon.core.domain import FATCAStatus, InvestorStatus, KYCStatus, RecordSource, ReportRecord
from mfrecon.core.exceptions import ParserError
from mfrecon.parsers.base import BaseParser
from mfrecon.parsers.crm import HeaderMapper
from mfrecon.parsers.report_result import ReportParseMetadata, ReportParseResult
from mfrecon.utils.hash import calculate_sha256

CAMS_ALIASES = {
    "pan": ["pan", "pannumber", "panno", "permanentaccountnumber"],
    "investor_name": ["name", "investorname", "clientname", "investor_name"],
    "mobile": ["mobile", "mobilenumber", "contactnumber", "phone", "phonenumber"],
    "email": ["email", "emailaddress"],
    "kyc_status": ["kyc", "kycstatus", "kyccompliance"],
    "fatca_status": ["fatca", "fatcastatus", "fatcacompliance"],
    "investor_status": ["status", "investorstatus", "clientstatus"],
    "total_amount": ["amount", "totalamount", "balance", "holdingbalance"],
    "folio_number": ["folio", "folionumber", "foliono"],
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

class CAMSParser(BaseParser):
    """Parser class for loading and validating CAMS reports."""

    def __init__(self, header_mapper: HeaderMapper | None = None) -> None:
        self.header_mapper = header_mapper or HeaderMapper(aliases=CAMS_ALIASES)
        self.source = RecordSource.CAMS

    def parse(self, file_path: Path) -> list[ReportRecord]:
        """Parses CAMS file and returns a flat list of successfully validated ReportRecord objects."""
        result = self.parse_report(file_path)
        return result.records

    def parse_report(self, file_path: Path, sheet_name: str | None = None) -> ReportParseResult:
        """
        Parses a CAMS report (CSV or Excel) and returns a detailed ReportParseResult.

        Args:
            file_path: Path to the target report file.
            sheet_name: Specific sheet name to read (Excel only).

        Returns:
            ReportParseResult: Ingestion results container.
        """
        self.check_file_exists(file_path)

        if file_path.stat().st_size == 0:
            logger.error(f"CAMS parser failed: file {file_path.name} is empty.")
            raise ParserError(f"CAMS report file is empty: {file_path.name}")

        file_hash = calculate_sha256(file_path)
        suffix = file_path.suffix.lower()

        # Ingest file into pandas DataFrame
        df: pd.DataFrame
        try:
            if suffix == ".csv":
                df = self._read_csv(file_path)
            elif suffix in (".xlsx", ".xls"):
                df = self._read_excel(file_path, sheet_name)
            else:
                logger.error(f"Unsupported CAMS report extension: {suffix}")
                raise ParserError(f"Unsupported file type: {suffix}")
        except Exception as e:
            if not isinstance(e, ParserError):
                logger.error(f"Pandas failed to read file: {e}")
                raise ParserError(f"Failed to read file: {e}") from e
            raise

        total_rows = len(df)
        if total_rows == 0:
            return ReportParseResult(
                records=[],
                validation_failures=[],
                metadata=ReportParseMetadata(
                    source=self.source,
                    file_name=file_path.name,
                    file_hash=file_hash,
                    total_rows=0,
                    parsed_rows=0,
                    failed_rows=0
                )
            )

        # Combine split name / address / bank columns before header mapping
        df = self.combine_split_columns(df)

        # Execute header mapping
        columns = [str(col) for col in df.columns]
        header_mapping = self.header_mapper.map_headers(columns)

        # Rename columns to standardized names and convert dataframe to dictionary list
        df_mapped = df.rename(columns=header_mapping)
        raw_rows = df.to_dict(orient="records")
        mapped_rows = df_mapped.to_dict(orient="records")

        records: list[ReportRecord] = []
        validation_failures: list[dict[str, Any]] = []

        for idx, mapped_row in enumerate(mapped_rows):
            row_number = idx + 2
            raw_data = raw_rows[idx]

            # Null values cleanup in pandas (NaN -> None)
            cleaned_row = {k: (None if pd.isna(v) else v) for k, v in mapped_row.items()}

            # Keep only standard fields and inject source/index
            domain_data: dict[str, Any] = {
                k: v for k, v in cleaned_row.items()
                if k in ("pan", "investor_name", "mobile", "email", "kyc_status",
                         "fatca_status", "investor_status", "total_amount", "folio_number", "tax_status",
                         "date_of_birth", "bank_name", "bank_account", "ifsc", "registered_address",
                         "mode_of_holding", "nominee_1", "nominee_relation", "distributor_arn")
            }
            domain_data["source"] = self.source
            domain_data["raw_row_index"] = row_number

            # Extract missing/empty fields
            missing, empty = self.extract_missing_and_empty_fields(raw_data, header_mapping)
            domain_data["missing_fields"] = missing
            domain_data["empty_fields"] = empty

            # Minor account awareness
            tax_status_val, is_minor = self.check_minor_account(raw_data, header_mapping)
            domain_data["tax_status"] = tax_status_val
            domain_data["is_minor_account"] = is_minor


            # Force string format on string fields to coerce floats/ints from Excel
            string_fields = ("pan", "investor_name", "mobile", "email", "folio_number", "tax_status",
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
                    "source": self.source,
                    "reason": f"Missing required fields: {', '.join(missing)}",
                    "raw_data": raw_data
                })
                continue

            # Parse Enums or fall back to UNKNOWN
            for enum_field, enum_cls in (
                ("kyc_status", KYCStatus),
                ("fatca_status", FATCAStatus),
                ("investor_status", InvestorStatus)
            ):
                if enum_field in domain_data and domain_data[enum_field] is not None:
                    # Save the raw KYC string before normalising to enum
                    if enum_field == "kyc_status":
                        domain_data["kyc_status_raw"] = str(domain_data[enum_field]).strip()
                    domain_data[enum_field] = self.resolve_enum_status(domain_data[enum_field], enum_cls)
                else:
                    domain_data[enum_field] = enum_cls.UNKNOWN

            # Run Pydantic model validation
            try:
                report_record = ReportRecord.model_validate(domain_data)
                records.append(report_record)
            except ValidationError as e:
                reasons = [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
                validation_failures.append({
                    "row_number": row_number,
                    "source": self.source,
                    "reason": "; ".join(reasons),
                    "raw_data": raw_data
                })

        metadata = ReportParseMetadata(
            source=self.source,
            file_name=file_path.name,
            file_hash=file_hash,
            total_rows=total_rows,
            parsed_rows=len(records),
            failed_rows=len(validation_failures)
        )

        logger.info(
            f"CAMS Parsing Complete: {file_path.name}. Total: {total_rows}, "
            f"Parsed: {len(records)}, Failed: {len(validation_failures)}"
        )

        return ReportParseResult(
            records=records,
            validation_failures=validation_failures,
            metadata=metadata
        )

    def _read_csv(self, file_path: Path) -> pd.DataFrame:
        """Reads CSV file trying multiple standard encodings."""
        encodings = ["utf-8", "latin-1", "cp1252"]
        for encoding in encodings:
            try:
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
            sheet_name = excel_file.sheet_names[0]

        try:
            df = excel_file.parse(sheet_name=sheet_name)
            df.columns = df.columns.astype(str).str.strip()
            return df
        except Exception as e:
            raise ParserError(f"Failed to parse sheet '{sheet_name}' in {file_path.name}: {e}") from e

