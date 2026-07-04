"""Registry manager for dynamically routing, registering, and auto-detecting report parsers."""

from pathlib import Path

import pandas as pd
from loguru import logger

from mfrecon.core.exceptions import ParserError
from mfrecon.parsers.base import BaseParser


class ParserRegistry:
    """Manages parser registrations, instantiations, and auto-detection schemas."""

    def __init__(self) -> None:
        self._parsers: dict[str, type[BaseParser]] = {}

    def register(self, source_name: str, parser_class: type[BaseParser]) -> None:
        """
        Registers a parser class under a source identifier name.

        Args:
            source_name: Standard source name (e.g. CAMS, KFINTECH, BSE, NSE, PDF_CAS).
            parser_class: Subclass of BaseParser implementing the parser logic.
        """
        normalized_name = source_name.upper().strip()
        self._parsers[normalized_name] = parser_class
        logger.info(f"Registered parser class '{parser_class.__name__}' for source: {normalized_name}")

    def get(self, source_name: str) -> BaseParser:
        """
        Retrieves an instance of the parser registered for the source.

        Args:
            source_name: Standard source name identifier.

        Returns:
            BaseParser: An instance of the matching parser class.

        Raises:
            ParserError: If no parser class has been registered for the source.
        """
        normalized_name = source_name.upper().strip()
        if normalized_name not in self._parsers:
            logger.error(f"No parser registered for source: {normalized_name}")
            raise ParserError(f"No parser registered for source: {normalized_name}")
        return self._parsers[normalized_name]()

    def detect_parser(self, file_path: Path) -> BaseParser:
        """
        Auto-detects the matching parser by analyzing file extension, sheet names, or headers.

        Args:
            file_path: Path to the target report file.

        Returns:
            BaseParser: An instance of the auto-detected parser class.

        Raises:
            ParserError: If the file type is unsupported or cannot be matched to any registered parser.
        """
        if not file_path.exists():
            raise ParserError(f"File not found for auto-detection: {file_path}")

        suffix = file_path.suffix.lower()

        # 1. Route PDFs directly to PDF_CAS
        if suffix == ".pdf":
            logger.info(f"Auto-detected PDF CAS Parser for file: {file_path.name}")
            return self.get("PDF_CAS")

        # 2. Ingest headers or sheet names for spreadsheets/CSVs
        try:
            if suffix == ".csv":
                # Read just the header row
                df_headers = pd.read_csv(file_path, nrows=0)
                columns = [str(c).lower() for c in df_headers.columns]
                return self._detect_from_headers(columns, file_path.name)

            if suffix in (".xlsx", ".xls"):
                excel_file = pd.ExcelFile(file_path)
                # Check sheet names first
                for sheet in excel_file.sheet_names:
                    normalized_sheet = sheet.lower()
                    if "insurance" in normalized_sheet or "policy" in normalized_sheet:
                        return self.get("INSURANCE")
                    if "cams" in normalized_sheet:
                        return self.get("CAMS")
                    if "kfin" in normalized_sheet or "karvy" in normalized_sheet:
                        return self.get("KFINTECH")
                    if "bse" in normalized_sheet:
                        return self.get("BSE")
                    if "nse" in normalized_sheet:
                        return self.get("NSE")

                # Fallback: read headers from the first sheet
                df_headers = excel_file.parse(sheet_name=excel_file.sheet_names[0], nrows=0)
                columns = [str(c).lower() for c in df_headers.columns]
                return self._detect_from_headers(columns, file_path.name)

            raise ParserError(f"Unsupported extension for auto-detection: {suffix}")

        except Exception as e:
            if isinstance(e, ParserError):
                raise
            logger.error(f"Auto-detection check failed: {e}")
            raise ParserError(f"Parser auto-detection failed for file {file_path.name}: {e}") from e

    def _detect_from_headers(self, columns: list[str], filename: str) -> BaseParser:
        """Evaluates column name signatures to identify source."""
        # Convert header lists to a single search block
        headers_str = " ".join(columns).lower()
        filename_lower = filename.lower()

        # 1. Check filename / headers for explicit source names first (highest priority)
        if "insurance" in headers_str or "insurance" in filename_lower or "policy" in headers_str or "policy" in filename_lower:
            return self.get("INSURANCE")
        if "kfin" in headers_str or "karvy" in headers_str or "kfintech" in filename_lower or "mfsd211" in filename_lower:
            return self.get("KFINTECH")
        if "bse" in headers_str or "bse" in filename_lower:
            return self.get("BSE")
        if "nse" in headers_str or "nse" in filename_lower:
            return self.get("NSE")
        if "cams" in headers_str or "cams" in filename_lower:
            return self.get("CAMS")

        # 2. Fallbacks based on signature columns
        if "folio" in headers_str:
            # By default, treat generic folio files as CAMS
            return self.get("CAMS")

        logger.error(f"Could not auto-detect source from headers: {columns}")
        raise ParserError(f"Could not auto-detect report source for file: {filename}")
