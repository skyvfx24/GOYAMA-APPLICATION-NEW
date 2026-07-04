from decimal import Decimal

from mfrecon.core.domain import CRMRecord, RecordSource, ReportRecord
from mfrecon.validators.duplicate import DuplicateDetector


def test_duplicate_detector_no_duplicates():
    detector = DuplicateDetector()

    records = [
        CRMRecord(
            crm_client_id="C1",
            pan="ABCDE1234F",
            investor_name="Ramesh Sharma",
            mobile="9876543210",
            email="ramesh@gmail.com",
            total_amount=Decimal("100.00")
        ),
        CRMRecord(
            crm_client_id="C2",
            pan="VWXYZ9876A",
            investor_name="Suresh Kumar",
            mobile="9876543211",
            email="suresh@gmail.com",
            total_amount=Decimal("200.00")
        )
    ]

    valid, invalid, failures = detector.process(records)
    assert len(valid) == 2
    assert len(invalid) == 0
    assert len(failures) == 0


def test_duplicate_detector_exact_duplicates_crm():
    detector = DuplicateDetector()

    rec1 = CRMRecord(
        crm_client_id="C1",
        pan="ABCDE1234F",
        investor_name="Ramesh Sharma",
        mobile="9876543210",
        email="ramesh@gmail.com",
        total_amount=Decimal("100.00")
    )
    # Exact duplicate CRM records (same PAN, same CRM client ID)
    rec2 = CRMRecord(
        crm_client_id="C1",
        pan="ABCDE1234F",
        investor_name="Ramesh Sharma",
        mobile="9876543210",
        email="ramesh@gmail.com",
        total_amount=Decimal("100.00")
    )

    valid, invalid, failures = detector.process([rec1, rec2])
    assert len(valid) == 1
    assert len(invalid) == 1
    assert valid[0].crm_client_id == "C1"
    assert invalid[0].crm_client_id == "C1"
    assert len(failures) == 1
    assert failures[0]["failure_type"] == "EXACT_DUPLICATE"
    assert failures[0]["field_name"] == "pan"


def test_duplicate_detector_conflicting_duplicates_crm():
    detector = DuplicateDetector()

    rec1 = CRMRecord(
        crm_client_id="C1",
        pan="ABCDE1234F",
        investor_name="Ramesh Sharma",
        mobile="9876543210",
        email="ramesh@gmail.com",
        total_amount=Decimal("100.00")
    )
    # Conflicting duplicate: different name and email, same client ID
    rec2 = CRMRecord(
        crm_client_id="C1",
        pan="ABCDE1234F",
        investor_name="Ramesh Kumar Sharma",
        mobile="9876543210",
        email="ramesh.k@gmail.com",
        total_amount=Decimal("100.00")
    )

    valid, invalid, failures = detector.process([rec1, rec2])
    assert len(valid) == 1
    assert len(invalid) == 1
    assert len(failures) == 1
    assert failures[0]["failure_type"] == "CONFLICTING_DUPLICATE"
    assert "investor_name" in failures[0]["message"]
    assert "email" in failures[0]["message"]



def test_duplicate_detector_with_folios_report_records():
    detector = DuplicateDetector()

    rec1 = ReportRecord(
        source=RecordSource.CAMS,
        folio_number="F123",
        raw_row_index=1,
        pan="ABCDE1234F",
        investor_name="Ramesh Sharma",
        mobile="9876543210",
        email="ramesh@gmail.com",
        total_amount=Decimal("100.00")
    )
    # Duplicate with same PAN and same Folio
    rec2 = ReportRecord(
        source=RecordSource.CAMS,
        folio_number="F123",
        raw_row_index=2,
        pan="ABCDE1234F",
        investor_name="Ramesh Sharma",
        mobile="9876543210",
        email="ramesh@gmail.com",
        total_amount=Decimal("100.00")
    )
    # Same PAN but DIFFERENT Folio (this is NOT a duplicate because PAN + Folio differs!)
    rec3 = ReportRecord(
        source=RecordSource.CAMS,
        folio_number="F999",
        raw_row_index=3,
        pan="ABCDE1234F",
        investor_name="Ramesh Sharma",
        mobile="9876543210",
        email="ramesh@gmail.com",
        total_amount=Decimal("100.00")
    )

    valid, invalid, failures = detector.process([rec1, rec2, rec3])
    assert len(valid) == 2  # rec1 and rec3 are distinct keys
    assert len(invalid) == 1  # rec2 is duplicate of rec1
    assert len(failures) == 1
    assert failures[0]["row_number"] == 2
    assert failures[0]["failure_type"] == "EXACT_DUPLICATE"
