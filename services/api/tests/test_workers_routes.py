"""Worker location plane API: ingest, roster, and finding exposure."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient
from verge_api.main import app

client = TestClient(app)


def _ingest(worker: str, zone: str, **extra) -> dict:
    body = {
        "ts": datetime.now(UTC).isoformat(),
        "workerId": worker,
        "zoneId": zone,
        **extra,
    }
    r = client.post("/api/workers/ingest", json=body)
    assert r.status_code == 200, r.text
    return r.json()


def test_ingest_and_list_workers():
    _ingest("WT-1", "B-04", name="S. Rao", role="welder", source="sim-rtls")
    _ingest("WT-2", "B-03")
    body = client.get("/api/workers").json()
    ids = [w["workerId"] for w in body["workers"]]
    assert "WT-1" in ids and "WT-2" in ids
    assert body["total"] >= 2
    assert "B-04" in body["byZone"]
    w1 = next(w for w in body["workers"] if w["workerId"] == "WT-1")
    assert w1["name"] == "S. Rao"
    assert w1["stale"] is False


def test_ingest_rejects_contract_violation():
    r = client.post(
        "/api/workers/ingest",
        json={"ts": "not-a-timestamp", "workerId": "WT-9", "zoneId": "B-01"},
    )
    assert r.status_code == 422


def test_finding_exposure_uses_zone_adjacency():
    # Seeded finding F-CONV-07 lives in B-04; B-03/B-05 are adjacent in the twin.
    _ingest("WT-10", "B-04")
    _ingest("WT-11", "B-03")
    _ingest("WT-12", "B-01")
    body = client.get("/api/findings/F-CONV-07/exposure").json()
    assert body["findingId"] == "F-CONV-07"
    in_zone = [w["workerId"] for w in body["inZone"]]
    in_adj = [w["workerId"] for w in body["inAdjacent"]]
    assert "WT-10" in in_zone
    assert "WT-11" in in_adj
    assert "WT-12" not in in_zone + in_adj
    assert body["headcountAtRisk"] >= 2


def test_finding_exposure_404_for_unknown_finding():
    assert client.get("/api/findings/F-NOPE/exposure").status_code == 404
