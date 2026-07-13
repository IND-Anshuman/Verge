"""Emergency mode: P8 gate, evidence freeze, muster roll-call, stand-down."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient
from verge_api.main import app

client = TestClient(app)


def _worker(worker: str, zone: str, **extra) -> None:
    r = client.post(
        "/api/workers/ingest",
        json={"ts": datetime.now(UTC).isoformat(), "workerId": worker,
              "zoneId": zone, **extra},
    )
    assert r.status_code == 200


def _stand_down_if_active() -> None:
    if client.get("/api/emergency/status").json().get("active"):
        client.post("/api/emergency/stand-down", json={"approvedBy": "test-teardown"})


def test_declare_requires_approver_and_audits_refusal():
    _stand_down_if_active()
    r = client.post("/api/findings/F-CONV-07/emergency/declare", json={})
    assert r.status_code == 403
    kinds = [e["kind"] for e in client.get("/api/audit?limit=5").json()]
    assert "emergency-declare-refused" in kinds


def test_full_emergency_lifecycle():
    _stand_down_if_active()
    _worker("WE-1", "B-04", name="S. Rao", role="welder")
    _worker("WE-2", "B-03")
    _worker("WE-3", "B-01")

    r = client.post(
        "/api/findings/F-CONV-07/emergency/declare", json={"approvedBy": "cro-shift-a"}
    )
    assert r.status_code == 200, r.text
    status = r.json()
    assert status["active"] is True
    assert "B-04" in status["affectedZones"]
    assert status["muster"]["expected"] >= 3
    assert status["evidenceFreeze"]["hash"]
    assert status["evacuation"]["routes"]["B-04"]["route"][0] == "B-04"

    # Frozen evidence is servable and hash-bound.
    frozen = client.get("/api/emergency/evidence").json()
    assert frozen["hash"] == status["evidenceFreeze"]["hash"]
    assert frozen["manifest"]["workerRoster"]

    # A second declaration while active is refused (409).
    r2 = client.post(
        "/api/findings/F-CONV-07/emergency/declare", json={"approvedBy": "someone"}
    )
    assert r2.status_code == 409

    # Roll-call: WE-1 checks in; the rest are missing with last-known zones.
    r3 = client.post(
        "/api/emergency/muster/check-in",
        json={"workerId": "WE-1", "musterId": "MP-WEST", "recordedBy": "gatekeeper"},
    )
    muster = r3.json()["muster"]
    assert any(a["workerId"] == "WE-1" for a in muster["accounted"])
    missing_ids = [m["workerId"] for m in muster["missing"]]
    assert "WE-2" in missing_ids
    we2 = next(m for m in muster["missing"] if m["workerId"] == "WE-2")
    assert we2["lastKnownZone"] == "B-03"

    # Stand-down closes it out and the audit trail has the whole story.
    r4 = client.post("/api/emergency/stand-down", json={"approvedBy": "cro-shift-a"})
    assert r4.status_code == 200
    assert client.get("/api/emergency/status").json()["active"] is False
    kinds = [e["kind"] for e in client.get("/api/audit?limit=20").json()]
    for kind in ("emergency-declared", "muster-check-in", "emergency-stand-down"):
        assert kind in kinds


def test_stand_down_requires_approver():
    _stand_down_if_active()
    _worker("WE-9", "B-04")
    client.post(
        "/api/findings/F-CONV-07/emergency/declare", json={"approvedBy": "cro"}
    )
    assert client.post("/api/emergency/stand-down", json={}).status_code == 403
    client.post("/api/emergency/stand-down", json={"approvedBy": "cro"})
