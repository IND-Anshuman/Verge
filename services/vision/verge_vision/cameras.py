"""Camera -> zone registry for the vision plane (spec §5).

CCTV placement is fixed at commissioning time — each camera covers one zone.
This is a deliberately simple, explicit mapping, not pixel-space geometry:
this repo has no camera calibration/homography data, so a real detection's
zone comes from *which camera* saw it, the same way an annotation's zoneId
is a flat field today (`AnnotationDetector`). A person detected by a camera
assigned to a ``restricted`` zone is therefore a real, computed
zone-intrusion signal — not a guess.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

SAMPLES_DIR = Path(__file__).parent / "samples"
DEMO_CAMERAS = SAMPLES_DIR / "vizag-cameras.json"


@dataclass(frozen=True)
class CameraZone:
    zone_id: str
    restricted: bool = False


def load_camera_registry(path: str | Path) -> dict[str, CameraZone]:
    """Parse a ``{cameraId: {zoneId, restricted}}`` JSON file.

    Tolerant of malformed entries (P4 — a bad row is dropped, never crashes
    wiring); raises only if the file itself can't be read or isn't a JSON
    object, so callers can decide how to degrade.
    """
    raw = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(raw, dict):
        raise ValueError("camera registry must be a JSON object keyed by camera id")
    out: dict[str, CameraZone] = {}
    for camera_id, entry in raw.items():
        if not isinstance(entry, dict) or not entry.get("zoneId"):
            continue
        out[camera_id] = CameraZone(
            zone_id=str(entry["zoneId"]),
            restricted=bool(entry.get("restricted", False)),
        )
    return out


def camera_registry_from_env(env: Mapping[str, str]) -> dict[str, CameraZone]:
    """``VERGE_VISION_CAMERAS`` if set and readable, else the bundled demo registry."""
    path = env.get("VERGE_VISION_CAMERAS")
    if path:
        try:
            return load_camera_registry(path)
        except (ValueError, OSError):
            pass  # falls through to the demo registry rather than raising
    if DEMO_CAMERAS.exists():
        try:
            return load_camera_registry(DEMO_CAMERAS)
        except (ValueError, OSError):
            return {}
    return {}
