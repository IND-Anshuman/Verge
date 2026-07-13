"""CAPA routes: generate, transition gates, audit trail."""

from __future__ import annotations

from fastapi.testclient import TestClient
from verge_api.main import app

client = TestClient(app)


def test_generate_then_idempotent():
    r = client.post("/api/compliance/actions/generate")
    assert r.status_code == 200
    first = r.json()
    listing = client.get("/api/compliance/actions").json()
    assert listing["total"] >= first["count"] > 0

    again = client.post("/api/compliance/actions/generate").json()
    assert again["count"] == 0
    assert "idempotent" in (again["note"] or "")

    kinds = [e["kind"] for e in client.get("/api/audit?limit=10").json()]
    assert "corrective-actions-generated" in kinds


def test_transition_gates_and_audit():
    client.post("/api/compliance/actions/generate")
    action = client.get("/api/compliance/actions").json()["actions"][0]
    aid = action["actionId"]

    # Named actor required.
    r = client.post(f"/api/compliance/actions/{aid}/transition", json={"to": "in-progress"})
    assert r.status_code == 403

    # Illegal jump rejected.
    r = client.post(
        f"/api/compliance/actions/{aid}/transition",
        json={"to": "closed-effective", "actor": "x", "note": "skip"},
    )
    assert r.status_code == 409

    r = client.post(
        f"/api/compliance/actions/{aid}/transition",
        json={"to": "in-progress", "actor": "s.rao"},
    )
    assert r.status_code == 200
    assert r.json()["state"] == "in-progress"

    kinds = [e["kind"] for e in client.get("/api/audit?limit=10").json()]
    assert "corrective-action-transition" in kinds


def test_assign_owner_and_due():
    client.post("/api/compliance/actions/generate")
    actions = client.get("/api/compliance/actions").json()["actions"]
    aid = actions[-1]["actionId"]
    r = client.post(
        f"/api/compliance/actions/{aid}/assign",
        json={"owner": "m.devi", "due": "2026-08-01", "actor": "plant-manager"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["owner"] == "m.devi"
    assert body["due"] == "2026-08-01"


def test_unknown_action_404():
    assert client.get("/api/compliance/actions").status_code == 200
    r = client.post(
        "/api/compliance/actions/CA-NOPE/transition",
        json={"to": "in-progress", "actor": "x"},
    )
    assert r.status_code == 404
