from fastapi.testclient import TestClient
from verge_api.main import app


def test_voice_languages_lists_melia_catalog() -> None:
    client = TestClient(app)
    body = client.get("/api/voice/languages").json()
    assert body["model"] == "melia-1"
    assert body["count"] >= 40
    codes = {row["code"] for row in body["languages"]}
    assert {"en", "hi", "ta"}.issubset(codes)
    assert "te" not in codes
    unsupported = {row["code"] for row in body["unsupportedPlantRequests"]}
    assert "te" in unsupported and "kn" in unsupported
