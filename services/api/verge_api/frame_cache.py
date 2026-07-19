"""In-process vision frame bytes for console display (Phase Live Ops).

MinIO may hold the durable copy (s3://…); browsers need an HTTP URL.
We keep a small rolling map of detection_id → JPEG/PNG bytes so
``GET /api/vision/frames/{id}`` can render last annotated stills honestly.
"""

from __future__ import annotations

_MAX_FRAMES = 64


def _map(app_state) -> dict[str, tuple[bytes, str]]:
    m = getattr(app_state, "vision_frame_bytes", None)
    if m is None:
        app_state.vision_frame_bytes = {}
        m = app_state.vision_frame_bytes
    return m


def store_frame(
    app_state,
    detection_id: str,
    image: bytes,
    *,
    content_type: str = "image/jpeg",
) -> str:
    """Store bytes; return the browser-fetchable API path."""
    if not detection_id or not image:
        return ""
    m = _map(app_state)
    m[detection_id] = (image, content_type or "image/jpeg")
    while len(m) > _MAX_FRAMES:
        # Drop oldest insertion order (Py3.7+ dict order).
        oldest = next(iter(m))
        del m[oldest]
    return f"/api/vision/frames/{detection_id}"


def get_frame(app_state, detection_id: str) -> tuple[bytes, str] | None:
    return _map(app_state).get(detection_id)
