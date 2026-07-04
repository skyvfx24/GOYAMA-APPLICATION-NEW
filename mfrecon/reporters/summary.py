"""Executive summary reporter computing metrics and formatting plain text summaries."""

from typing import Any

from mfrecon.core.domain import DiscrepancyType, ReconciliationResult


class SummaryReporter:
    """Computes reconciliation run metrics and formats an executive summary."""

    def get_summary_metrics(self, result: ReconciliationResult) -> dict[str, Any]:
        """
        Computes counts and breakdowns from a ReconciliationResult.

        Args:
            result: Facade ReconciliationResult container.

        Returns:
            dict[str, Any]: Mapping of summary metric counts.
        """
        total_crm = result.metadata.total_crm_records
        total_report = result.metadata.total_report_records
        matched_count = len(result.matched_audits)

        missing_in_crm = 0
        missing_in_report = 0
        field_discrepancies = 0

        breakdown: dict[str, int] = {}
        for disc in result.discrepancies:
            d_type = disc.discrepancy_type.value
            breakdown[d_type] = breakdown.get(d_type, 0) + 1
            if disc.discrepancy_type == DiscrepancyType.MISSING_IN_CRM:
                missing_in_crm += 1
            elif disc.discrepancy_type == DiscrepancyType.MISSING_IN_REPORT:
                missing_in_report += 1
            else:
                field_discrepancies += 1

        return {
            "total_crm_records": total_crm,
            "total_report_records": total_report,
            "matched_records": matched_count,
            "missing_in_crm": missing_in_crm,
            "missing_in_report": missing_in_report,
            "field_discrepancies": field_discrepancies,
            "validation_failures": result.metadata.validation_failures_count,
            "failed_files_count": len(result.metadata.failed_files),
            "discrepancy_breakdown": breakdown,
        }

    def generate_summary(self, result: ReconciliationResult) -> str:
        """
        Formats metrics into a plain text executive summary statement.

        Args:
            result: Facade ReconciliationResult container.

        Returns:
            str: Plain text summary.
        """
        metrics = self.get_summary_metrics(result)

        lines = [
            "==================================================",
            "        RECONCILIATION RUN EXECUTIVE SUMMARY      ",
            "==================================================",
            f"Total CRM Records: {metrics['total_crm_records']:,}",
            f"Total Report Records: {metrics['total_report_records']:,}",
            f"Matched Records: {metrics['matched_records']:,}",
            f"Missing In CRM: {metrics['missing_in_crm']:,}",
            f"Missing In Report: {metrics['missing_in_report']:,}",
            f"Discrepancies: {metrics['field_discrepancies']:,}",
            f"Validation Failures: {metrics['validation_failures']:,}",
            f"Failed Files: {metrics['failed_files_count']:,}",
            "",
            "Discrepancy Breakdown by Type:",
            "--------------------------------------------------",
        ]

        breakdown = metrics["discrepancy_breakdown"]
        if breakdown:
            for d_type, count in sorted(breakdown.items()):
                lines.append(f" - {d_type}: {count:,}")
        else:
            lines.append(" - No discrepancies detected.")

        lines.append("==================================================")
        return "\n".join(lines)
