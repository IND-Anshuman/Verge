"""API contract: lifecycle is enforced, feedback measures FPR, audit verifies."""

from fastapi.testclient import TestClient
from verge_api.main import app

client = TestClient(app)


def test_health_reports_audit_and_llm() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["audit"]["verified"] is True
    assert "provider" in body["llm"]


def test_findings_seeded_in_multiple_states() -> None:
    states = {f["state"] for f in client.get("/api/findings").json()}
    assert {"new", "acknowledged", "snoozed", "escalated", "resolved"} <= states


def test_legal_transition_updates_and_audits() -> None:
    before = len(client.get("/api/audit?limit=999").json())
    r = client.post(
        "/api/findings/F-NEW-01/transition", json={"to": "acknowledged", "actor": "maya"}
    )
    assert r.status_code == 200
    assert r.json()["state"] == "acknowledged"
    after = len(client.get("/api/audit?limit=999").json())
    assert after == before + 1
    # audit still verifies after the append
    assert client.get("/health").json()["audit"]["verified"] is True


def test_illegal_transition_is_409() -> None:
    r = client.post("/api/findings/F-RES-01/transition", json={"to": "new", "actor": "maya"})
    assert r.status_code == 409


def test_snooze_without_reason_is_409() -> None:
    r = client.post("/api/findings/F-ACK-02/transition", json={"to": "snoozed", "actor": "maya"})
    assert r.status_code == 409


def test_feedback_drives_fpr() -> None:
    r = client.post("/api/findings/F-CONV-07/feedback", json={"actor": "maya", "verdict": "useful"})
    assert r.status_code == 200
    assert r.json()["fpr"] == 0.0
    client.post("/api/findings/F-NEW-01/feedback",
                json={"actor": "maya", "verdict": "false-alarm", "reasonCode": "noise"})
    assert client.post("/api/findings/F-ACK-01/feedback",
                       json={"actor": "maya", "verdict": "useful"}).json()["fpr"] > 0


def test_ribbon_text() -> None:
    txt = client.get("/api/sensors/ribbon").json()["text"]
    assert "live" in txt and "stale" in txt
