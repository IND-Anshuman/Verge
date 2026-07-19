"""Phase 3 specialist gold gates — RCA / compliance / lessons demo beats."""

from __future__ import annotations

import json
from pathlib import Path

from verge_compliance import assess, enrich_report
from verge_lessons import default_corpus, match_lessons, proactive_cards
from verge_maintenance import default_store
from verge_maintenance.rca import build_rca_digest, similar_failures
from verge_risk import STARTER_RULES, load_rules
from verge_twin import load_plant

GOLD = Path(__file__).resolve().parents[1] / "gold" / "specialists.json"


def _load() -> list[dict]:
    return json.loads(GOLD.read_text(encoding="utf-8"))


def test_specialist_gold_has_three_demo_beats():
    beats = {r["demoBeat"] for r in _load()}
    assert beats >= {"rca", "compliance", "lessons"}


def test_gold_rca_digest_citations():
    row = next(r for r in _load() if r["demoBeat"] == "rca")
    store = default_store()
    orders = [o.to_dict() for o in store.list(zone_id=row["zoneId"])]
    sims = similar_failures(store, zone_id=row["zoneId"])
    digest = build_rca_digest(
        work_orders=orders,
        sensor_window={"series": [{"sensorId": "LEL-04", "points": [1]}], "degraded": False},
        manuals={
            "citations": [
                {"documentId": "DOC-HOT-WORK-SOP", "excerpt": "Purge before hot work."}
            ]
        },
        similar=sims,
        finding_title=row["title"],
    )
    assert digest["citationCount"] >= row["minCitations"]
    refs = [c["refId"] for c in digest["citations"]]
    assert any(any(r.startswith(p) for p in row["requiredRefPrefixes"]) for r in refs)


def test_gold_compliance_evidence_levels():
    row = next(r for r in _load() if r["demoBeat"] == "compliance")
    plant = load_plant()
    body = enrich_report(assess(plant, load_rules(STARTER_RULES)))
    assert row["requireEvidenceLevels"]
    assert body.get("evidenceLevels")
    assert body.get("coverageDisclaimer")
    assert "gapBoard" in body


def test_gold_lessons_proactive_card():
    row = next(r for r in _load() if r["demoBeat"] == "lessons")
    lessons = match_lessons(
        default_corpus(),
        zone_id=row["zoneId"],
        title=row["title"],
        lineage=["LEL-04"],
        permit_kinds=["hot-work"],
        hazards=["gas", "smell", "lel"],
    )
    cards = proactive_cards(lessons, finding_id="F-DEMO-LESSON")
    assert len(cards) >= row["minProactiveCards"]
    assert any(c["lessonId"] == row["expectedLessonId"] for c in cards)
    assert all(c.get("sourceRefs") for c in cards)
