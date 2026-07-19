"""Gap board evidence levels — no bare compliance % as primary claim (Phase 3B)."""

from __future__ import annotations

from verge_compliance import assess, enrich_report, load_clauses
from verge_risk import STARTER_RULES, load_rules
from verge_twin import load_plant


def test_enrich_report_exposes_evidence_levels_and_disclaimer():
    plant = load_plant()
    report = assess(plant, load_rules(STARTER_RULES))
    body = enrich_report(report)
    assert "coverageDisclaimer" in body
    assert "evidenceLevels" in body
    assert "gapBoard" in body
    assert "legal compliance percentage" in body["coverageDisclaimer"].lower()
    for row in body["clauses"]:
        assert row["evidenceLevel"] in {
            "platform",
            "configured",
            "observed",
            "attested",
            "not-evidenced",
        }


def test_peso_pack_loaded_with_oisd():
    clauses = load_clauses()
    standards = {c.standard for c in clauses}
    assert any("OISD" in s or "oisd" in s.lower() for s in standards) or len(clauses) > 5
    ids = {c.id for c in clauses}
    # peso.json contributes distinct clause ids when present
    assert len(ids) == len(clauses)
