# Parser package module loader.

from mfrecon.parsers.base import BaseParser
from mfrecon.parsers.bse import BSEParser
from mfrecon.parsers.cams import CAMSParser
from mfrecon.parsers.kfintech import KFintechParser
from mfrecon.parsers.nse import NSEParser
from mfrecon.parsers.pdf_cas import PDFCASParser
from mfrecon.parsers.insurance import InsuranceParser
from mfrecon.parsers.registry import ParserRegistry
from mfrecon.parsers.report_result import ReportParseMetadata, ReportParseResult

# Default pre-registered parser registry instance
default_registry = ParserRegistry()
default_registry.register("CAMS", CAMSParser)
default_registry.register("KFINTECH", KFintechParser)
default_registry.register("BSE", BSEParser)
default_registry.register("NSE", NSEParser)
default_registry.register("PDF_CAS", PDFCASParser)
default_registry.register("INSURANCE", InsuranceParser)

__all__ = [
    "BaseParser",
    "CAMSParser",
    "KFintechParser",
    "BSEParser",
    "NSEParser",
    "PDFCASParser",
    "InsuranceParser",
    "ParserRegistry",
    "ReportParseResult",
    "ReportParseMetadata",
    "default_registry"
]
