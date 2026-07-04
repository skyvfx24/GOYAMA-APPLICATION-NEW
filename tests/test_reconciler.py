from decimal import Decimal

from mfrecon.core.config import EngineConfig
from mfrecon.core.domain import CRMRecord, DiscrepancyType, RecordSource, ReportRecord
from mfrecon.engine.reconciler import ReconciliationEngine


def test_reconciler_execution():
    reconciler = ReconciliationEngine()

    crm_records = [
        # Match 1 (exact)
        CRMRecord(
            crm_client_id="C1",
            pan="ABCDE1234F",
            investor_name="RAMESH SHARMA",
            total_amount=Decimal("100.00")
        ),
        # Match 2 (missing in report)
        CRMRecord(
            crm_client_id="C2",
            pan="VWXYZ9876A",
            investor_name="SURESH KUMAR",
            total_amount=Decimal("200.00")
        )
    ]

    report_records = [
        # Match 1 (exact)
        ReportRecord(
            source=RecordSource.CAMS,
            folio_number="F123",
            raw_row_index=1,
            pan="ABCDE1234F",
            investor_name="RAMESH SHARMA",
            total_amount=Decimal("100.00")
        ),
        # Match 3 (missing in CRM)
        ReportRecord(
            source=RecordSource.CAMS,
            folio_number="F456",
            raw_row_index=2,
            pan="KLMNO4321B",
            investor_name="AMIT SHARMA",
            total_amount=Decimal("300.00")
        )
    ]

    config = EngineConfig()
    config.reporting.severity_mappings = {
        "MISSING_IN_CRM": "CRITICAL",
        "MISSING_IN_REPORT": "HIGH"
    }

    result = reconciler.reconcile(crm_records, report_records, config)

    # Statistics checks
    assert result.statistics.total_records == 4
    assert result.statistics.matched_count == 1
    assert result.statistics.unmatched_count == 2
    assert result.statistics.discrepancy_count == 2

    # Discrepancies check
    disc_types = [d.discrepancy_type for d in result.discrepancies]
    assert DiscrepancyType.MISSING_IN_CRM in disc_types
    assert DiscrepancyType.MISSING_IN_REPORT in disc_types
