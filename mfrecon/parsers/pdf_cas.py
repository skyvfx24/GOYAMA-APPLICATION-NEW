"""Parser implementation for PDF CAS/SOA statements using pdfplumber."""

import re
from decimal import Decimal
from pathlib import Path
from typing import Any

import pdfplumber
from loguru import logger
from pydantic import ValidationError

from mfrecon.core.domain import FATCAStatus, InvestorStatus, KYCStatus, RecordSource, ReportRecord
from mfrecon.core.exceptions import ParserError, PDFDecryptionError
from mfrecon.parsers.base import BaseParser
from mfrecon.parsers.report_result import ReportParseMetadata, ReportParseResult
from mfrecon.utils.hash import calculate_sha256


class PDFCASParser(BaseParser):
    """Parser class for reading and validating multi-page PDF CAS files."""

    def __init__(self) -> None:
        self.source = RecordSource.PDF_CAS

    def parse(self, file_path: Path) -> list[ReportRecord]:
        """Parses PDF CAS file and returns a list of successfully validated ReportRecord objects."""
        result = self.parse_report(file_path)
        return result.records

    def parse_report(self, file_path: Path, password: str | None = None) -> ReportParseResult:
        """
        Parses a PDF statement (Common Account Statement) using pdfplumber.

        Args:
            file_path: Path to the target PDF file.
            password: Password string for encrypted files.

        Returns:
            ReportParseResult: Ingestion results container.

        Raises:
            FileAccessError: If the file is missing or unreadable.
            PDFDecryptionError: If the PDF is encrypted and the password fails or is missing.
            ParserError: If the PDF structure is corrupted.
        """
        self.check_file_exists(file_path)

        if file_path.stat().st_size == 0:
            logger.error(f"PDF CAS parser failed: file {file_path.name} is empty.")
            raise ParserError(f"PDF CAS file is empty: {file_path.name}")

        file_hash = calculate_sha256(file_path)
        total_text = ""

        # Open and decrypt PDF using pdfplumber
        try:
            with pdfplumber.open(file_path, password=password) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        total_text += text + "\n"
        except Exception as e:
            err_msg = str(e).lower()
            # Catch standard encryption / password exceptions
            if "password" in err_msg or "decrypt" in err_msg or "incorrect" in err_msg or "authenticate" in err_msg:
                logger.error(f"PDF decryption failed for: {file_path.name}. Reason: {e}")
                raise PDFDecryptionError(f"PDF statement decryption failed: {file_path.name}") from e
            logger.error(f"PDF structure read failed: {e}")
            raise ParserError(f"Failed to read PDF structure: {file_path.name}") from e

        # Extract records from accumulated text
        records: list[ReportRecord] = []
        validation_failures: list[dict[str, Any]] = []

        raw_blocks = self._extract_raw_blocks(total_text)
        total_rows = len(raw_blocks)

        for idx, block in enumerate(raw_blocks):
            row_number = idx + 1
            raw_data = block.copy()

            # Keep only allowed fields for PDF_CAS (pan, investor_name, mobile, total_amount)
            # Available: pan, investor_name, mobile, total_amount
            domain_data: dict[str, Any] = {
                "pan": block.get("pan"),
                "investor_name": block.get("investor_name"),
                "mobile": block.get("mobile"),
                "email": block.get("email"),
                "total_amount": block.get("total_amount", Decimal("0.00")),
                "source": self.source,
                "raw_row_index": row_number,
                "kyc_status": KYCStatus.UNKNOWN,
                "fatca_status": FATCAStatus.UNKNOWN,
                "investor_status": InvestorStatus.UNKNOWN,
                "folio_number": block.get("folio_number"),
                "tax_status": block.get("tax_status"),
                "date_of_birth": block.get("date_of_birth"),
                "bank_name": block.get("bank_name"),
                "bank_account": block.get("bank_account"),
                "ifsc": block.get("ifsc"),
                "registered_address": block.get("registered_address"),
                "mode_of_holding": block.get("mode_of_holding"),
                "nominee_1": block.get("nominee_1"),
                "nominee_relation": block.get("nominee_relation"),
                "distributor_arn": block.get("distributor_arn")
            }

            # Extract missing/empty fields
            missing, empty = self.extract_missing_and_empty_fields(block, header_mapping=None)
            domain_data["missing_fields"] = missing
            domain_data["empty_fields"] = empty

            # Minor account awareness
            tax_status_val, is_minor = self.check_minor_account(block, header_mapping=None)
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

            # Required: pan, investor_name
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
            f"PDF CAS Ingestion Complete: {file_path.name}. Total: {total_rows}, "
            f"Parsed: {len(records)}, Failed: {len(validation_failures)}"
        )

        return ReportParseResult(
            records=records,
            validation_failures=validation_failures,
            metadata=metadata
        )

    def _extract_raw_blocks(self, text: str) -> list[dict[str, Any]]:
        """Parses CAS text line-by-line using block detection logic."""
        blocks: list[dict[str, Any]] = []
        current: dict[str, Any] = {}

        def commit_current() -> None:
            if current:
                # Only save if we have at least one key populated
                blocks.append(current.copy())
                current.clear()

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            # 1. Match PAN
            # Match standard PAN patterns
            pan_match = re.search(r"PAN\s*:\s*([A-Z0-9]{10})", line, re.IGNORECASE)
            if not pan_match:
                # Try generic PAN regex
                pan_match = re.search(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", line)

            if pan_match:
                pan_val = pan_match.group(1) if len(pan_match.groups()) > 0 else pan_match.group(0)
                pan_val = pan_val.strip().upper()
                if "pan" in current:
                    commit_current()
                current["pan"] = pan_val

            # 2. Match Name
            name_match = re.search(r"(?:Name|Investor Name)\s*:\s*([A-Za-z\s.]+)", line, re.IGNORECASE)
            if name_match:
                name_val = name_match.group(1).strip()
                if "investor_name" in current:
                    commit_current()
                current["investor_name"] = name_val

            # 3. Match Mobile
            mobile_match = re.search(r"(?:Mobile|Phone|Contact)\s*:\s*([0-9\+\-\s]+)", line, re.IGNORECASE)
            if mobile_match:
                mobile_val = re.sub(r"\D", "", mobile_match.group(1))
                if len(mobile_val) > 10 and mobile_val.startswith("91"):
                    mobile_val = mobile_val[2:]
                if "mobile" in current:
                    commit_current()
                current["mobile"] = mobile_val

            # 4. Match Amount
            amount_match = re.search(r"(?:Amount|Balance|Value)\s*:\s*([0-9,]+\.?[0-9]*)", line, re.IGNORECASE)
            if amount_match:
                amt_str = amount_match.group(1).replace(",", "").strip()
                try:
                    amt_val = Decimal(amt_str)
                    if "total_amount" in current:
                        commit_current()
                    current["total_amount"] = amt_val
                except (ValueError, ArithmeticError):
                    pass

            # 5. Match Folio
            folio_match = re.search(r"(?:Folio|Folio Number|Folio No)\s*:\s*([A-Za-z0-9\/]+)", line, re.IGNORECASE)
            if folio_match:
                folio_val = folio_match.group(1).strip()
                if "folio_number" in current:
                    commit_current()
                current["folio_number"] = folio_val

            # 6. Match Email
            email_match = re.search(r"(?:Email|Email Address)\s*:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", line, re.IGNORECASE)
            if email_match:
                email_val = email_match.group(1).strip()
                if "email" in current:
                    commit_current()
                current["email"] = email_val

            # 7. Match Tax Status
            tax_match = re.search(r"(?:Tax Status|Taxability|Tax Category)\s*:\s*([A-Za-z\s./-]+)", line, re.IGNORECASE)
            if tax_match:
                tax_val = tax_match.group(1).strip()
                if "tax_status" in current:
                    commit_current()
                current["tax_status"] = tax_val

            # 8. Match Date of Birth
            dob_match = re.search(r"(?:Date of Birth|DOB|Birth Date|Birthdate)\s*:\s*([0-9A-Za-z\s./-]+)", line, re.IGNORECASE)
            if dob_match:
                dob_val = dob_match.group(1).strip()
                if "date_of_birth" in current:
                    commit_current()
                current["date_of_birth"] = dob_val

            # 9. Match Bank Name
            bank_match = re.search(r"(?:Bank Name|Bank)\s*:\s*([A-Za-z\s./-]+)", line, re.IGNORECASE)
            if bank_match:
                bank_val = bank_match.group(1).strip()
                if "bank_name" in current:
                    commit_current()
                current["bank_name"] = bank_val

            # 10. Match Bank Account
            acct_match = re.search(r"(?:Bank Account|Account No|Account Number|A/c)\s*:\s*([0-9]+)", line, re.IGNORECASE)
            if acct_match:
                acct_val = acct_match.group(1).strip()
                if "bank_account" in current:
                    commit_current()
                current["bank_account"] = acct_val

            # 11. Match IFSC
            ifsc_match = re.search(r"(?:IFSC|IFSC Code)\s*:\s*([A-Z0-9]{11})", line, re.IGNORECASE)
            if ifsc_match:
                ifsc_val = ifsc_match.group(1).strip()
                if "ifsc" in current:
                    commit_current()
                current["ifsc"] = ifsc_val

            # 12. Match Registered Address
            addr_match = re.search(r"(?:Address|Registered Address)\s*:\s*([A-Za-z0-9\s.,/-]+)", line, re.IGNORECASE)
            if addr_match:
                addr_val = addr_match.group(1).strip()
                if "registered_address" in current:
                    commit_current()
                current["registered_address"] = addr_val

            # 13. Match Mode of Holding
            mode_match = re.search(r"(?:Mode of Holding|Holding Mode|Mode)\s*:\s*([A-Za-z\s./-]+)", line, re.IGNORECASE)
            if mode_match:
                mode_val = mode_match.group(1).strip()
                if "mode_of_holding" in current:
                    commit_current()
                current["mode_of_holding"] = mode_val

            # 14. Match Nominee 1
            nom_match = re.search(r"(?:Nominee 1|Nominee Name|Nominee)\s*:\s*([A-Za-z\s./-]+)", line, re.IGNORECASE)
            if nom_match:
                nom_val = nom_match.group(1).strip()
                if "nominee_1" in current:
                    commit_current()
                current["nominee_1"] = nom_val

            # 15. Match Nominee Relation
            rel_match = re.search(r"(?:Nominee Relation|Relation|Relation/Percentage)\s*:\s*([A-Za-z\s./%0-9-]+)", line, re.IGNORECASE)
            if rel_match:
                rel_val = rel_match.group(1).strip()
                if "nominee_relation" in current:
                    commit_current()
                current["nominee_relation"] = rel_val

            # 16. Match Distributor (ARN)
            arn_match = re.search(r"(?:Distributor|ARN|Broker Code|Distributor \(ARN\))\s*:\s*([A-Za-z0-9\s./%-]+)", line, re.IGNORECASE)
            if arn_match:
                arn_val = arn_match.group(1).strip()
                if "distributor_arn" in current:
                    commit_current()
                current["distributor_arn"] = arn_val


        # Commit final remaining block
        commit_current()
        return blocks
