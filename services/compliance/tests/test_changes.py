"""Regulatory-change monitoring (spec §14 Phase 3)."""

from __future__ import annotations

from verge_compliance import (
    changes_since_prior,
    diff_clauses,
    library_fingerprint,
    load_clauses,
)
from verge_compliance.changes import load_prior


def test_fingerprint_is_stable_and_order_independent():
    clauses = load_clauses()
    assert library_fingerprint(clauses) == library_fingerprint(list(reversed(clauses)))
    assert len(library_fingerprint(clauses)) == 64


def test_identical_library_has_no_changes():
    clauses = load_clauses()
    diff = diff_clauses(clauses, clauses)
    assert diff["changed"] is False
    assert not diff["added"] and not diff["removed"] and not diff["modified"]


def test_current_vs_prior_snapshot_detects_additions_and_modifications():
    diff = changes_since_prior()
    assert diff["changed"] is True
    # Current library added gas-detection + startup clauses since the 2023 baseline.
    assert "VC-GAS-DETECTION" in diff["added"]
    assert "VC-STARTUP" in diff["added"]
    # The hot-work requirement wording was strengthened.
    modified_ids = {m["clauseId"] for m in diff["modified"]}
    assert "VC-HOT-WORK" in modified_ids
    hot = next(m for m in diff["modified"] if m["clauseId"] == "VC-HOT-WORK")
    assert "requirement" in hot["changes"]
    assert diff["fingerprintFrom"] != diff["fingerprintTo"]


def test_prior_snapshot_loads():
    assert len(load_prior()) >= 12


def test_duplicate_clause_id_is_rejected(tmp_path):
    import json

    import pytest

    dup = [
        {"id": "VC-X", "title": "A", "requirement": "r", "capability": "audit"},
        {"id": "VC-X", "title": "B", "requirement": "r", "capability": "evidence"},
    ]
    p = tmp_path / "dup.json"
    p.write_text(json.dumps(dup), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate clause id"):
        load_clauses(p)
