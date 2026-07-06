"""Finding telemetry route tests."""

from fastapi.testclient import TestClient
from verge_api.main import app

client = TestClient(app)


def test_finding_telemetry_returns_series_for_convergence() -> None:
    r = client.get("/api/findings/F-CONV-07/telemetry")
    assert r.status_code == 200
    body = r.json()
    assert body["findingId"] == "F-CONV-07"
    assert body["zoneId"] == "B-04"
    assert body["degraded"] is False
    assert len(body["series"]) >= 1
    lel = next(s for s in body["series"] if s["sensorId"] == "LEL-04")
    assert len(lel["points"]) >= 10
    assert lel["threshold"] == 100.0


def test_reading_ingest_appends_to_telemetry() -> None:
    payload = {
        "ts": "2025-01-13T07:00:00+00:00",
        "sensorId": "LEL-TEST",
        "kind": "gas-lel",
        "unit": "%LEL",
        "zoneId": "B-99",
        "value": 42.0,
    }
    assert client.post("/api/readings/ingest", json=payload).status_code == 200


def test_finding_telemetry_unknown_finding_is_404() -> None:
    assert client.get("/api/findings/NOPE/telemetry").status_code == 404
