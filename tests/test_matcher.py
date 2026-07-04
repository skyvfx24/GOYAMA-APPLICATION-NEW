from mfrecon.core.domain import CRMRecord, RecordSource, ReportRecord
from mfrecon.engine.matcher import RecordMatcher


def test_matcher_exact_pan_match():
    crm_recs = [
        CRMRecord(
            crm_client_id="C1",
            pan="ABCDE1234F",
            investor_name="Ramesh Sharma",
            mobile="9876543210",
            email="ramesh@gmail.com"
        )
    ]
    matcher = RecordMatcher(crm_recs)

    report = ReportRecord(
        source=RecordSource.CAMS,
        folio_number="F123",
        raw_row_index=1,
        pan="ABCDE1234F",
        investor_name="Ramesh Sharma",
        mobile="9876543210",
        email="ramesh@gmail.com"
    )

    res = matcher.find_match(report)
    assert res.match_type == "EXACT"
    assert res.matching_route == "EXACT_PAN"
    assert res.crm_record is not None
    assert res.crm_record.crm_client_id == "C1"


def test_matcher_unmatched():
    crm_recs = [
        CRMRecord(
            crm_client_id="C1",
            pan="ABCDE1234F",
            investor_name="Ramesh Sharma",
            mobile="9876543210",
            email="ramesh@gmail.com"
        )
    ]
    matcher = RecordMatcher(crm_recs)

    report = ReportRecord(
        source=RecordSource.CAMS,
        folio_number="F123",
        raw_row_index=1,
        pan="VWXYZ9876A",  # Different PAN
        investor_name="Suresh Kumar",
        mobile="9876543211",
        email="suresh@gmail.com"
    )

    res = matcher.find_match(report, enable_fuzzy=False)
    assert res.match_type == "UNMATCHED"
    assert res.crm_record is None


def test_matcher_fuzzy_match_by_mobile():
    crm_recs = [
        CRMRecord(
            crm_client_id="C1",
            pan="ABCDE1234F",
            investor_name="Ramesh Sharma",
            mobile="9876543210",
            email="ramesh@gmail.com"
        )
    ]
    matcher = RecordMatcher(crm_recs)

    # Different PAN, but Name matches threshold and Mobile matches exactly
    report = ReportRecord(
        source=RecordSource.CAMS,
        folio_number="F123",
        raw_row_index=1,
        pan="VWXYZ9876A",
        investor_name="Ramesh S. Sharma",  # Fuzzy Name (Levenshtein score is high)
        mobile="9876543210",  # Exact Mobile
        email="different@gmail.com"
    )

    res = matcher.find_match(report, enable_fuzzy=True, threshold=0.85)
    assert res.match_type == "FUZZY_MATCH_WARNING"
    assert res.matching_route == "FUZZY_NAME_AND_MOBILE"
    assert res.crm_record is not None
    assert res.crm_record.crm_client_id == "C1"
    assert res.confidence >= 0.85


def test_matcher_fuzzy_match_by_email():
    crm_recs = [
        CRMRecord(
            crm_client_id="C1",
            pan="ABCDE1234F",
            investor_name="Ramesh Sharma",
            mobile="9876543210",
            email="ramesh@gmail.com"
        )
    ]
    matcher = RecordMatcher(crm_recs)

    # Different PAN, Name matches threshold, Email matches exactly
    report = ReportRecord(
        source=RecordSource.CAMS,
        folio_number="F123",
        raw_row_index=1,
        pan="VWXYZ9876A",
        investor_name="Ramesh Kumar Sharma",
        mobile="different",
        email="ramesh@gmail.com"
    )

    res = matcher.find_match(report, enable_fuzzy=True, threshold=0.80)
    assert res.match_type == "FUZZY_MATCH_WARNING"
    assert res.matching_route == "FUZZY_NAME_AND_EMAIL"
    assert res.crm_record is not None


def test_matcher_fuzzy_match_disabled():
    crm_recs = [
        CRMRecord(
            crm_client_id="C1",
            pan="ABCDE1234F",
            investor_name="Ramesh Sharma",
            mobile="9876543210",
            email="ramesh@gmail.com"
        )
    ]
    matcher = RecordMatcher(crm_recs)

    report = ReportRecord(
        source=RecordSource.CAMS,
        folio_number="F123",
        raw_row_index=1,
        pan="VWXYZ9876A",
        investor_name="Ramesh Sharma",
        mobile="9876543210",
        email="ramesh@gmail.com"
    )

    # Fuzzy matching is false, should be unmatched
    res = matcher.find_match(report, enable_fuzzy=False)
    assert res.match_type == "UNMATCHED"
