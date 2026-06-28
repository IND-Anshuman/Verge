"""Scenario model: a deterministic plant that drifts toward a convergence.

Replaces VesperGrid's Gazebo/ROS2 theater (spec §12) with a high-fidelity event
stream — no 3D world, no drone animation. Same canonical events the edge gateway
ingests, so sims and production share one wire format.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta


@dataclass
class SensorSpec:
    sensor_id: str
    kind: str
    unit: str
    zone_id: str
    start: float
    drift_per_min: float
    accel: float = 0.0  # quadratic term kicking in late
    accel_after_min: float = 999.0
    stale_from_min: float | None = None  # inject a stale gap (sensor-health plane)
    stale_to_min: float | None = None

    def value(self, m: float) -> float:
        v = self.start + self.drift_per_min * m
        if m > self.accel_after_min:
            v += self.accel * (m - self.accel_after_min) ** 2
        return round(v, 2)

    def is_stale(self, m: float) -> bool:
        return (
            self.stale_from_min is not None
            and self.stale_to_min is not None
            and self.stale_from_min <= m < self.stale_to_min
        )


@dataclass
class Scenario:
    name: str
    t0: datetime
    duration_min: float
    sensors: list[SensorSpec]
    permit_at_min: float | None = None
    permit: dict = field(default_factory=dict)
    # Multiple permits for SIMOPS scenarios; each dict carries atMin (+ optional
    # durationMin) plus permitId/kind/zoneId. Takes precedence over permit_at_min.
    permits: list[dict] | None = None
    changeover: tuple[float, float] | None = None  # (start_min, end_min)
    step_s: float = 30.0

    def _permit_specs(self) -> list[dict]:
        if self.permits:
            return self.permits
        if self.permit_at_min is not None:
            return [{"atMin": self.permit_at_min, **self.permit}]
        return []

    def events(self) -> Iterator[dict]:
        for p in self._permit_specs():
            at = float(p["atMin"])
            dur = float(p.get("durationMin", self.duration_min + 30 - at))
            t = self.t0 + timedelta(minutes=at)
            body = {k: v for k, v in p.items() if k not in ("atMin", "durationMin")}
            yield {"type": "permit", "ts": t.isoformat(), **body,
                   "validFrom": t.isoformat(),
                   "validTo": (t + timedelta(minutes=dur)).isoformat()}
        if self.changeover:
            s, e = self.changeover
            yield {"type": "shift", "ts": (self.t0 + timedelta(minutes=s)).isoformat(),
                   "event": "changeover-start", "zoneId": self.permit.get("zoneId", "B-04")}
            yield {"type": "shift", "ts": (self.t0 + timedelta(minutes=e)).isoformat(),
                   "event": "changeover-end", "zoneId": self.permit.get("zoneId", "B-04")}

        steps = int(self.duration_min * 60 / self.step_s) + 1
        for i in range(steps):
            m = i * self.step_s / 60.0
            ts = (self.t0 + timedelta(seconds=i * self.step_s)).isoformat()
            for s in self.sensors:
                if s.is_stale(m):
                    continue
                yield {"type": "reading", "ts": ts, "sensorId": s.sensor_id,
                       "kind": s.kind, "unit": s.unit, "zoneId": s.zone_id, "value": s.value(m)}


def vizag_like() -> Scenario:
    """The demo scenario: hot-work + rising LEL during changeover in B-04."""
    return Scenario(
        name="vizag-like",
        t0=datetime(2025, 1, 13, 6, 30, tzinfo=UTC),
        duration_min=40.0,
        sensors=[
            SensorSpec("LEL-04", "gas-lel", "%LEL", "B-04", start=80.0, drift_per_min=0.45,
                       accel=0.06, accel_after_min=27.0, stale_from_min=8.0, stale_to_min=12.0),
            SensorSpec("CO-04", "gas-co", "ppm", "B-04", start=38.0, drift_per_min=0.32),
        ],
        permit_at_min=10.0,
        permit={"permitId": "PW-2025-0142", "kind": "hot-work", "zoneId": "B-04",
                "equipmentId": "charging-car-hydraulics"},
        changeover=(12.0, 30.0),
    )


def simops_demo() -> Scenario:
    """A SIMOPS conflict: a hot-work permit in B-04 and a confined-space entry in
    adjacent B-05, overlapping in time. No single gas reading is alarming — the
    risk is the *combination* of the two permits in adjacent zones."""
    return Scenario(
        name="simops-demo",
        t0=datetime(2025, 2, 1, 8, 0, tzinfo=UTC),
        duration_min=20.0,
        sensors=[
            SensorSpec("LEL-04", "gas-lel", "%LEL", "B-04", start=40.0, drift_per_min=0.1),
            SensorSpec("LEL-05", "gas-lel", "%LEL", "B-05", start=42.0, drift_per_min=0.1),
        ],
        permits=[
            {"atMin": 2.0, "permitId": "PW-HW-21", "kind": "hot-work", "zoneId": "B-04",
             "equipmentId": "charging-car-hydraulics"},
            {"atMin": 5.0, "permitId": "PW-CS-22", "kind": "confined-space", "zoneId": "B-05",
             "equipmentId": "vessel-V-7"},
        ],
    )


SCENARIOS = {"vizag-like": vizag_like, "simops-demo": simops_demo}

