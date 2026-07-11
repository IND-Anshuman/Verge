"""PPE / person / zone-intrusion CV detector plane (spec §5 Pillar — vision).

Vision is a **detector plane**, not a narrator: it emits classic-CV detections
(a person without a hard-hat, an intrusion into a restricted zone) that become
one leg — a ``ContributingSignal(kind="frame")`` — of a compound finding. It is
deterministic ML (Ultralytics / RT-DETR on the plant GPU box in production), not
an LLM, so it is allowed in the safety plane (P1). The narrative layer never
enters here.

With no model configured, ``detect`` returns ``degraded=True`` and an empty
detection list; it never fabricates a detection (P4). Three real backends are
provided:

* ``AnnotationDetector`` — replays pre-labeled frame annotations (deterministic;
  the same role the event replay plays for the risk engine — real detections,
  no GPU, reproducible in CI and demos).
* ``ultralytics`` — real CPU inference (YOLOv8n by default; a GPU helps but is
  not required for periodic-sample industrial CCTV use). Detects ``person``
  deterministically; derives ``zone-intrusion`` from the camera's registered
  zone (see ``cameras.py``) rather than pixel-space geometry, since no camera
  calibration data exists in this repo. ``ppe-missing`` has no offline
  purpose-trained classifier available (see ``docs/progress.md`` —
  "IMPORTANT — PPE detection"), so it is inferred via a vision-capable LLM
  (aimlapi) crop classification when one is configured, tagged
  ``inferred_by="vlm"`` so it is never confused with a calibrated reading, and
  simply absent (not fabricated, not guessed) when no LLM is reachable.
  Lazily imports ``ultralytics``/``PIL``; degrades to the stub if either is
  unavailable rather than raising.

Backend selection is env-driven (``VERGE_VISION_*``), mirroring the memory/voice
providers so the whole intelligence layer degrades the same way.
"""

from __future__ import annotations

import base64
import io
import json
import math
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol, runtime_checkable

from verge_schema.findings import ContributingSignal

from .cameras import CameraZone, camera_registry_from_env

SAMPLES_DIR = Path(__file__).parent / "samples"

# Detection labels the plane emits. Kept small and stable — a schema of sorts.
PERSON = "person"
PPE_MISSING = "ppe-missing"
ZONE_INTRUSION = "zone-intrusion"
LABELS: frozenset[str] = frozenset({PERSON, PPE_MISSING, ZONE_INTRUSION})


@dataclass(frozen=True)
class Detection:
    label: str
    zone_id: str
    confidence: float
    camera_id: str
    ts: datetime | None = None
    detail: str = ""  # e.g. "no hard-hat", "restricted zone"
    bbox: tuple[float, float, float, float] | None = None  # normalized x,y,w,h
    # None for a calibrated/deterministic detection. "vlm" marks a detection
    # inferred by a vision-language model rather than a purpose-trained
    # classifier (lower precision, requires cloud reachability) -- the audit
    # trail must always be able to tell these apart (P3/P4).
    inferred_by: str | None = None

    def summary(self) -> str:
        base = {
            PERSON: "person detected",
            PPE_MISSING: "PPE missing",
            ZONE_INTRUSION: "zone intrusion",
        }.get(self.label, self.label)
        where = f" in {self.zone_id}" if self.zone_id else ""
        why = f" ({self.detail})" if self.detail else ""
        return f"{base}{why}{where}"

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "zoneId": self.zone_id,
            "confidence": round(self.confidence, 4),
            "cameraId": self.camera_id,
            "ts": self.ts.isoformat() if self.ts else None,
            "detail": self.detail,
            "bbox": list(self.bbox) if self.bbox else None,
            "inferredBy": self.inferred_by,
        }


@dataclass
class VisionResult:
    camera_id: str
    detections: list[Detection] = field(default_factory=list)
    degraded: bool = False
    reason: str = ""
    backend: str = "stub"

    def to_dict(self) -> dict:
        return {
            "cameraId": self.camera_id,
            "detections": [d.to_dict() for d in self.detections],
            "degraded": self.degraded,
            "reason": self.reason,
            "backend": self.backend,
        }


@runtime_checkable
class VisionDetector(Protocol):
    backend: str

    def detect(
        self, camera_id: str, frame_id: str | None = None, image: bytes | None = None
    ) -> VisionResult: ...


class StubDetector:
    """The honest default: no model, no detections, ``degraded=True`` (P4)."""

    backend = "stub"

    def __init__(self, reason: str = "vision disabled (no model configured)") -> None:
        self._reason = reason

    def detect(
        self, camera_id: str, frame_id: str | None = None, image: bytes | None = None
    ) -> VisionResult:
        return VisionResult(camera_id=camera_id, degraded=True, reason=self._reason)


class AnnotationDetector:
    """Deterministic replay of pre-labeled frame annotations (no GPU required).

    Annotations are ``{camera_id: [detection, ...]}``. Each detection dict may
    carry ``frameId`` so a specific frame can be requested; omitting ``frame_id``
    returns every detection for the camera.
    """

    backend = "annotations"

    def __init__(self, annotations: Mapping[str, list[dict]]) -> None:
        self._ann = dict(annotations)

    def detect(
        self, camera_id: str, frame_id: str | None = None, image: bytes | None = None
    ) -> VisionResult:
        # `image` is accepted for protocol parity with the real backend but
        # unused here -- replay is keyed by camera/frame id, not pixels.
        # A detection with no frameId is a camera-wide detection (matches any
        # requested frame); a frame-scoped one matches only its own frame.
        raw = self._ann.get(camera_id, [])
        dets: list[Detection] = []
        skipped = 0
        for d in raw:
            if frame_id is not None and d.get("frameId") not in (None, frame_id):
                continue
            if d.get("label") not in LABELS:
                continue
            det = self._parse_detection(d, camera_id)
            if det is None:
                skipped += 1  # malformed annotation — drop, never fabricate (P4)
            else:
                dets.append(det)
        reason = f"{skipped} malformed annotation(s) skipped" if skipped else ""
        return VisionResult(camera_id=camera_id, detections=dets,
                            backend=self.backend, reason=reason)

    @staticmethod
    def _parse_detection(d: dict, camera_id: str) -> Detection | None:
        """Build one Detection, tolerating malformed fields (returns None)."""
        try:
            confidence = float(d.get("confidence", 0.0))
            if not math.isfinite(confidence):
                return None
            ts_raw = d.get("ts")
            ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00")) if ts_raw else None
            bbox = d.get("bbox")
            if bbox is not None:
                bbox = tuple(float(x) for x in bbox)
                if len(bbox) != 4:
                    bbox = None
            return Detection(
                label=d["label"],
                zone_id=d.get("zoneId", ""),
                confidence=confidence,
                camera_id=camera_id,
                ts=ts,
                detail=d.get("detail", ""),
                bbox=bbox,
            )
        except (ValueError, TypeError, AttributeError):
            return None


def load_annotations(path: str | Path) -> dict[str, list[dict]]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


_PPE_SYSTEM_PROMPT = (
    "You inspect one cropped photo of a single worker on an industrial site. "
    "Reply with exactly one word: compliant, missing, or uncertain. "
    "'missing' means the worker is clearly NOT wearing a hard hat and/or a "
    "hi-vis vest. If the crop is blurry, cropped-off, or ambiguous in any way, "
    "reply uncertain. Never guess -- an uncertain answer is always safe."
)


@dataclass(frozen=True)
class _PpeVerdict:
    missing: bool
    detail: str


def _classify_ppe_crop(llm, crop_jpeg: bytes, *, model: str | None) -> _PpeVerdict | None:
    """One VLM call per person crop. Returns None on any degrade (P4 — never
    fabricate): no provider, unreachable, or an answer that isn't a clear
    'missing' all count as *no signal*, not a detection."""
    if llm is None:
        return None
    from verge_llm import Message

    b64 = base64.b64encode(crop_jpeg).decode("ascii")
    messages = [
        Message(role="system", content=_PPE_SYSTEM_PROMPT),
        Message(
            role="user",
            content=[
                {"type": "text", "text": "Is this worker's PPE (hard hat, hi-vis vest) compliant?"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
            ],
        ),
    ]
    completion = llm.complete(messages, model=model, max_tokens=8)
    if completion.degraded:
        return None
    answer = completion.text.strip().lower()
    if "missing" not in answer:
        return None  # "compliant" or "uncertain" -> no signal
    return _PpeVerdict(
        missing=True,
        detail="hard-hat/vest missing (VLM-inferred — verify before acting)",
    )


class UltralyticsDetector:
    """Real CPU person detection (YOLOv8n by default) + camera-zone-derived
    zone-intrusion + VLM-inferred PPE compliance.

    PPE-missing has no offline purpose-trained classifier available in this
    repo (see ``docs/progress.md`` — "IMPORTANT — PPE detection"); this
    backend asks a vision-capable LLM per detected person as a real,
    working stand-in, tagged ``inferred_by="vlm"`` and only ever emitted on a
    clear "missing" answer -- degraded LLM or an ambiguous answer both mean
    *no detection*, never a guess presented as fact (P4).
    """

    backend = "ultralytics"

    def __init__(
        self,
        *,
        model_path: str = "yolov8n.pt",
        cameras: Mapping[str, CameraZone] | None = None,
        llm=None,
        vision_model: str | None = None,
        min_confidence: float = 0.45,
        model=None,
    ) -> None:
        self._model_path = model_path
        self._cameras = dict(cameras or {})
        self._llm = llm
        self._vision_model = vision_model
        self._min_confidence = min_confidence
        self._model = model  # injectable for tests; lazy-loaded otherwise

    def _load_model(self):
        if self._model is None:
            from ultralytics import YOLO  # heavy import; only paid when reached

            self._model = YOLO(self._model_path)
        return self._model

    def detect(
        self, camera_id: str, frame_id: str | None = None, image: bytes | None = None
    ) -> VisionResult:
        if not image:
            return VisionResult(
                camera_id=camera_id, degraded=True, backend=self.backend,
                reason="ultralytics backend requires an image frame",
            )
        try:
            from PIL import Image

            pil_image = Image.open(io.BytesIO(image)).convert("RGB")
        except Exception as exc:  # noqa: BLE001 - any bad/corrupt frame degrades
            return VisionResult(
                camera_id=camera_id, degraded=True, backend=self.backend,
                reason=f"invalid image frame: {type(exc).__name__}",
            )

        try:
            model = self._load_model()
            results = model.predict(pil_image, verbose=False)
        except Exception as exc:  # noqa: BLE001 - model/runtime failure degrades
            return VisionResult(
                camera_id=camera_id, degraded=True, backend=self.backend,
                reason=f"ultralytics unavailable: {type(exc).__name__}: {exc}",
            )

        cam = self._cameras.get(camera_id)
        zone_id = cam.zone_id if cam else ""
        restricted = cam.restricted if cam else False
        ts = datetime.now(UTC)
        width, height = pil_image.size

        detections: list[Detection] = []
        for r in results:
            for box in getattr(r, "boxes", None) or []:
                if self._label_of(model, box) != PERSON:
                    continue
                confidence = float(box.conf[0])
                if confidence < self._min_confidence:
                    continue
                xyxy = [float(v) for v in box.xyxy[0].tolist()]
                bbox = self._normalize_bbox(xyxy, width, height)

                detections.append(Detection(
                    label=PERSON, zone_id=zone_id, confidence=confidence,
                    camera_id=camera_id, ts=ts, bbox=bbox,
                ))
                if restricted:
                    detections.append(Detection(
                        label=ZONE_INTRUSION, zone_id=zone_id, confidence=confidence,
                        camera_id=camera_id, ts=ts, bbox=bbox,
                        detail=f"person in restricted zone {zone_id}",
                    ))
                verdict = self._check_ppe(pil_image, xyxy)
                if verdict is not None:
                    detections.append(Detection(
                        label=PPE_MISSING, zone_id=zone_id, confidence=confidence,
                        camera_id=camera_id, ts=ts, bbox=bbox,
                        detail=verdict.detail, inferred_by="vlm",
                    ))

        return VisionResult(camera_id=camera_id, detections=detections, backend=self.backend)

    @staticmethod
    def _label_of(model, box) -> str:
        names = getattr(model, "names", None) or {}
        return str(names.get(int(box.cls[0]), "")).lower()

    @staticmethod
    def _normalize_bbox(
        xyxy: list[float], width: int, height: int
    ) -> tuple[float, float, float, float] | None:
        if not width or not height:
            return None
        x0, y0, x1, y1 = xyxy
        return (x0 / width, y0 / height, (x1 - x0) / width, (y1 - y0) / height)

    def _check_ppe(self, pil_image, xyxy: list[float]) -> _PpeVerdict | None:
        if self._llm is None:
            return None
        try:
            x0, y0, x1, y1 = xyxy
            pad = 8
            crop = pil_image.crop((
                max(0, x0 - pad), max(0, y0 - pad),
                min(pil_image.width, x1 + pad), min(pil_image.height, y1 + pad),
            ))
            buf = io.BytesIO()
            crop.save(buf, format="JPEG")
        except Exception:  # noqa: BLE001 - a bad crop just skips the PPE check
            return None
        return _classify_ppe_crop(self._llm, buf.getvalue(), model=self._vision_model)


def _ultralytics_detector(env: Mapping[str, str]) -> VisionDetector:
    """Build the real detector; degrade to the stub if ultralytics is absent."""
    try:
        import ultralytics  # noqa: F401
    except Exception as exc:  # noqa: BLE001 - any import failure degrades
        return StubDetector(reason=f"ultralytics unavailable: {exc}")

    from verge_llm import provider_from_env as llm_provider_from_env

    return UltralyticsDetector(
        model_path=env.get("VERGE_VISION_MODEL", "yolov8n.pt"),
        cameras=camera_registry_from_env(env),
        llm=llm_provider_from_env(dict(env)),
        vision_model=env.get("VERGE_LLM_VISION_MODEL"),
    )


def provider_from_env(env: Mapping[str, str] | None = None) -> VisionDetector:
    """Select a detector from ``VERGE_VISION_*``; default is the degraded stub."""
    env = env or os.environ
    if env.get("VERGE_VISION_ENABLED", "").lower() not in ("1", "true", "yes"):
        return StubDetector(reason="vision disabled (VERGE_VISION_ENABLED not set)")
    backend = env.get("VERGE_VISION_BACKEND", "stub").lower()
    if backend == "annotations":
        path = env.get("VERGE_VISION_ANNOTATIONS")
        if not path or not Path(path).exists():
            return StubDetector(reason="annotations backend: file not found")
        # A corrupt/non-dict annotations file must degrade, not crash wiring (P4).
        try:
            ann = load_annotations(path)
            if not isinstance(ann, dict):
                raise ValueError("annotations must be a JSON object keyed by camera id")
            return AnnotationDetector(ann)
        except (ValueError, OSError) as exc:
            return StubDetector(reason=f"annotations backend: unreadable/invalid ({exc})")
    if backend == "ultralytics":
        return _ultralytics_detector(env)
    return StubDetector(reason=f"unknown backend '{backend}'")


def to_contributing_signals(result: VisionResult) -> list[ContributingSignal]:
    """Convert detections into finding lineage legs (``kind="frame"``, P3)."""
    return [
        ContributingSignal(
            kind="frame",
            ref_id=f"{d.camera_id}:{d.label}",
            summary=d.summary(),
            ts=d.ts,
        )
        for d in result.detections
    ]
