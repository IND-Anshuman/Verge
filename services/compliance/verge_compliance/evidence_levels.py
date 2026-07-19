"""Evidence-level disclaimer mapping for gap board (Phase 3B).

Levels (honest, never a fake % as the primary claim):
  platform | configured | observed | attested | not-evidenced
"""

from __future__ import annotations

from .gaps import STATUS_GAP, STATUS_SATISFIED, ClauseResult, ComplianceReport

LEVEL_PLATFORM = "platform"
LEVEL_CONFIGURED = "configured"
LEVEL_OBSERVED = "observed"
LEVEL_ATTESTED = "attested"
LEVEL_NOT_EVIDENCED = "not-evidenced"


def evidence_level_for(result: ClauseResult) -> str:
    """Map a clause assessment row to a disclaimer level."""
    if result.clause.is_platform and result.status == STATUS_SATISFIED:
        return LEVEL_PLATFORM
    if result.status == STATUS_SATISFIED:
        # Deterministic detectors prove plant config — not human attestation.
        return LEVEL_CONFIGURED
    reason = (result.reason or "").lower()
    if "no detector" in reason:
        return LEVEL_NOT_EVIDENCED
    return LEVEL_NOT_EVIDENCED


def enrich_report(report: ComplianceReport) -> dict:
    """Wire-ready report with per-clause evidenceLevel; coverage is secondary."""
    clauses = []
    level_counts: dict[str, int] = {}
    for r in report.results:
        level = evidence_level_for(r)
        level_counts[level] = level_counts.get(level, 0) + 1
        row = r.to_dict()
        row["evidenceLevel"] = level
        clauses.append(row)
    gaps = [c for c in clauses if c.get("status") == STATUS_GAP]
    return {
        "plant": report.plant,
        "satisfied": report.satisfied,
        "gaps": len(gaps),
        "total": len(report.results),
        # Kept for backwards compat but UI must not treat this as a compliance KPI.
        "coverageRatio": round(report.coverage_ratio, 4),
        "coverageDisclaimer": (
            "coverageRatio is a detector tally, not a legal compliance percentage. "
            "Use evidenceLevel drill-down per clause."
        ),
        "evidenceLevels": level_counts,
        "clauses": clauses,
        "gapBoard": gaps,
    }
