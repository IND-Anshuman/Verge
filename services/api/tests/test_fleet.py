"""Fleet summary aggregates live findings by plant."""

from fastapi.testclient import TestClient
from verge_api.main import app

client = TestClient(app)


def test_fleet_summary_lists_all_plants() -> None:
    r = client.get("/api/fleet/summary")
    assert r.status_code == 200
    body = r.json()
    ids = {p["plantId"] for p in body["plants"]}
    assert ids == {"PLT-VIZAG", "PLT-JAIPUR", "PLT-TEXAS"}
    vizag = next(p for p in body["plants"] if p["plantId"] == "PLT-VIZAG")
    assert vizag["activeRisks"] >= 1
    assert vizag["sensorHealth"] is not None
    assert vizag["measured"]["activeRisks"] is True
    # Unmeasured fleet KPIs stay null (truth gate) — never ship baseline fiction.
    assert vizag["trir"] is None
    assert vizag["alertFatigueRate"] is None
    assert vizag["measured"]["trir"] is False
    assert vizag.get("connected") is True
