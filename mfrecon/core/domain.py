"""Domain models and enums representing the core entities of the reconciliation library."""

from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, EmailStr, Field


class KYCStatus(StrEnum):
    """Represents the KYC compliance status of an investor."""
    VERIFIED = "VERIFIED"
    PENDING = "PENDING"
    FAILED = "FAILED"
    EXEMPT = "EXEMPT"
    UNKNOWN = "UNKNOWN"


class FATCAStatus(StrEnum):
    """Represents the FATCA compliance status of an investor."""
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    PENDING = "PENDING"
    UNKNOWN = "UNKNOWN"


class InvestorStatus(StrEnum):
    """Represents the operational status of an investor record in the system."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    UNKNOWN = "UNKNOWN"


class DiscrepancyType(StrEnum):
    """Defines the types of discrepancies detected during reconciliation."""
    MISSING_IN_CRM = "MISSING_IN_CRM"
    MISSING_IN_REPORT = "MISSING_IN_REPORT"
    NAME_MISMATCH = "NAME_MISMATCH"
    MOBILE_MISMATCH = "MOBILE_MISMATCH"
    EMAIL_MISMATCH = "EMAIL_MISMATCH"
    KYC_MISMATCH = "KYC_MISMATCH"
    FATCA_MISMATCH = "FATCA_MISMATCH"
    STATUS_MISMATCH = "STATUS_MISMATCH"
    DATE_MISMATCH = "DATE_MISMATCH"
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
    DUPLICATE_RECORD = "DUPLICATE_RECORD"
    PAN_MISMATCH = "PAN_MISMATCH"
    EXACT_DUPLICATE = "EXACT_DUPLICATE"
    CONFLICTING_DUPLICATE = "CONFLICTING_DUPLICATE"
    FUZZY_MATCH_WARNING = "FUZZY_MATCH_WARNING"
    FIELD_MISSING = "FIELD_MISSING"
    FIELD_EMPTY = "FIELD_EMPTY"
    INCOMPLETE_CRM_RECORD = "INCOMPLETE_CRM_RECORD"
    DOB_MISMATCH = "DOB_MISMATCH"
    BANK_MISMATCH = "BANK_MISMATCH"
    BANK_ACCOUNT_MISMATCH = "BANK_ACCOUNT_MISMATCH"
    IFSC_MISMATCH = "IFSC_MISMATCH"
    ADDRESS_MISMATCH = "ADDRESS_MISMATCH"
    MODE_OF_HOLDING_MISMATCH = "MODE_OF_HOLDING_MISMATCH"
    NOMINEE_MISMATCH = "NOMINEE_MISMATCH"
    NOMINEE_RELATION_MISMATCH = "NOMINEE_RELATION_MISMATCH"
    DISTRIBUTOR_ARN_MISMATCH = "DISTRIBUTOR_ARN_MISMATCH"


class RecordSource(StrEnum):
    """Supported data report sources."""
    CRM = "CRM"
    CAMS = "CAMS"
    KFINTECH = "KFINTECH"
    BSE = "BSE"
    NSE = "NSE"
    PDF_CAS = "PDF_CAS"
    INSURANCE = "INSURANCE"


class BaseRecord(BaseModel):
    """Base schema containing standard data fields common to both CRM and report records."""
    pan: str = Field(..., description="10-digit Alphanumeric Permanent Account Number")
    investor_name: str = Field(..., description="Full Name of the Investor")
    mobile: str | None = Field(default=None, description="Normalized 10-digit mobile number")
    email: EmailStr | None = Field(default=None, description="Normalized email address")
    kyc_status: KYCStatus = Field(default=KYCStatus.UNKNOWN, description="KYC compliance status")
    kyc_status_raw: str | None = Field(default=None, description="Original KYC status string from source file, before enum normalization")
    fatca_status: FATCAStatus = Field(default=FATCAStatus.UNKNOWN, description="FATCA status")
    investor_status: InvestorStatus = Field(default=InvestorStatus.UNKNOWN, description="Current operational status")
    last_transaction_date: date | None = Field(default=None, description="Date of the last recorded transaction")
    total_amount: Decimal = Field(default=Decimal("0.00"), description="Aggregated asset/holding balance amount")
    tax_status: str | None = Field(default=None, description="Tax status from source file")
    is_minor_account: bool = Field(default=False, description="Flag indicating if this is a minor's account")
    date_of_birth: str | None = Field(default=None, description="Date of Birth of the investor")
    bank_name: str | None = Field(default=None, description="Bank Name")
    bank_account: str | None = Field(default=None, description="Bank Account Number")
    ifsc: str | None = Field(default=None, description="IFSC Code")
    registered_address: str | None = Field(default=None, description="Registered Address")
    mode_of_holding: str | None = Field(default=None, description="Mode of Holding")
    nominee_1: str | None = Field(default=None, description="Nominee 1 Name")
    nominee_relation: str | None = Field(default=None, description="Nominee Relation / Percentage")
    distributor_arn: str | None = Field(default=None, description="Distributor / ARN Code")


class CRMRecord(BaseRecord):
    """Investor record from the internal CRM database."""
    crm_client_id: str = Field(..., description="Unique client identifier in CRM database")


class ReportRecord(BaseRecord):
    """Parsed investor record from an external transaction or holding report."""
    source: RecordSource = Field(..., description="Report origin source")
    folio_number: str | None = Field(default=None, description="Folio number mapped from the report")
    raw_row_index: int = Field(..., description="Index of the row in the source file for auditability")
    missing_fields: list[str] = Field(default_factory=list, description="Fields whose columns were missing from the raw report")
    empty_fields: list[str] = Field(default_factory=list, description="Fields whose columns existed but values were blank/empty")



class AuditTrace(BaseModel):
    """Execution metadata detailing the path and decisions taken to resolve a match."""
    matching_route: str = Field(..., description="E.g., EXACT_PAN, FUZZY_NAME_AND_MOBILE, UNMATCHED")
    match_confidence: float = Field(1.0, description="Match confidence score (0.0 to 1.0)")
    evaluation_timestamp: str = Field(..., description="Timestamp when matching execution occurred")
    reconciler_version: str = Field(..., description="Version of the reconciler package")
    rule_evaluated: str = Field(..., description="Configuration rule matching applied")
    skipped_comparisons: list[str] = Field(
        default_factory=list,
        description="Fields skipped during comparison due to source profile omissions"
    )


class FileFailure(BaseModel):
    """Details of a file that failed to parse during the reconciliation run."""
    file_name: str = Field(..., description="Original name of the failed file")
    source: str = Field(..., description="The detected or expected source of the file")
    failure_type: str = Field(..., description="Type of failure (e.g., PDF_DECRYPTION_ERROR)")
    message: str = Field(..., description="Detailed failure message")


class MatchedAudit(BaseModel):
    """Audit trace details for successfully matched records."""
    pan: str = Field(..., description="PAN associated with the record")
    route: str = Field(..., description="Route used for matching")
    confidence: float = Field(..., description="Match confidence score (0.0 to 1.0)")
    source: str = Field(..., description="Data report source of the matched record")
    timestamp: str = Field(..., description="Timestamp when matching execution occurred")
    skipped_comparisons: list[str] = Field(
        default_factory=list,
        description="Fields skipped during comparison due to source profile omissions"
    )


class Discrepancy(BaseModel):
    """Represents a single mismatch identified between a CRM record and a report record."""
    discrepancy_type: DiscrepancyType = Field(..., description="The type classification of this discrepancy")
    pan: str = Field(..., description="PAN associated with the record")
    field_name: str | None = Field(default=None, description="Specific field name showing a mismatch, if applicable")
    crm_value: str | None = Field(default=None, description="Value recorded in CRM database")
    report_value: str | None = Field(default=None, description="Value recorded in the report file")
    severity: str = Field(default="HIGH", description="CRITICAL, HIGH, MEDIUM, or LOW severity classification")
    explanation: str = Field(..., description="Plain English description of why the mismatch occurred")
    source_info: dict[str, str] = Field(
        default_factory=dict,
        description="Metadata linking to the source record (e.g. line numbers, source file names)"
    )
    audit_trace: AuditTrace = Field(..., description="Traceability details for matching decision paths")


class ReconciliationRunMetadata(BaseModel):
    """Run-level audit and monitoring metrics for a single reconciliation execution."""
    run_id: str = Field(..., description="Unique UUID for the execution run")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp of execution")
    crm_file_hash: str = Field(..., description="SHA-256 fingerprint of the CRM master file")
    report_file_hashes: dict[str, str] = Field(
        ...,
        description="Mapping of report file names to their SHA-256 fingerprints"
    )
    total_crm_records: int = Field(..., description="Count of CRM records parsed")
    total_report_records: int = Field(..., description="Count of report records parsed")
    validation_failures_count: int = Field(..., description="Count of rows failed on validation and isolated")
    discrepancies_count: int = Field(..., description="Total count of discrepancies generated")
    failed_files: list[FileFailure] = Field(
        default_factory=list,
        description="List of report files that failed parsing/decryption"
    )


class ReconciliationResult(BaseModel):
    """Reconciliation run response output containing metadata, list of discrepancies, and output paths."""
    metadata: ReconciliationRunMetadata = Field(..., description="Session metadata information")
    discrepancies: list[Discrepancy] = Field(..., description="List of generated discrepancies")
    excel_report_path: str | None = Field(default=None, description="Absolute path to Excel discrepancy report")
    csv_report_path: str | None = Field(default=None, description="Absolute path to flat CSV discrepancy report")
    json_report_path: str | None = Field(default=None, description="Absolute path to JSON discrepancy report")
    matched_audits: list[MatchedAudit] = Field(
        default_factory=list,
        description="List of audit traces for successfully matched records"
    )

