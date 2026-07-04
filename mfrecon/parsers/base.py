"""Base class for all report and CRM parsers."""

from abc import ABC, abstractmethod
from pathlib import Path

from mfrecon.core.domain import ReportRecord
from mfrecon.core.exceptions import FileAccessError
from mfrecon.core.interfaces import ParserInterface


class BaseParser(ParserInterface, ABC):
    """
    Abstract Base Class providing common utility methods and parsing structures.

    All specific parser implementations should inherit from this class.
    """

    def check_file_exists(self, file_path: Path) -> None:
        """
        Validates that the file exists and is a regular file.

        Args:
            file_path: File path to check.

        Raises:
            FileAccessError: If the file does not exist or is not a file.
        """
        if not file_path.exists():
            raise FileAccessError(f"Target file does not exist: {file_path}")
        if not file_path.is_file():
            raise FileAccessError(f"Target path is not a file: {file_path}")

    @abstractmethod
    def parse(self, file_path: Path) -> list[ReportRecord]:
        """
        Abstract parsing method that concrete classes must implement.

        Args:
            file_path: The filesystem Path to parse.

        Returns:
            List[ReportRecord]: List of structured report rows.
        """
        pass

    def extract_missing_and_empty_fields(
        self, 
        raw_row: dict[str, Any], 
        header_mapping: dict[str, str] | None = None
    ) -> tuple[list[str], list[str]]:
        """Identifies standard fields that are missing from the headers or empty in the row."""
        import pandas as pd
        from typing import Any

        standard_fields = [
            "pan",
            "investor_name",
            "mobile",
            "email",
            "kyc_status",
            "fatca_status",
            "investor_status",
            "last_transaction_date",
            "total_amount"
        ]

        missing = []
        empty = []

        if header_mapping is not None:
            # Target field to source column mapping
            target_to_source = {v: k for k, v in header_mapping.items()}
            for field in standard_fields:
                if field not in target_to_source:
                    missing.append(field)
                else:
                    source_col = target_to_source[field]
                    val = raw_row.get(source_col)
                    if val is None or pd.isna(val) or str(val).strip() == "":
                        empty.append(field)
        else:
            # Fallback for dict-based parsers like PDF CAS
            for field in standard_fields:
                if field not in raw_row:
                    missing.append(field)
                else:
                    val = raw_row.get(field)
                    if val is None or pd.isna(val) or str(val).strip() == "":
                        empty.append(field)

        return missing, empty

    @staticmethod
    def resolve_enum_status(raw_val: str, enum_cls: type) -> Any:
        """
        Resolves a raw string value (from an uploaded file) to the correct enum variant.
        Handles common synonyms for KYCStatus, FATCAStatus, and InvestorStatus before
        falling back to the UNKNOWN variant.
        """
        from mfrecon.core.domain import KYCStatus, FATCAStatus, InvestorStatus

        val = str(raw_val).strip().upper()

        # Try direct match first
        try:
            return enum_cls(val)
        except ValueError:
            pass

        # KYC synonyms
        if enum_cls is KYCStatus:
            KYC_VERIFIED = {
                'K', 'KYC', 'YES', 'Y', 'VALID', 'OK', 'VERIFIED',
                'COMPLIANT', 'KRA COMPLIANT', 'KRA-COMPLIANT',
                'KYC OK', 'KYC VERIFIED', 'KYC COMPLIANT',
                'COMPLIANT / VERIFIED', 'KYC DONE', 'KYC COMPLETE',
                'REGISTERED', 'VALID KYC', 'DONE'
            }
            KYC_PENDING = {'PENDING', 'IN PROGRESS', 'PROCESSING', 'UNDER REVIEW', 'SUBMITTED'}
            KYC_FAILED = {'FAILED', 'REJECTED', 'INVALID', 'NO', 'N', 'NOT VERIFIED', 'NOT COMPLIANT'}
            KYC_EXEMPT = {'EXEMPT', 'EXEMPTED', 'PAN EXEMPT', 'MINOR EXEMPT'}
            if val in KYC_VERIFIED:
                return KYCStatus.VERIFIED
            if val in KYC_PENDING:
                return KYCStatus.PENDING
            if val in KYC_FAILED:
                return KYCStatus.FAILED
            if val in KYC_EXEMPT:
                return KYCStatus.EXEMPT

        # FATCA synonyms
        if enum_cls is FATCAStatus:
            FATCA_COMPLIANT = {'C', 'YES', 'Y', 'COMPLIANT', 'FATCA COMPLIANT', 'VALID', 'OK', 'DONE'}
            FATCA_NON = {'NON_COMPLIANT', 'NON COMPLIANT', 'NC', 'NO', 'N', 'NOT COMPLIANT', 'FAILED'}
            FATCA_PENDING = {'PENDING', 'IN PROGRESS', 'SUBMITTED'}
            if val in FATCA_COMPLIANT:
                return FATCAStatus.COMPLIANT
            if val in FATCA_NON:
                return FATCAStatus.NON_COMPLIANT
            if val in FATCA_PENDING:
                return FATCAStatus.PENDING

        # InvestorStatus synonyms
        if enum_cls is InvestorStatus:
            ACTIVE = {'A', 'ACTIVE', 'ENABLED', 'LIVE', 'YES', 'Y'}
            INACTIVE = {'I', 'INACTIVE', 'DISABLED', 'CLOSED', 'NO', 'N'}
            SUSPENDED = {'S', 'SUSPENDED', 'BLOCKED', 'FROZEN', 'DEACTIVATED'}
            if val in ACTIVE:
                return InvestorStatus.ACTIVE
            if val in INACTIVE:
                return InvestorStatus.INACTIVE
            if val in SUSPENDED:
                return InvestorStatus.SUSPENDED

        return enum_cls.UNKNOWN

    def check_minor_account(
        self, 
        raw_row: dict[str, Any], 
        header_mapping: dict[str, str] | None = None
    ) -> tuple[str | None, bool]:
        """Checks if the tax status indicates a minor account."""
        tax_status = None
        if header_mapping is not None:
            target_to_source = {v: k for k, v in header_mapping.items()}
            source_col = target_to_source.get("tax_status")
            if source_col:
                tax_status = raw_row.get(source_col)
        else:
            tax_status = raw_row.get("tax_status")

        is_minor = False
        if tax_status is not None:
            tax_str = str(tax_status).upper()
            if "MINOR" in tax_str or "ON BEHALF OF MINOR" in tax_str:
                is_minor = True

        return str(tax_status) if tax_status is not None else None, is_minor

    def combine_split_columns(self, df: "pd.DataFrame") -> "pd.DataFrame":
        """
        Auto-detects and combines split name and address columns into single fields.
        Handles BSE/NSE format: 'Primary Holder First/Middle/Last Name',
        multi-part bank/address columns, and Nominee 1 Name / Relationship.
        Returns the DataFrame with combined columns added.
        Uses a single pd.concat at the end to avoid fragmentation warnings.
        """
        import pandas as pd

        cols_lower = {col.lower().strip(): col for col in df.columns}
        # Collect all new derived columns in this dict, then concat once at the end
        new_cols: dict[str, "pd.Series"] = {}

        # --- Full investor name from split first/middle/last ---
        has_full = any(k in cols_lower for k in (
            "name", "investor name", "investorname", "clientname", "fullname", "customer name"
        ))
        if not has_full:
            first = next((cols_lower[k] for k in (
                "primary holder first name", "first name", "firstname", "first_name"
            ) if k in cols_lower), None)
            last = next((cols_lower[k] for k in (
                "primary holder last name", "last name", "lastname", "last_name"
            ) if k in cols_lower), None)
            middle = next((cols_lower[k] for k in (
                "primary holder middle name", "middle name", "middlename", "middle_name"
            ) if k in cols_lower), None)
            if first and last:
                parts = [df[first].fillna("").astype(str).str.strip()]
                if middle:
                    parts.append(df[middle].fillna("").astype(str).str.strip())
                parts.append(df[last].fillna("").astype(str).str.strip())
                new_cols["Investor Name"] = pd.concat(parts, axis=1).apply(
                    lambda r: " ".join(p for p in r if p), axis=1
                ).str.replace(r"\s+", " ", regex=True).str.strip()

        # --- PAN: BSE/NSE uses 'Primary Holder PAN' ---
        has_pan = any(k in cols_lower for k in ("pan", "pannumber", "panno"))
        if not has_pan:
            primary_pan = next((cols_lower[k] for k in (
                "primary holder pan", "primary holder pan no"
            ) if k in cols_lower), None)
            if primary_pan:
                new_cols["PAN"] = df[primary_pan]

        # --- Mobile: BSE/NSE uses 'Indian Mobile No.' ---
        has_mobile = any(k in cols_lower for k in ("mobile", "mobilenumber", "phone", "contactnumber"))
        if not has_mobile:
            indian_mobile = next((cols_lower[k] for k in (
                "indian mobile no.", "indian mobile no", "indianmobileno"
            ) if k in cols_lower), None)
            if indian_mobile:
                new_cols["Mobile"] = df[indian_mobile]

        # --- Bank Name 1 ---
        has_bank = any(k in cols_lower for k in ("bank", "bankname", "bank_name"))
        if not has_bank:
            bank_col = next((cols_lower[k] for k in (
                "bank name 1", "bankname1"
            ) if k in cols_lower), None)
            if bank_col:
                new_cols["Bank Name"] = df[bank_col]

        # --- Account No 1 ---
        has_acct = any(k in cols_lower for k in ("account no", "account_no", "bank_account", "ac_no"))
        if not has_acct:
            acct_col = next((cols_lower[k] for k in (
                "account no 1", "accountno1"
            ) if k in cols_lower), None)
            if acct_col:
                new_cols["Account No"] = df[acct_col]

        # --- IFSC Code 1 ---
        has_ifsc = any(k in cols_lower for k in ("ifsc", "ifsc_code", "ifsccode"))
        if not has_ifsc:
            ifsc_col = next((cols_lower[k] for k in (
                "ifsc code 1", "ifsccode1"
            ) if k in cols_lower), None)
            if ifsc_col:
                new_cols["IFSC"] = df[ifsc_col]

        # --- Address: combine Address 1/2/3, City, State, Pincode ---
        has_addr = any(k in cols_lower for k in ("address", "registered_address", "residence_address"))
        if not has_addr:
            addr_series = []
            for k in ("address 1", "address 2", "address 3", "city", "state", "pincode"):
                if k in cols_lower:
                    addr_series.append(df[cols_lower[k]].fillna("").astype(str).str.strip())
            if addr_series:
                new_cols["Registered Address"] = pd.concat(addr_series, axis=1).apply(
                    lambda r: ", ".join(p for p in r if p and p.lower() != "nan"), axis=1
                ).str.strip(", ")

        # --- Mode of Holding: 'Holding Nature' ---
        has_mode = any(k in cols_lower for k in ("mode", "mode_of_holding", "holding_mode"))
        if not has_mode:
            mode_col = next((cols_lower[k] for k in (
                "holding nature", "holdingnature"
            ) if k in cols_lower), None)
            if mode_col:
                new_cols["Mode of Holding"] = df[mode_col]

        # --- KYC: 'Primary Holder KYC Type' ---
        has_kyc = any(k in cols_lower for k in ("kyc", "kycstatus", "kyc_status"))
        if not has_kyc:
            kyc_col = next((cols_lower[k] for k in (
                "primary holder kyc type", "primaryholderkyctype"
            ) if k in cols_lower), None)
            if kyc_col:
                new_cols["KYC Status"] = df[kyc_col]

        # --- DOB: 'Primary Holder DOB/Incorporation' ---
        has_dob = any(k in cols_lower for k in ("dob", "date_of_birth", "birthdate"))
        if not has_dob:
            dob_col = next((cols_lower[k] for k in (
                "primary holder dob/incorporation", "primary holder dob"
            ) if k in cols_lower), None)
            if dob_col:
                new_cols["Date of Birth"] = df[dob_col]

        # --- Nominee 1 Name ---
        has_nom = any(k in cols_lower for k in ("nominee", "nominee_1", "nominee1", "nominee 1 name"))
        if not has_nom:
            nom_col = next((cols_lower[k] for k in ("nominee 1 name",) if k in cols_lower), None)
            if nom_col:
                new_cols["Nominee"] = df[nom_col]

        # --- Nominee 1 Relationship / Percentage ---
        has_nom_rel = any(k in cols_lower for k in ("nominee_relation", "relation", "nominee_relationship"))
        if not has_nom_rel:
            nom_rel_col = next((cols_lower[k] for k in (
                "nominee 1 relationship",
            ) if k in cols_lower), None)
            nom_pct_col = next((cols_lower[k] for k in (
                "nominee 1 applicable(%)", "nominee 1 applicable (%)", "nominee1applicable"
            ) if k in cols_lower), None)
            if nom_rel_col or nom_pct_col:
                rel_parts = []
                if nom_rel_col:
                    rel_parts.append(df[nom_rel_col].fillna("").astype(str).str.strip())
                if nom_pct_col:
                    rel_parts.append(df[nom_pct_col].fillna("").astype(str).str.strip() + "%")
                if rel_parts:
                    new_cols["Nominee Relation"] = pd.concat(rel_parts, axis=1).apply(
                        lambda r: " / ".join(p for p in r if p and p != "%"), axis=1
                    )

        # Concat all new columns at once to avoid DataFrame fragmentation warnings
        if new_cols:
            df = pd.concat([df, pd.DataFrame(new_cols, index=df.index)], axis=1)

        return df

