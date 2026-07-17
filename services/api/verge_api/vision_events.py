"""Rolling vision-detection buffer for risk-engine fusion predicates."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from verge_schema.events import VisionDetection

_MAX = 200


def _buf(app_state) -> list[VisionDetection]:
    buf = getattr(app_state, "vision_detections", None)
    if buf is None:
        app_state.vision_detections = []
        buf = app_state.vision_detections
    return buf


def record_vision_detections(app_state, detections: list[dict]) -> list[VisionDetection]:
    """Persist detector plane outputs into the fusion buffer."""
    out: list[VisionDetection] = []
    buf = _buf(app_state)
    now = datetime.now(UTC)
    for d in detections:
        ts_raw = d.get("ts")
        if isinstance(ts_raw, str) and ts_raw:
            try:
                ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            except ValueError:
                ts = now
        else:
            ts = now
        label = str(d.get("label") or "unknown")
        # Map VLM detail phrases into fusion-friendly labels when needed.
        detail = str(d.get("detail") or "").lower()
        if label == "ppe-missing" or "hard-hat" in detail or "hardhat" in detail:
            fusion_label = "ppe-missing"
        else:
            fusion_label = label
        ev = VisionDetection(
            detection_id=f"VD-{uuid.uuid4().hex[:10].upper()}",
            ts=ts,
            camera_id=str(d.get("cameraId") or "cam"),
            zone_id=str(d.get("zoneId") or ""),
            label=fusion_label,
            confidence=float(d.get("confidence") or 0.5),
            frame_uri=d.get("frameUri"),
        )
        if not ev.zone_id:
            continue
        buf.append(ev)
        out.append(ev)
    del buf[:-_MAX]
    return out


def list_vision_detections(app_state, *, limit: int = 50) -> list[VisionDetection]:
    buf = _buf(app_state)
    cap = max(1, min(limit, _MAX))
    return list(reversed(buf[-cap:]))
