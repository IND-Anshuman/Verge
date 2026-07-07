"""Hash-chained incident report generator (spec §14 Phase 3 — audit).

This is the **final, audit-backed** incident report — distinct from the
orchestrator's real-time preliminary draft (`verge_orchestrator.report`, which an
LLM narrates for the operator during the event). This report is a legal record:
assembled deterministically (no LLM) from the finding, its full lifecycle/audit
trail, its evidence pack, and the regulatory clauses the hazard touches, then
bound to the audit-chain head by a content hash. Same inputs → same hash, so the
report is reproducible and tamper-evident (P6) — what a regulator can rely on.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime

from verge_audit import canonical_json
from verge_audit.chain import GENESIS_HASH
from verge_schema.findings import RiskFinding

from .clauses import Clause, load_clauses

# Hazard keyword / signal → the capability (hence clause) an incident touches.
_KEYWORD_CAPABILITIES: dict[str, str] = {
    "hot-work": "hot-work-control",
    "hot work": "hot-work-control",
    "hot-tapping": "hot-work-control",
    "confined-space": "confined-space-control",
    "confined space": "confined-space-control",
    "vessel-entry": "confined-space-control",
    "isolation": "isolation-control",
    "simops": "simops-review",
    "changeover": "shift-handover",
    "handover": "shift-handover",
    "drift": "gas-drift-monitoring",
}


def clauses_for_finding(finding: RiskFinding, clauses: list[Clause] | None = None) -> list[Clause]:
    """Select the regulatory clauses a finding's hazard touches (deterministic)."""
    clauses = clauses or load_clauses()
    blob = " ".join(
        [finding.title.lower(), *(s.summary.lower() for s in finding.contributing_signals),
         *(s.ref_id.lower() for s in finding.contributing_signals)]
    )
    caps: set[str] = set()
    for keyword, cap in _KEYWORD_CAPABILITIES.items():
        if keyword in blob:
            caps.add(cap)
    if any(s.kind == "reading" for s in finding.contributing_signals):
        caps.add("gas-detection")
    # Every incident report rests on the audit + evidence guarantees.
    caps.update({"audit", "evidence"})
    return [c for c in clauses if c.capability in caps]


def _ts_key(entry: dict) -> str:
    """Sortable string key tolerant of datetime OR str timestamps (or missing).

    Persisted audit rows carry datetime timestamps; API-JSON rows carry ISO
    strings. Mixing them in sorted() raises TypeError — normalize to isoformat."""
    ts = entry.get("timestamp")
    if isinstance(ts, datetime):
        return ts.isoformat()
    return str(ts) if ts is not None else ""


def _timeline(audit_trail: list[dict]) -> list[dict]:
    """Reconstruct a human timeline from the finding's audit entries."""
    events: list[dict] = []
    for e in sorted(audit_trail, key=_ts_key):
        kind = e.get("kind", "")
        payload = e.get("payload") or {}
        actor = e.get("actor", "")
        ts = _ts_key(e)
        if kind == "finding-created":
            desc = "finding created"
        elif kind == "finding-event":
            frm = payload.get("fromState") or "—"
            desc = f"{frm} → {payload.get('toState', '?')}"
            if payload.get("reasonText") or payload.get("reasonCode"):
                desc += f" ({payload.get('reasonText') or payload.get('reasonCode')})"
        elif kind == "feedback":
            desc = f"feedback: {payload.get('verdict', '?')}"
            if payload.get("reasonCode"):
                desc += f" ({payload['reasonCode']})"
        else:
            desc = kind
        events.append({"ts": ts, "actor": actor, "event": desc})
    return events


@dataclass
class IncidentReport:
    report_id: str
    finding_id: str
    created_at: datetime
    timeline: list[dict]
    cited: list[str]
    clause_ids: list[str]
    evidence_hash: str | None
    audit_head: str
    hash: str = ""
    markdown: str = field(default="", repr=False)

    def to_dict(self) -> dict:
        return {
            "reportId": self.report_id,
            "findingId": self.finding_id,
            "createdAt": self.created_at.isoformat(),
            "timeline": self.timeline,
            "cited": self.cited,
            "clauseIds": self.clause_ids,
            "evidenceHash": self.evidence_hash,
            "auditHead": self.audit_head,
            "manifestHash": self.hash,
            "markdown": self.markdown,
        }


def build_incident_report(
    finding: RiskFinding,
    *,
    audit_trail: list[dict],
    created_at: datetime,
    evidence_hash: str | None = None,
    clauses: list[Clause] | None = None,
    audit_head: str = GENESIS_HASH,
) -> IncidentReport:
    timeline = _timeline(audit_trail)
    cited = [f"{s.kind}:{s.ref_id}" for s in finding.contributing_signals] or list(finding.lineage)
    linked = clauses_for_finding(finding, clauses)
    clause_ids = sorted(c.id for c in linked)

    # Content hash covers the report substance + evidence + audit head, NOT the
    # wall-clock time — identical incidents produce identical, comparable hashes.
    # Hash the SAME representation the rendered report shows (signal order,
    # which is deterministic from the engine) — so a matching hash means a byte-
    # identical human artifact, not just matching content in some other order.
    body = {
        "findingId": finding.finding_id,
        "title": finding.title,
        "zoneId": finding.zone_id,
        "timeline": timeline,
        "cited": cited,
        "clauseIds": clause_ids,
        "evidenceHash": evidence_hash,
        "auditHead": audit_head,
    }
    digest = hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()

    report = IncidentReport(
        report_id=f"IR-{finding.finding_id}",
        finding_id=finding.finding_id,
        created_at=created_at,
        timeline=timeline,
        cited=cited,
        clause_ids=clause_ids,
        evidence_hash=evidence_hash,
        audit_head=audit_head,
        hash=digest,
    )
    report.markdown = _render_markdown(finding, report, linked)
    return report


def _render_markdown(finding: RiskFinding, report: IncidentReport, clauses: list[Clause]) -> str:
    lines = [
        f"# Incident report — {finding.finding_id}",
        "",
        "> Final audit-backed record (spec §14 Phase 3). Assembled deterministically "
        "from the audit chain — reproducible and tamper-evident (P6), not an LLM draft.",
        "",
        f"**Title** {finding.title}",
        f"**Zone** {finding.zone_id} · **band** {finding.lead_time_band} · "
        f"**confidence** {finding.confidence:.2f}",
        "",
        "## Timeline",
        "",
    ]
    if report.timeline:
        for ev in report.timeline:
            actor = f" — {ev['actor']}" if ev["actor"] else ""
            lines.append(f"- `{ev['ts']}` {ev['event']}{actor}")
    else:
        lines.append("- (no lifecycle events recorded)")
    lines += ["", "## Contributing signals (lineage)", ""]
    for s in finding.contributing_signals:
        lines.append(f"- {s.kind}:{s.ref_id} — {s.summary}")
    if not finding.contributing_signals:
        lines.append("- (none recorded)")
    if clauses:
        lines += ["", "## Regulatory linkage", ""]
        for c in clauses:
            lines.append(f"- **{c.id}** ({c.standard}) — {c.title}")
    lines += [
        "",
        "## Integrity",
        "",
        f"- Report id: `{report.report_id}`",
        f"- Manifest hash: `{report.hash}`",
        f"- Audit head at issue: `{report.audit_head}`",
    ]
    if report.evidence_hash:
        lines.append(f"- Evidence pack manifest: `{report.evidence_hash}`")
    lines.append("")
    return "\n".join(lines)
