"""Core interfaces and abstract protocols for the reconciliation engine."""

from abc import ABC, abstractmethod
from pathlib import Path

from mfrecon.core.domain import ReconciliationResult, ReportRecord


class ParserInterface(ABC):
    """
    Abstract Base Class defining the protocol for file parsers.

    All source parsers (CRM, CAMS, KFintech, PDF CAS, BSE, NSE) must inherit
    from this class and implement the parse method.
    """

    @abstractmethod
    def parse(self, file_path: Path) -> list[ReportRecord]:
        """
        Parses a target file path and extracts a list of structured ReportRecord objects.

        Args:
            file_path: The absolute Path to the input file.

        Returns:
            List[ReportRecord]: List of parsed domain records.

        Raises:
            FileAccessError: If the file cannot be accessed.
            ParserError: If parsing fails or standard layout cannot be extracted.
        """
        pass


class ReporterInterface(ABC):
    """
    Abstract Base Class defining the protocol for report exporters.

    All format reporters (Excel, CSV, JSON) must inherit from this class and
    implement the generate method.
    """

    @abstractmethod
    def generate(self, result: ReconciliationResult, output_path: Path) -> bool:
        """
        Generates and saves the discrepancy and summary reports.

        Args:
            result: The complete ReconciliationResult payload.
            output_path: Target output path where the file should be generated.

        Returns:
            bool: True if writing succeeded, False otherwise.

        Raises:
            ReportingError: If reports cannot be written or formatted.
        """
        pass
