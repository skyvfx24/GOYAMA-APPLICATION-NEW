from typing import Any, Dict, Set
from backend.config.settings import settings

class ResultSerializer:
    """Serializes engine's ReconciliationResult into frontend JSON schema."""

    @staticmethod
    def get_source_from_rule(rule: str) -> str:
        """Parses the source identifier from rule_evaluated text (e.g. 'SourceProfile: CAMS')."""
        rule_upper = rule.upper()
        if "CAMS" in rule_upper:
            return "CAMS"
        if "KFINTECH" in rule_upper or "KFIN" in rule_upper:
            return "KFINTECH"
        if "BSE" in rule_upper:
            return "BSE"
        if "NSE" in rule_upper:
            return "NSE"
        if "PDF_CAS" in rule_upper or "CAS" in rule_upper:
            return "PDF_CAS"
        return "UNKNOWN"

    @classmethod
    def serialize(cls, job_id: str, result: Any) -> Dict[str, Any]:
        """Converts ReconciliationResult to serialized dictionary format."""
        metadata = result.metadata
        discrepancies = result.discrepancies
        matched_audits = result.matched_audits

        # 1. Count categories of discrepancies
        missing_in_crm_count = 0
        missing_in_report_count = 0
        
        # Track unique PANs per source with discrepancies
        discrepant_pans_by_source: Dict[str, Set[str]] = {
            "CAMS": set(),
            "KFINTECH": set(),
            "BSE": set(),
            "NSE": set(),
            "PDF_CAS": set()
        }

        serialized_discrepancies = []
        for d in discrepancies:
            disc_type = d.discrepancy_type.value
            
            if disc_type == "MISSING_IN_CRM":
                missing_in_crm_count += 1
            elif disc_type == "MISSING_IN_REPORT":
                missing_in_report_count += 1
                
            source_name = cls.get_source_from_rule(d.audit_trace.rule_evaluated)
            if source_name != "UNKNOWN":
                discrepant_pans_by_source[source_name].add(d.pan)

            # Convert discrepancy to dict
            serialized_discrepancies.append({
                "discrepancy_type": disc_type,
                "pan": d.pan,
                "field_name": d.field_name,
                "crm_value": d.crm_value,
                "report_value": d.report_value,
                "severity": d.severity,
                "explanation": d.explanation,
                "source_info": d.source_info,
                "audit_trace": {
                    "matching_route": d.audit_trace.matching_route,
                    "match_confidence": d.audit_trace.match_confidence,
                    "evaluation_timestamp": d.audit_trace.evaluation_timestamp,
                    "reconciler_version": d.audit_trace.reconciler_version,
                    "rule_evaluated": d.audit_trace.rule_evaluated,
                    "skipped_comparisons": d.audit_trace.skipped_comparisons
                }
            })

        # 2. Count matched audits by source
        matched_by_source: Dict[str, int] = {
            "CAMS": 0,
            "KFINTECH": 0,
            "BSE": 0,
            "NSE": 0,
            "PDF_CAS": 0
        }
        
        # Track missing in CRM count by source
        missing_in_crm_by_source: Dict[str, int] = {
            "CAMS": 0,
            "KFINTECH": 0,
            "BSE": 0,
            "NSE": 0,
            "PDF_CAS": 0
        }

        for audit in matched_audits:
            audit_source = audit.source.upper().strip()
            # Map alternative source keys if needed
            if "KFINTECH" in audit_source:
                audit_source = "KFINTECH"
            if "PDF_CAS" in audit_source:
                audit_source = "PDF_CAS"
            if audit_source in matched_by_source:
                matched_by_source[audit_source] += 1

        for d in discrepancies:
            if d.discrepancy_type.value == "MISSING_IN_CRM":
                source_name = cls.get_source_from_rule(d.audit_trace.rule_evaluated)
                if source_name in missing_in_crm_by_source:
                    missing_in_crm_by_source[source_name] += 1

        # 3. Calculate source breakdown
        source_breakdown = {}
        for src in ["CAMS", "KFINTECH", "BSE", "NSE", "PDF_CAS"]:
            matched_count = matched_by_source[src]
            missing_count = missing_in_crm_by_source[src]
            
            # processed = matched + missing in crm (records that are in the report but not in CRM)
            processed_count = matched_count + missing_count
            discrepancy_count = len(discrepant_pans_by_source[src])
            
            source_breakdown[src] = {
                "processed": processed_count,
                "matched": matched_count,
                "discrepancies": discrepancy_count
            }

        # 4. Core summary calculations
        total_crm = metadata.total_crm_records
        matched_records = max(0, total_crm - missing_in_report_count)
        match_rate = round((matched_records / total_crm) * 100, 1) if total_crm > 0 else 100.0

        return {
            "job_id": job_id,
            "status": "done",
            "summary": {
                "total_crm_records": total_crm,
                "matched_records": matched_records,
                "missing_in_crm": missing_in_crm_count,
                "missing_in_report": missing_in_report_count,
                "discrepancy_count": len(discrepancies),
                "failed_files": len(metadata.failed_files),
                "match_rate_percent": match_rate
            },
            "failed_files": [
                {
                    "file_name": f.file_name,
                    "source": f.source,
                    "failure_type": f.failure_type,
                    "message": f.message
                } for f in metadata.failed_files
            ],
            "source_breakdown": source_breakdown,
            "pipeline_stages": [
                { "stage": "CRM Uploaded",       "status": "done" },
                { "stage": "Reports Uploaded",   "status": "done" },
                { "stage": "Validation",         "status": "done" },
                { "stage": "Reconciliation",     "status": "done" },
                { "stage": "Report Generation",  "status": "done" }
            ],
            "discrepancies": serialized_discrepancies,
            "matched_audits": [
                {
                    "pan": a.pan,
                    "route": a.route,
                    "confidence": a.confidence,
                    "source": a.source,
                    "timestamp": a.timestamp,
                    "skipped_comparisons": a.skipped_comparisons
                } for a in matched_audits
            ],
            "download_urls": {
                "excel": f"/api/reports/{job_id}/excel",
                "csv": f"/api/reports/{job_id}/csv",
                "json": f"/api/reports/{job_id}/json"
            }
        }

result_serializer = ResultSerializer()
