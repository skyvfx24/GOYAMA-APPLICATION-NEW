import time
from decimal import Decimal

from mfrecon.core.config import EngineConfig
from mfrecon.core.domain import CRMRecord, RecordSource, ReportRecord
from mfrecon.engine.explainability import format_explanation
from mfrecon.engine.reconciler import ReconciliationEngine


def test_explainability_explanations():
    exp = format_explanation("AMOUNT_MISMATCH", "total_amount", 100.50, 95.00)
    assert "Amount mismatch detected. CRM value 100.50 differs from Report value 95.00." in exp

    exp2 = format_explanation("FUZZY_MATCH_WARNING", None, None, None, {"confidence": 0.92, "matching_route": "FUZZY_NAME_AND_MOBILE"})
    assert "Fuzzy match warning: Record aligned via name similarity of 92.0% using route 'FUZZY_NAME_AND_MOBILE'." in exp2


def test_reconciler_performance_large_dataset():
    # Construct 1000 CRM and 1000 Report records to verify sub-second indexed search capability
    crm_recs = []
    report_recs = []

    for i in range(1000):
        pan = f"ABCDE{i:04d}F"
        crm_recs.append(CRMRecord(
            crm_client_id=f"CRM{i}",
            pan=pan,
            investor_name=f"RAMESH SHARMA {i}",
            mobile=f"987654{i:04d}",
            email=f"ramesh_{i}@gmail.com",
            total_amount=Decimal("100.00")
        ))

        # Reports match exactly
        report_recs.append(ReportRecord(
            source=RecordSource.CAMS,
            folio_number=f"F{i}",
            raw_row_index=i,
            pan=pan,
            investor_name=f"RAMESH SHARMA {i}",
            mobile=f"987654{i:04d}",
            email=f"ramesh_{i}@gmail.com",
            total_amount=Decimal("100.00")
        ))

    engine = ReconciliationEngine()
    config = EngineConfig()

    start = time.perf_counter()
    res = engine.reconcile(crm_recs, report_recs, config)
    elapsed = time.perf_counter() - start

    assert res.statistics.matched_count == 1000
    assert res.statistics.unmatched_count == 0
    # Performance check: executing 2000 total records alignments must be extremely fast due to index lookups
    assert elapsed < 0.5
