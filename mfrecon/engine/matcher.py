"""Record matching logic using indexed lookups and secondary fuzzy validation fallback."""

from rapidfuzz import fuzz

from mfrecon.core.domain import CRMRecord, ReportRecord


class MatchResult:
    """Encapsulates the result of a single record alignment attempt."""

    def __init__(
        self,
        match_type: str,
        confidence: float,
        matching_route: str,
        crm_record: CRMRecord | None = None
    ) -> None:
        self.match_type = match_type
        self.confidence = confidence
        self.matching_route = matching_route
        self.crm_record = crm_record


class RecordMatcher:
    """Aligns ReportRecord items against indexed CRMRecord master lists."""

    def __init__(self, crm_records: list[CRMRecord]) -> None:
        self.crm_records = crm_records

        # Build lookup tables for O(1) alignment lookups
        self.pan_index: dict[str, list[CRMRecord]] = {}
        self.mobile_index: dict[str, list[CRMRecord]] = {}
        self.email_index: dict[str, list[CRMRecord]] = {}

        for rec in crm_records:
            if rec.pan:
                # Store by normalized PAN
                self.pan_index.setdefault(rec.pan.strip().upper(), []).append(rec)
            if rec.mobile:
                # Store by normalized mobile
                self.mobile_index.setdefault(rec.mobile.strip(), []).append(rec)
            if rec.email:
                # Store by normalized email
                self.email_index.setdefault(rec.email.strip().lower(), []).append(rec)

    def find_match(
        self,
        report_record: ReportRecord,
        enable_fuzzy: bool = False,
        threshold: float = 0.90,
        secondary_keys: list[str] | None = None
    ) -> MatchResult:
        """
        Attempts to align a ReportRecord to a CRMRecord.

        Args:
            report_record: Mapped record from input report file.
            enable_fuzzy: Flag enabling fuzzy matching fallback.
            threshold: Fuzzy matching name similarity threshold (0.0 to 1.0).
            secondary_keys: Mandatory fields checked during secondary fuzzy matching.

        Returns:
            MatchResult: Alignment result parameters and aligned CRMRecord.
        """
        if secondary_keys is None:
            secondary_keys = ["mobile", "email"]

        pan_key = report_record.pan.strip().upper() if report_record.pan else ""

        # 1. Attempt exact PAN match
        if pan_key and pan_key in self.pan_index:
            # Match the first record in index (or iterate if multiple, but first is standard)
            crm_rec = self.pan_index[pan_key][0]
            return MatchResult(
                match_type="EXACT",
                confidence=1.0,
                matching_route="EXACT_PAN",
                crm_record=crm_rec
            )

        # 2. Fuzzy Matching fallback (if enabled)
        if enable_fuzzy:
            candidates_list: list[CRMRecord] = []

            # Retrieve candidates matching exact secondary key (Mobile or Email)
            if "mobile" in secondary_keys and report_record.mobile:
                mobile_key = report_record.mobile.strip()
                if mobile_key in self.mobile_index:
                    candidates_list.extend(self.mobile_index[mobile_key])

            if "email" in secondary_keys and report_record.email:
                email_key = report_record.email.strip().lower()
                if email_key in self.email_index:
                    candidates_list.extend(self.email_index[email_key])

            # Deduplicate CRMRecords by crm_client_id
            candidates: list[CRMRecord] = []
            seen_ids = set()
            for cand in candidates_list:
                if cand.crm_client_id not in seen_ids:
                    seen_ids.add(cand.crm_client_id)
                    candidates.append(cand)

            best_candidate: CRMRecord | None = None
            best_score = 0.0
            best_route = "UNMATCHED"

            # Check name similarity on eligible candidates
            for candidate in candidates:
                if not candidate.investor_name or not report_record.investor_name:
                    continue

                # Compute similarity score using RapidFuzz (0 to 100)
                score = float(fuzz.token_sort_ratio(candidate.investor_name, report_record.investor_name))
                score / 100.0

                # Check if similarity meets threshold (supporting both 0-1 and 0-100 ranges)
                threshold_val = threshold if threshold > 1.0 else threshold * 100.0
                if score >= threshold_val and score > best_score:
                    best_score = score
                    best_candidate = candidate

                    # Identify which key successfully aligned
                    if report_record.mobile and candidate.mobile == report_record.mobile:
                        best_route = "FUZZY_NAME_AND_MOBILE"
                    else:
                        best_route = "FUZZY_NAME_AND_EMAIL"

            if best_candidate is not None:
                return MatchResult(
                    match_type="FUZZY_MATCH_WARNING",
                    confidence=best_score / 100.0,
                    matching_route=best_route,
                    crm_record=best_candidate
                )

        # 3. Unmatched
        return MatchResult(
            match_type="UNMATCHED",
            confidence=0.0,
            matching_route="UNMATCHED",
            crm_record=None
        )
