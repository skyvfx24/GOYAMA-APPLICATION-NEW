"""Engine package initialization. Exposes ReconciliationEngine, RecordMatcher, and results."""

from mfrecon.engine.discrepancy import compare_records
from mfrecon.engine.explainability import format_explanation
from mfrecon.engine.matcher import MatchResult, RecordMatcher
from mfrecon.engine.reconciler import ReconciliationEngine
from mfrecon.engine.result import ReconciliationMetadata, ReconciliationResult, ReconciliationStatistics

__all__ = [
    "MatchResult",
    "RecordMatcher",
    "compare_records",
    "format_explanation",
    "ReconciliationEngine",
    "ReconciliationMetadata",
    "ReconciliationResult",
    "ReconciliationStatistics",
]
