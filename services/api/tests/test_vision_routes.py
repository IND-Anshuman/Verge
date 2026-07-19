"""Vision API routes: degraded by default, real detections when configured."""

from __future__ import annotations

import io

from fastapi.testclient import TestClient
from PIL import Image
from verge_vision import SAMPLE_ANNOTATIONS, AnnotationDetector, load_annotations
from verge_vision.detect import PERSON, UltralyticsDetector


def _jpeg_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (32, 32), color=(80, 80, 80)).save(buf, format="JPEG")
    return buf.getvalue()


class _FakeBox:
    def __init__(self, cls_id, conf, xyxy):
        self.cls, self.conf, self.xyxy = [cls_id], [conf], [_FakeTensor(xyxy)]


class _FakeTensor:
    def __init__(self, values):
        self._values = values

    def tolist(self):
        return self._values


class _FakeResult:
    def __init__(self, boxes):
        self.boxes = boxes


class _FakeModel:
    names = {0: "person"}

    def predict(self, image, verbose=False):
        return [_FakeResult([_FakeBox(0, 0.9, [1.0, 1.0, 10.0, 20.0])])]


def test_detect_degraded_by_default():
    from verge_api.main import app

    client = TestClient(app)
    r = client.post("/api/vision/detect", json={"cameraId": "CAM-B04"})
    assert r.status_code == 200
    body = r.json()
    # No GPU/model in the default env -> degraded, no fabricated detections.
    assert body["degraded"] is True
    assert body["detections"] == []
    assert body["contributingSignals"] == []


def test_detect_returns_frame_signals_when_backend_configured():
    from verge_api.main import app

    app.state.vision = AnnotationDetector(load_annotations(SAMPLE_ANNOTATIONS))
    try:
        client = TestClient(app)
        body = client.post("/api/vision/detect", json={"cameraId": "CAM-B04"}).json()
        assert body["degraded"] is False
        assert body["detections"]
        signals = body["contributingSignals"]
        assert signals and all(s["kind"] == "frame" for s in signals)
    finally:
        # Restore the degraded default so other tests see the real posture.
        from verge_vision import provider_from_env

        app.state.vision = provider_from_env({})


def test_detect_frame_requires_no_real_ultralytics_install_when_stub():
    """A degraded default backend still answers detect-frame — never a 500."""
    from verge_api.main import app

    client = TestClient(app)
    r = client.post(
        "/api/vision/detect-frame",
        data={"cameraId": "CAM-B04"},
        files={"file": ("frame.jpg", _jpeg_bytes(), "image/jpeg")},
    )
    assert r.status_code == 200
    assert r.json()["degraded"] is True


def test_detect_frame_returns_real_detections_from_an_uploaded_image():
    from verge_api.main import app

    app.state.vision = UltralyticsDetector(model=_FakeModel())
    try:
        client = TestClient(app)
        r = client.post(
            "/api/vision/detect-frame",
            data={"cameraId": "CAM-B04"},
            files={"file": ("frame.jpg", _jpeg_bytes(), "image/jpeg")},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["degraded"] is False
        assert body["backend"] == "ultralytics"
        assert body["detections"][0]["label"] == PERSON
        assert body["contributingSignals"]
    finally:
        from verge_vision import provider_from_env

        app.state.vision = provider_from_env({})


def test_vision_frame_http_cache_serves_bytes():
    """Console Live Ops needs GET /api/vision/frames/{id}, not s3:// only."""
    from verge_api.frame_cache import store_frame
    from verge_api.main import app

    client = TestClient(app)
    jpeg = _jpeg_bytes()
    path = store_frame(app.state, "VD-TESTFRAME01", jpeg)
    assert path == "/api/vision/frames/VD-TESTFRAME01"
    r = client.get(path)
    assert r.status_code == 200
    assert r.content == jpeg
    assert client.get("/api/vision/frames/VD-MISSING").status_code == 404
