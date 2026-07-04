"""Normalization Pipeline for coordinating standardizations on domain models."""

from mfrecon.core.domain import CRMRecord, ReportRecord
from mfrecon.normalizers.contact import normalize_email, normalize_mobile
from mfrecon.normalizers.date_amount import normalize_amount, normalize_date
from mfrecon.normalizers.identity import normalize_name, normalize_pan
from mfrecon.normalizers.status import (
    normalize_fatca_status,
    normalize_investor_status,
    normalize_kyc_status,
)


class NormalizationPipeline:
    """
    Coordinates execution of field-level normalization rules for CRMRecord
    and ReportRecord instances.
    """

    def normalize_crm_record(self, record: CRMRecord) -> CRMRecord:
        """
        Creates and returns a new normalized CRMRecord.
        The original CRMRecord remains unmodified.

        Args:
            record: Raw CRMRecord.

        Returns:
            CRMRecord: Normalized CRMRecord.
        """
        normalized_data = {
            "crm_client_id": record.crm_client_id,
            "pan": normalize_pan(record.pan),
            "investor_name": normalize_name(record.investor_name),
            "mobile": normalize_mobile(record.mobile) if record.mobile is not None else None,
            "email": normalize_email(record.email) if record.email is not None else None,
            "kyc_status": normalize_kyc_status(record.kyc_status),
            "fatca_status": normalize_fatca_status(record.fatca_status),
            "investor_status": normalize_investor_status(record.investor_status),
            "last_transaction_date": (
                normalize_date(record.last_transaction_date)
                if record.last_transaction_date is not None
                else None
            ),
            "total_amount": normalize_amount(record.total_amount),
        }
        return CRMRecord.model_validate(normalized_data)

    def normalize_report_record(self, record: ReportRecord) -> ReportRecord:
        """
        Creates and returns a new normalized ReportRecord.
        The original ReportRecord remains unmodified.

        Args:
            record: Raw ReportRecord.

        Returns:
            ReportRecord: Normalized ReportRecord.
        """
        normalized_data = {
            "source": record.source,
            "folio_number": record.folio_number,
            "raw_row_index": record.raw_row_index,
            "pan": normalize_pan(record.pan),
            "investor_name": normalize_name(record.investor_name),
            "mobile": normalize_mobile(record.mobile) if record.mobile is not None else None,
            "email": normalize_email(record.email) if record.email is not None else None,
            "kyc_status": normalize_kyc_status(record.kyc_status),
            "fatca_status": normalize_fatca_status(record.fatca_status),
            "investor_status": normalize_investor_status(record.investor_status),
            "last_transaction_date": (
                normalize_date(record.last_transaction_date)
                if record.last_transaction_date is not None
                else None
            ),
            "total_amount": normalize_amount(record.total_amount),
        }
        return ReportRecord.model_validate(normalized_data)
