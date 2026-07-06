from fastapi.testclient import TestClient
from verge_api.main import app

client = TestClient(app)


def test_evidence_manifest_degrades_without_minio() -> None:
    r = client.get("/api/evidence/EP-TEST")
    assert r.status_code == 200
    body = r.json()
    assert body["packId"] == "EP-TEST"
    assert body["degraded"] is True
    assert "MINIO" in body["reason"]
