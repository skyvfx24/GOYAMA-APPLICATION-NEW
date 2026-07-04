"""Custom exceptions for the Mutual Fund Reconciliation Engine."""

class MFReconException(Exception):
    """Base exception class for all exceptions raised by the reconciliation engine."""
    pass

class ConfigurationError(MFReconException):
    """Raised when configuration variables are invalid, missing, or malformed."""
    pass

class FileAccessError(MFReconException):
    """Raised when file input/output streams are blocked, files do not exist, or access is denied."""
    pass

class ParserError(MFReconException):
    """Base exception for data parsing failures."""
    pass

class SchemaMismatchError(ParserError):
    """Raised when source column layouts do not match expected config specs."""
    pass

class PDFDecryptionError(ParserError):
    """Raised when PDF decryption credentials fail, are wrong, or are omitted."""
    pass

class ReportingError(MFReconException):
    """Raised when discrepancy exports cannot be generated, populated, or saved."""
    pass
