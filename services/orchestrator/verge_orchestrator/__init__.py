"""Emergency Response Orchestrator (spec §4.4). Advisory only (P8)."""

from .alerts import draft_alert, draft_messages
from .evidence import build_evidence_pack, manifest_hash
from .orchestrate import Response, recommend_action, respond
from .report import ReportDraft, draft_incident_report

__all__ = [
    "ReportDraft",
    "Response",
    "build_evidence_pack",
    "draft_alert",
    "draft_incident_report",
    "draft_messages",
    "manifest_hash",
    "recommend_action",
    "respond",
]
__version__ = "0.3.0"
