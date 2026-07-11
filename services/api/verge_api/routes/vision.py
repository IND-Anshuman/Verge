"""Vision API — PPE / person / zone-intrusion detections (spec §5).

The detector plane is degraded-by-default: with no GPU/model configured the
endpoint returns ``degraded: true`` and no detections, never a fabricated one
(P4). When an annotation or model backend is configured it returns real
detections plus the ``frame`` contributing signals they map to, so the console
can show vision as one leg of a compound finding (P3).
"""

from __future__ import annotations

from fastapi import APIRouter, File, Form, Request, UploadFile
from pydantic import BaseModel
from verge_vision import to_contributing_signals

router = APIRouter(tags=["vision"])
FRAME_FILE = File(...)
CAMERA_FORM = Form(...)


class DetectBody(BaseModel):
    cameraId: str
    frameId: str | None = None


def _detect_response(detector, camera_id: str, frame_id: str | None, image: bytes | None) -> dict:
    result = detector.detect(camera_id, frame_id, image)
    signals = to_contributing_signals(result)
    return {
        **result.to_dict(),
        "contributingSignals": [s.model_dump(by_alias=True, mode="json") for s in signals],
    }


@router.post("/vision/detect")
def detect(body: DetectBody, request: Request) -> dict:
    """Annotation-replay / metadata-only detection (no real frame required)."""
    return _detect_response(request.app.state.vision, body.cameraId, body.frameId, None)


@router.post("/vision/detect-frame")
async def detect_frame(
    request: Request,
    cameraId: str = CAMERA_FORM,
    file: UploadFile = FRAME_FILE,
) -> dict:
    """Real-frame detection — an uploaded image is run through the configured
    detector (e.g. ``UltralyticsDetector``). This is how live/real CCTV or a
    routed demo clip (``verge vision watch``) reaches the vision plane; the
    stub/annotation backends still degrade or replay exactly as before."""
    image = await file.read()
    return _detect_response(request.app.state.vision, cameraId, None, image)
