"""Compliance: OISD / Factory Act / DGMS gap detection + evidence packs (spec §5).

Deterministic, LLM-free gap detection over a commissioned plant and its adopted
rules, plus regulator-ready, hash-chained evidence packs (P6). A gap is a legal
claim, so it is reproducible by construction — never generated.
"""

from .actions import (
    ActionsLog,
    CorrectiveAction,
    IllegalActionTransition,
    suggest_control_tier,
)
from .changes import changes_since_prior, diff_clauses, library_fingerprint
from .clauses import Clause, load_clauses
from .evidence import CompliancePack, build_compliance_pack
from .evidence_levels import enrich_report, evidence_level_for
from .gaps import ClauseResult, ComplianceReport, assess, gap_findings
from .incident_report import IncidentReport, build_incident_report, clauses_for_finding
from .render import render_markdown

__all__ = [
    "ActionsLog",
    "Clause",
    "ClauseResult",
    "CompliancePack",
    "ComplianceReport",
    "CorrectiveAction",
    "IllegalActionTransition",
    "IncidentReport",
    "assess",
    "suggest_control_tier",
    "build_compliance_pack",
    "build_incident_report",
    "changes_since_prior",
    "clauses_for_finding",
    "diff_clauses",
    "enrich_report",
    "evidence_level_for",
    "gap_findings",
    "library_fingerprint",
    "load_clauses",
    "render_markdown",
]
__version__ = "0.3.0"
