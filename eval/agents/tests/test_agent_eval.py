"""Gold brief gates for Phase 2.5 GenAI Core."""

from __future__ import annotations

import json
from pathlib import Path

from eval.agents.metrics import (
    citation_precision,
    groundedness_proxy,
    invented_tag_rate,
)
from verge_agents import TwinCatalog, validate_brief

GOLD = Path(__file__).resolve().parents[1] / "gold" / "briefs.json"


def _load_gold() -> list[dict]:
    return json.loads(GOLD.read_text(encoding="utf-8"))


def _catalog(row: dict) -> TwinCatalog:
    c = row["catalog"]
    return TwinCatalog(
        zone_ids=frozenset(c.get("zoneIds") or []),
        equipment_ids=frozenset(c.get("equipmentIds") or []),
        sensor_ids=frozenset(c.get("sensorIds") or []),
    )


def test_gold_file_has_at_least_three_briefs():
    assert len(_load_gold()) >= 3


def test_clean_gold_briefs_pass_validator():
    for row in _load_gold():
        if row.get("expectInvented"):
            continue
        out, report = validate_brief(
            row["brief"],
            _catalog(row),
            evidence_tools=row["evidenceTools"],
        )
        assert report.ok, (row["id"], report.to_wire())
        assert out["recommendedBarriers"]


def test_ghost_case_caught_by_validator():
    row = next(r for r in _load_gold() if r.get("expectInvented"))
    _, report = validate_brief(
        row["brief"],
        _catalog(row),
        evidence_tools=row["evidenceTools"],
    )
    for tag in row["expectInvented"]:
        assert tag in report.invented_tags


def test_invented_tag_rate_on_clean_subset_is_zero():
    clean = [r["brief"] for r in _load_gold() if not r.get("expectInvented")]
    # Use union catalog from first clean row + extras from all clean
    zones: set[str] = set()
    eq: set[str] = set()
    sensors: set[str] = set()
    for r in _load_gold():
        if r.get("expectInvented"):
            continue
        c = r["catalog"]
        zones |= set(c.get("zoneIds") or [])
        eq |= set(c.get("equipmentIds") or [])
        sensors |= set(c.get("sensorIds") or [])
    catalog = TwinCatalog(
        zone_ids=frozenset(zones),
        equipment_ids=frozenset(eq),
        sensor_ids=frozenset(sensors),
    )
    metrics = invented_tag_rate(clean, catalog)
    assert metrics["rate"] == 0.0


def test_citation_precision_on_gold_barriers():
    allowed: set[str] = set()
    barriers: list[dict] = []
    for r in _load_gold():
        if r.get("expectInvented"):
            continue
        allowed |= set(r["evidenceTools"])
        barriers.extend(r["brief"].get("recommendedBarriers") or [])
    m = citation_precision(barriers, allowed)
    assert m["precision"] >= 0.85


def test_groundedness_proxy_on_gold_summaries():
    for r in _load_gold():
        if r.get("expectInvented"):
            continue
        g = groundedness_proxy(r["brief"]["summary"], r["digestTokens"])
        assert g["grounded"] is True
