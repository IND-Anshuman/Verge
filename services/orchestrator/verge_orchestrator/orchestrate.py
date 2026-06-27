"""The closer: turn a confirmed finding into a coordinated, ADVISORY response.

Everything here is decision-support (P8). `respond()` returns recommendations,
a drafted alert, an evidence pack, and a report draft — it executes nothing.
The recommended Action is `advisory=True` and its kind is a `recommend-*` verb;
Verge never writes to OT/control/permit systems. The caller (API) hash-chains
the returned audit events and waits for the human to Approve.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from verge_llm import LLMProvider
from verge_schema.audit import Action, Alert, EvidencePack
from verge_schema.findings import RiskFinding

from .alerts import draft_alert
from .evidence import build_evidence_pack
from .report import ReportDraft, draft_incident_report


def recommend_action(finding: RiskFinding) -> Action:
    """Pick an advisory action from the finding. Never executed by Verge (P8)."""
    permit = next((s for s in finding.contributing_signals if s.kind == "permit"), None)
    if permit:
        kind = "recommend-permit-pause"
    elif finding.lead_time_band in ("IMMINENT", "NEAR"):
        kind = "recommend-evacuate-zone"
    else:
        kind = "recommend-investigate"
    return Action(
        action_id=f"AC-{finding.finding_id}",
        finding_id=finding.finding_id,
        kind=kind,
        advisory=True,
        timestamp=finding.created_at,
    )


_ACTION_PHRASE = {
    "recommend-permit-pause": "pause the permit and the shift handover",
    "recommend-evacuate-zone": "evacuate the affected zone",
    "recommend-investigate": "dispatch a check of the affected zone",
}


@dataclass
class Response:
    action: Action
    alert: Alert
    evidence: EvidencePack
    report: ReportDraft

    def audit_payloads(self) -> list[dict]:
        """What the caller should hash-chain (advisory recommendation + artifacts)."""
        return [
            {
                "kind": "recommendation",
                "action": self.action.model_dump(by_alias=True, mode="json"),
            },
            {"kind": "alert-drafted", "alertId": self.alert.alert_id,
             "channels": self.alert.channels, "languages": self.alert.languages},
            {"kind": "evidence-pack", "packId": self.evidence.pack_id,
             "manifestHash": self.evidence.manifest_hash},
        ]


def respond(
    finding: RiskFinding, *, at: datetime, provider: LLMProvider | None = None
) -> Response:
    action = recommend_action(finding)
    phrase = _ACTION_PHRASE.get(action.kind, "review the finding")
    alert = draft_alert(finding, phrase, issued_at=at)
    evidence = build_evidence_pack(finding, created_at=at)
    report = draft_incident_report(finding, evidence, at=at, provider=provider)
    return Response(action=action, alert=alert, evidence=evidence, report=report)
