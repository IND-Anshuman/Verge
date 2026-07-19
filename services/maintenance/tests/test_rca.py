"""Maintenance / RCA unit tests (Phase 3A)."""

from __future__ import annotations

from verge_maintenance import default_store
from verge_maintenance.rca import build_rca_digest, similar_failures


def test_default_store_loads_vizag_wos():
    store = default_store()
    assert len(store.orders) >= 3
    assert "WO-2024-142" in store.known_ids()


def test_similar_failures_ranks_closed_b04():
    store = default_store()
    matches = similar_failures(store, zone_id="B-04")
    assert matches
    assert all(m.get("orderId") for m in matches)
    assert all(m["orderId"].startswith("WO-") for m in matches)


def test_rca_digest_has_three_citations_on_gold_zone():
    store = default_store()
    orders = [o.to_dict() for o in store.list(zone_id="B-04")]
    sims = similar_failures(store, zone_id="B-04")
    digest = build_rca_digest(
        work_orders=orders,
        sensor_window={"series": [{"sensorId": "LEL-04", "points": [1]}], "degraded": False},
        manuals={
            "citations": [
                {"documentId": "DOC-HOT-WORK-SOP", "excerpt": "Purge before hot work."}
            ]
        },
        similar=sims,
        finding_title="hot work gas risk",
    )
    assert digest["citationCount"] >= 3
    assert digest["degraded"] is False
    assert digest["scheduleSuggestion"]
    refs = {c["refId"] for c in digest["citations"]}
    assert "WO-2025-061" in refs or any(r.startswith("WO-") for r in refs)


def test_rca_never_invents_order_ids():
    store = default_store()
    known = store.known_ids()
    digest = build_rca_digest(
        work_orders=[o.to_dict() for o in store.list()],
        sensor_window={"series": [], "degraded": True},
        manuals={"citations": []},
        similar=similar_failures(store, zone_id="B-04"),
    )
    for c in digest["citations"]:
        if c["kind"] in {"work-order", "similar-failure"}:
            assert c["refId"] in known
