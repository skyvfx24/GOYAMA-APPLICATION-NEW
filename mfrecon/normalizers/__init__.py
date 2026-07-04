"""Normalizers module initialization. Exposes individual normalizers and the pipeline."""

from mfrecon.normalizers.contact import normalize_email, normalize_mobile
from mfrecon.normalizers.date_amount import normalize_amount, normalize_date
from mfrecon.normalizers.identity import normalize_name, normalize_pan
from mfrecon.normalizers.pipeline import NormalizationPipeline
from mfrecon.normalizers.status import (
    normalize_fatca_status,
    normalize_investor_status,
    normalize_kyc_status,
)

__all__ = [
    "normalize_name",
    "normalize_pan",
    "normalize_email",
    "normalize_mobile",
    "normalize_kyc_status",
    "normalize_fatca_status",
    "normalize_investor_status",
    "normalize_date",
    "normalize_amount",
    "NormalizationPipeline",
]
