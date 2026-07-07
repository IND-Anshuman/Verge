"""Emergency Response Orchestrator (spec §4.4). Advisory only (P8)."""

from .alerts import draft_alert, draft_messages
from .dispatch import (
    DeliveryResult,
    DispatchReceipt,
    channels_from_env,
    dispatch_alert,
)
from .evidence import build_evidence_pack, manifest_hash
from .orchestrate import Response, phrase_for, recommend_action, respond
from .report import ReportDraft, draft_incident_report

__all__ = [
    "DeliveryResult",
    "DispatchReceipt",
    "ReportDraft",
    "Response",
    "build_evidence_pack",
    "channels_from_env",
    "dispatch_alert",
    "draft_alert",
    "draft_incident_report",
    "draft_messages",
    "manifest_hash",
    "phrase_for",
    "recommend_action",
    "respond",
]
__version__ = "0.3.0"
