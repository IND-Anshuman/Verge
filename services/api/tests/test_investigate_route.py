"""Investigation route: degraded fact-sheet path over real app-state tools."""

from __future__ import annotations

from fastapi.testclient import TestClient
from verge_api.main import app

client = TestClient(app)


def test_investigate_unknown_finding_404():
    assert client.post("/api/findings/F-NOPE/investigate").status_code == 404


def test_investigate_degraded_returns_fact_sheet_with_real_tools():
    # Default test env has the NullProvider → specialists + fact sheet (P4).
    r = client.post("/api/findings/F-CONV-07/investigate")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["findingId"] == "F-CONV-07"
    assert body["degraded"] is True
    assert body["brief"]["hypotheses"] == []  # no fabricated synthesis (P4)
    assert body["orchestrator"] == "advisory-v1"
    assert {s["name"] for s in body["specialists"]} >= {
        "telemetry", "knowledge", "compliance"
    }
    assert "validation" in body

    tools_called = [e["tool"] for e in body["evidence"]]
    for tool in ("get_finding", "get_zone_context", "get_recent_telemetry",
                 "get_active_permits", "search_plant_docs", "query_zone_graph"):
        assert tool in tools_called, f"{tool} missing from evidence"

    # Zone context tool must reflect the real twin (B-04 adjacency).
    import json

    zone_step = next(e for e in body["evidence"] if e["tool"] == "get_zone_context")
    zone = json.loads(zone_step["result"])
    assert zone["zoneId"] == "B-04"
    assert "B-03" in zone["adjacentZones"] and "B-05" in zone["adjacentZones"]

    # The run itself is audit-chained.
    kinds = [e["kind"] for e in client.get("/api/audit?limit=10").json()]
    assert "investigation-run" in kinds
