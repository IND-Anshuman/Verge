"""Hash-chained incident report generator (spec §14 Phase 3 — audit)."""

from __future__ import annotations

from datetime import UTC, datetime

from verge_compliance import build_incident_report, clauses_for_finding
from verge_schema.findings import ContributingSignal, RiskFinding

NOW = datetime(2026, 7, 7, tzinfo=UTC)


def _finding() -> RiskFinding:
    return RiskFinding(
        finding_id="F-CONV-07",
        created_at=NOW,
        zone_id="B-04",
        title="Hot work near elevated/rising flammable gas",
        confidence=0.85,
        contributing_signals=[
            ContributingSignal(kind="permit", ref_id="PTW-1001", summary="hot-work permit active"),
            ContributingSignal(kind="reading", ref_id="LEL-04", summary="gas-lel 88 (near)"),
        ],
        lineage=["permit:PTW-1001", "reading:LEL-04"],
    )


def _trail() -> list[dict]:
    return [
        {"kind": "finding-created", "actor": "risk-engine",
         "timestamp": "2026-07-07T06:00:00+00:00",
         "payload": {"findingId": "F-CONV-07", "title": "Hot work..."}},
        {"kind": "finding-event", "actor": "maya", "timestamp": "2026-07-07T06:02:00+00:00",
         "payload": {"findingId": "F-CONV-07", "fromState": "new", "toState": "acknowledged"}},
        {"kind": "feedback", "actor": "maya", "timestamp": "2026-07-07T06:30:00+00:00",
         "payload": {"findingId": "F-CONV-07", "verdict": "useful", "reasonCode": "real-hazard"}},
    ]


def test_timeline_is_ordered_and_human_readable():
    report = build_incident_report(_finding(), audit_trail=_trail(), created_at=NOW)
    events = [e["event"] for e in report.timeline]
    assert events[0] == "finding created"
    assert "new → acknowledged" in events[1]
    assert "feedback: useful" in events[2]


def test_clause_linkage_matches_hazard():
    linked = {c.id for c in clauses_for_finding(_finding())}
    # Hot-work + gas reading → hot-work + gas-detection clauses, plus audit/evidence.
    assert "VC-HOT-WORK" in linked
    assert "VC-GAS-DETECTION" in linked
    assert "VC-AUDIT" in linked and "VC-EVIDENCE" in linked
    # Not a confined-space or tank incident.
    assert "VC-TANK-FARM" not in linked


def test_report_hash_is_reproducible_and_ignores_wall_clock():
    a = build_incident_report(_finding(), audit_trail=_trail(), created_at=NOW,
                              audit_head="abc", evidence_hash="ev123")
    later = datetime(2027, 1, 1, tzinfo=UTC)
    b = build_incident_report(_finding(), audit_trail=list(reversed(_trail())),
                              created_at=later, audit_head="abc", evidence_hash="ev123")
    assert a.hash == b.hash  # same substance, different time / trail order
    assert len(a.hash) == 64


def test_report_hash_changes_with_audit_head():
    a = build_incident_report(_finding(), audit_trail=_trail(), created_at=NOW, audit_head="head-1")
    b = build_incident_report(_finding(), audit_trail=_trail(), created_at=NOW, audit_head="head-2")
    assert a.hash != b.hash  # bound to the audit chain state


def test_timeline_tolerates_datetime_and_missing_timestamps():
    # Persisted audit rows carry datetime timestamps; mixing with a missing one
    # must not crash sorted() (a real audit trail passed straight in).
    trail = [
        {"kind": "finding-event", "actor": "a", "timestamp": NOW,
         "payload": {"findingId": "F-CONV-07", "fromState": "new", "toState": "acknowledged"}},
        {"kind": "finding-created", "actor": "risk-engine",
         "payload": {"findingId": "F-CONV-07"}},  # no timestamp
    ]
    report = build_incident_report(_finding(), audit_trail=trail, created_at=NOW)
    assert len(report.timeline) == 2  # did not raise


def test_markdown_contains_timeline_and_integrity():
    md = build_incident_report(_finding(), audit_trail=_trail(), created_at=NOW,
                               audit_head="deadbeef").markdown
    assert "Incident report — F-CONV-07" in md
    assert "## Timeline" in md
    assert "## Integrity" in md
    assert "deadbeef" in md
