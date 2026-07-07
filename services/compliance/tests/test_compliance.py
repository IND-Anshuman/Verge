"""OISD/Factory Act gap detection + evidence packs (spec §5 compliance)."""

from __future__ import annotations

from datetime import UTC, datetime

from verge_compliance import (
    assess,
    build_compliance_pack,
    gap_findings,
    load_clauses,
)
from verge_compliance.clauses import PLATFORM_CAPABILITIES
from verge_risk import STARTER_RULES, load_rules
from verge_twin import load_plant

NOW = datetime(2026, 7, 7, tzinfo=UTC)


def _demo():
    return load_plant(), load_rules(STARTER_RULES)


def test_platform_clauses_always_satisfied():
    plant, rules = _demo()
    report = assess(plant, rules)
    for r in report.results:
        if r.clause.capability in PLATFORM_CAPABILITIES:
            assert r.status == "satisfied"


def test_demo_plant_satisfies_its_configured_capabilities():
    plant, rules = _demo()
    report = assess(plant, rules)
    by_cap = {r.clause.capability: r.status for r in report.results}
    # The coke-oven demo has gas sensors, hot-work + confined-space rules,
    # shift-changeover rules, and adjacency.
    assert by_cap["gas-detection"] == "satisfied"
    assert by_cap["hot-work-control"] == "satisfied"
    assert by_cap["confined-space-control"] == "satisfied"
    assert by_cap["shift-handover"] == "satisfied"
    assert by_cap["simops-review"] == "satisfied"
    assert by_cap["adjacency"] == "satisfied"


def test_demo_plant_has_honest_gaps():
    plant, rules = _demo()
    report = assess(plant, rules)
    by_cap = {r.clause.capability: r.status for r in report.results}
    # The coke-oven demo has no tank-farm or startup-abnormal rules.
    assert by_cap["tank-farm-monitoring"] == "gap"
    assert by_cap["startup-monitoring"] == "gap"
    assert 0.0 < report.coverage_ratio < 1.0


def test_gap_findings_are_regulatory_gap_payloads():
    plant, rules = _demo()
    report = assess(plant, rules)
    findings = gap_findings(report)
    assert findings
    for f in findings:
        assert f["kind"] == "regulatory-gap"
        assert f["clauseId"] and f["capability"] and f["standard"]


def test_evidence_pack_is_reproducible_and_hash_stable():
    plant, rules = _demo()
    report = assess(plant, rules)
    p1 = build_compliance_pack(report, created_at=NOW, finding_ids=["F-1", "F-2"])
    # A second assessment over identical inputs must hash identically, even at a
    # different wall-clock time (the hash covers content, not the timestamp).
    later = datetime(2026, 8, 1, tzinfo=UTC)
    p2 = build_compliance_pack(assess(plant, rules), created_at=later,
                               finding_ids=["F-2", "F-1"])
    assert p1.hash == p2.hash
    assert len(p1.hash) == 64
    assert p1.gap_clause_ids == p2.gap_clause_ids


def test_evidence_pack_hash_changes_with_coverage():
    plant, rules = _demo()
    full = build_compliance_pack(assess(plant, rules), created_at=NOW)
    fewer = build_compliance_pack(assess(plant, rules[:2]), created_at=NOW)
    assert full.hash != fewer.hash


def test_clause_library_loads():
    clauses = load_clauses()
    assert len(clauses) >= 15
    assert all(c.id and c.capability for c in clauses)
