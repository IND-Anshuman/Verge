"""In-memory sensor reading ring buffer for console telemetry charts."""

from __future__ import annotations

import json
from collections import defaultdict, deque
from pathlib import Path

from verge_schema.findings import RiskFinding

REPLAY_SEED = Path(__file__).resolve().parents[3] / "eval/replays/vizag-2025-01/events.jsonl"
MAX_POINTS_PER_SENSOR = 120


class ReadingBuffer:
    """Rolling window of canonical reading events keyed by sensor_id."""

    def __init__(self, max_points: int = MAX_POINTS_PER_SENSOR) -> None:
        self._max = max_points
        self._by_sensor: dict[str, deque[dict]] = defaultdict(deque)

    def ingest(self, event: dict) -> None:
        if event.get("type") != "reading":
            return
        sensor_id = event.get("sensorId")
        if not sensor_id:
            return
        point = {
            "ts": event["ts"],
            "value": float(event["value"]),
            "zoneId": event.get("zoneId"),
            "kind": event.get("kind"),
            "unit": event.get("unit"),
        }
        buf = self._by_sensor[sensor_id]
        buf.append(point)
        while len(buf) > self._max:
            buf.popleft()

    def seed_from_replay(self, path: Path | None = None) -> int:
        path = path or REPLAY_SEED
        if not path.exists():
            return 0
        n = 0
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            event = json.loads(line)
            if event.get("type") == "reading":
                self.ingest(event)
                n += 1
        return n

    def sensor_ids_for_finding(self, finding: RiskFinding) -> list[str]:
        ids: list[str] = []
        seen: set[str] = set()
        for ref in finding.lineage:
            if ref.startswith("reading:"):
                sid = ref.split(":", 1)[1]
                if sid not in seen:
                    seen.add(sid)
                    ids.append(sid)
        for sig in finding.contributing_signals:
            if sig.kind == "reading" and sig.ref_id not in seen:
                seen.add(sig.ref_id)
                ids.append(sig.ref_id)
        if not ids:
            for sid, buf in self._by_sensor.items():
                if buf and buf[-1].get("zoneId") == finding.zone_id:
                    ids.append(sid)
        return ids

    def series_for_finding(
        self,
        finding: RiskFinding,
        *,
        thresholds: dict[str, float] | None = None,
    ) -> dict:
        thresholds = thresholds or {}
        sensor_ids = self.sensor_ids_for_finding(finding)
        series = []
        for sid in sensor_ids:
            points = list(self._by_sensor.get(sid, []))
            if not points:
                continue
            kind = points[-1].get("kind") or "unknown"
            series.append({
                "sensorId": sid,
                "kind": kind,
                "unit": points[-1].get("unit") or "",
                "threshold": thresholds.get(kind),
                "points": points,
            })
        return {
            "findingId": finding.finding_id,
            "zoneId": finding.zone_id,
            "series": series,
            "degraded": len(series) == 0,
            "reason": None if series else "no telemetry for finding sensors",
        }
