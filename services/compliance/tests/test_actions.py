"""CAPA workflow: clause 10.2 state machine, idempotent generation."""

from __future__ import annotations

import pytest
from verge_compliance import (
    ActionsLog,
    IllegalActionTransition,
    assess,
    suggest_control_tier,
)
from verge_risk import STARTER_RULES, load_rules
from verge_twin import DEMO_PLANT, load_plant


def _report():
    return assess(load_plant(DEMO_PLANT), load_rules(STARTER_RULES))


def test_generation_creates_one_action_per_gap_idempotently():
    log = ActionsLog()
    report = _report()
    created = log.generate_from_gaps(report)
    assert len(created) == len(report.gaps) > 0
    assert all(a.state == "open" and a.clause_id for a in created)
    # Re-run with the same gaps: nothing new (a live action already exists).
    assert log.generate_from_gaps(report) == []


def test_full_lifecycle_with_verification_gate():
    log = ActionsLog()
    action = log.generate_from_gaps(_report())[0]

    action.transition("in-progress", actor="s.rao")
    action.transition("pending-verification", actor="s.rao", note="LOTO rule adopted")

    # Clause 10.2: closing as effective REQUIRES a verification note.
    with pytest.raises(PermissionError):
        action.transition("closed-effective", actor="auditor")
    action.transition("closed-effective", actor="auditor",
                      note="verified in shift drill 2026-07-14")
    assert action.state == "closed-effective"
    assert [h["to"] for h in action.history] == [
        "in-progress", "pending-verification", "closed-effective",
    ]


def test_ineffective_action_reopens_and_can_recover():
    log = ActionsLog()
    action = log.generate_from_gaps(_report())[0]
    action.transition("in-progress", actor="a")
    action.transition("pending-verification", actor="a")
    action.transition("reopened", actor="auditor", note="drill failed")
    assert action.state == "reopened"
    action.transition("in-progress", actor="a")  # recovery path
    assert action.state == "in-progress"


def test_illegal_transitions_rejected():
    log = ActionsLog()
    action = log.generate_from_gaps(_report())[0]
    with pytest.raises(IllegalActionTransition):
        action.transition("closed-effective", actor="x", note="skip the work")
    with pytest.raises(IllegalActionTransition):
        action.transition("nonsense-state", actor="x")
    with pytest.raises(PermissionError):
        action.transition("in-progress", actor="   ")  # unnamed actor


def test_closed_action_frees_clause_for_regeneration():
    log = ActionsLog()
    report = _report()
    action = log.generate_from_gaps(report)[0]
    action.transition("in-progress", actor="a")
    action.transition("pending-verification", actor="a")
    action.transition("closed-effective", actor="v", note="verified")
    # The clause's gap persists in the (unchanged) report → a NEW action may
    # be generated for it, but live ones are still not duplicated.
    regenerated = log.generate_from_gaps(report)
    assert any(a.clause_id == action.clause_id for a in regenerated)


def test_control_tier_suggestions_follow_hierarchy():
    assert suggest_control_tier("isolation-control") == "engineering"
    assert suggest_control_tier("gas-drift-monitoring") == "engineering"
    assert suggest_control_tier("permit-review") == "administrative"
    assert suggest_control_tier("unknown-capability") == "administrative"
