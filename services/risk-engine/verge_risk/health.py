"""Sensor-health plane (spec §4.7).

Deterministic per-sensor classification. Verge tells the plant when it *cannot
see*; findings that rest on degraded data are down-weighted and flagged. This is
what makes P4 (honest uncertainty) a measurement rather than an aspiration.
"""

from __future__ import annotations

from datetime import datetime

from verge_schema.core import Reading, Sensor
from verge_schema.enums import DataQuality

# Tunables (overridable per zone/shift via the Rules DSL in production).
STALE_CADENCE_MULT = 3.0  # stale if no reading within 3x expected cadence
STUCK_WINDOW = 5  # last N readings...
STUCK_EPSILON = 1e-6  # ...all within epsilon => stuck-at-value
CLOCK_SKEW_S = 5.0  # reading ts vs plant time drift tolerance


def classify(
    sensor: Sensor,
    recent: list[Reading],
    *,
    now: datetime,
    plant_time: datetime | None = None,
) -> DataQuality:
    """Classify a sensor from its recent readings (ascending by ts)."""
    if not recent:
        return DataQuality.MISSING

    latest = recent[-1]
    plant_time = plant_time or now

    # clock skew: the reading claims a time AHEAD of the plant clock (a past-dated
    # timestamp is just latency, handled by the staleness check below).
    skew_ahead = (latest.ts - plant_time).total_seconds()
    if skew_ahead > CLOCK_SKEW_S:
        return DataQuality.CLOCK_SKEWED

    # stale: nothing recent enough
    age_s = (now - latest.ts).total_seconds()
    if age_s > STALE_CADENCE_MULT * sensor.expected_cadence_s:
        return DataQuality.STALE

    # out of range: physically implausible
    if sensor.plausible_min is not None and latest.value < sensor.plausible_min:
        return DataQuality.OUT_OF_RANGE
    if sensor.plausible_max is not None and latest.value > sensor.plausible_max:
        return DataQuality.OUT_OF_RANGE

    # stuck-at-value: last N readings identical (within epsilon)
    if len(recent) >= STUCK_WINDOW:
        window = recent[-STUCK_WINDOW:]
        lo = min(r.value for r in window)
        hi = max(r.value for r in window)
        if hi - lo <= STUCK_EPSILON:
            return DataQuality.STUCK_AT_VALUE

    return DataQuality.LIVE


def is_degraded(q: DataQuality) -> bool:
    return q is not DataQuality.LIVE


def ribbon(counts: dict[DataQuality, int]) -> str:
    """The always-visible operator ribbon (spec §4.7)."""
    live = counts.get(DataQuality.LIVE, 0)
    stale = counts.get(DataQuality.STALE, 0)
    suspect = (
        counts.get(DataQuality.STUCK_AT_VALUE, 0)
        + counts.get(DataQuality.OUT_OF_RANGE, 0)
        + counts.get(DataQuality.CLOCK_SKEWED, 0)
    )
    offline = counts.get(DataQuality.MISSING, 0)
    return f"{live} sensors live · {stale} stale · {suspect} suspect · {offline} offline"
