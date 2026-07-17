"""Vision event ingest for risk fusion."""

from __future__ import annotations

from fastapi.testclient import TestClient
from verge_api.main import app


def test_vision_event_text_ingest() -> None:
    client = TestClient(app)
    app.state.vision_detections = []
    r = client.post(
        "/api/vision/events",
        json={
            "cameraId": "CAM-B04",
            "zoneId": "B-04",
            "label": "ppe-missing",
            "confidence": 0.88,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 1
    assert body["detections"][0]["zoneId"] == "B-04"

    listed = client.get("/api/vision/events").json()
    assert listed["count"] >= 1
