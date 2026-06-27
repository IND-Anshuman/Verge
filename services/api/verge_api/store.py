"""In-memory store backing the API (a Postgres-backed store wraps this later).

Owns the findings, the audit hash chain, operator feedback, and sensor-health
counts. Every lifecycle transition and feedback event is hash-chained (P6).
"""

from __future__ import annotations

from datetime import datetime, timezone

from verge_audit import AuditChain
from verge_schema.enums import DataQuality, FeedbackVerdict
from verge_schema.enums import FindingState as S
from verge_schema.findings import FindingFeedback, RiskFinding
from verge_schema.lifecycle import transition


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Store:
    def __init__(self) -> None:
        self.findings: dict[str, RiskFinding] = {}
        self.feedback: list[FindingFeedback] = []
        self.audit = AuditChain()
        self.sensor_health: dict[DataQuality, int] = {DataQuality.LIVE: 0}

    # ── findings ──────────────────────────────────────────────────────────
    def add_finding(self, f: RiskFinding) -> RiskFinding:
        self.findings[f.finding_id] = f
        self.audit.append(
            actor="risk-engine", kind="finding-created",
            payload={"findingId": f.finding_id, "title": f.title}, timestamp=f.created_at,
        )
        return f

    def list_findings(self, state: str | None = None) -> list[RiskFinding]:
        items = list(self.findings.values())
        if state:
            items = [f for f in items if f.state == state]
        return sorted(items, key=lambda f: f.created_at, reverse=True)

    def transition(
        self, finding_id: str, to: S, actor: str,
        reason_code: str | None = None, reason_text: str | None = None,
    ) -> RiskFinding:
        f = self.findings[finding_id]
        frm = S(f.state)
        ev = transition(finding_id, frm, to, actor=actor, timestamp=_now(),
                        reason_code=reason_code, reason_text=reason_text)
        f.state = to.value
        if to in (S.ASSIGNED, S.IN_PROGRESS) and actor:
            f.owner = actor
        self.audit.append(actor=actor, kind="finding-event",
                          payload=ev.model_dump(by_alias=True, mode="json"),
                          timestamp=ev.timestamp)
        return f

    # ── feedback (spec §4.6) ──────────────────────────────────────────────
    def add_feedback(self, finding_id: str, actor: str, verdict: FeedbackVerdict,
                     reason_code: str | None = None) -> FindingFeedback:
        fb = FindingFeedback(finding_id=finding_id, actor=actor, timestamp=_now(),
                             verdict=verdict, reason_code=reason_code)
        self.feedback.append(fb)
        self.audit.append(actor=actor, kind="feedback",
                          payload=fb.model_dump(by_alias=True, mode="json"),
                          timestamp=fb.timestamp)
        return fb

    def fpr(self) -> float | None:
        if not self.feedback:
            return None
        fa = sum(1 for f in self.feedback if f.verdict == FeedbackVerdict.FALSE_ALARM.value)
        return round(fa / len(self.feedback), 3)
