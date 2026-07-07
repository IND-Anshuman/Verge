"""Reading ingest contract enforcement."""

from __future__ import annotations

from fastapi.testclient import TestClient
from verge_api.main import app

client = TestClient(app)


def test_readings_ingest_rejects_invalid_contract() -> None:
    r = client.post("/api/readings/ingest", json={
        "type": "reading",
        "sensorId": "LEL-04",
        "value": "not-a-number",
    })
    assert r.status_code == 422


def test_readings_ingest_enriches_valid_event() -> None:
    r = client.post("/api/readings/ingest", json={
        "type": "reading",
        "ts": "2025-01-13T06:30:00+00:00",
        "sensorId": "LEL-04",
        "kind": "gas-lel",
        "unit": "%LEL",
        "zoneId": "B-04",
        "value": 12.0,
    })
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["eventId"]
