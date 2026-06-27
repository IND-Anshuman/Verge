"""Sensor-health classification — each degraded state is detectable."""

from datetime import datetime, timedelta, timezone

from verge_risk.health import classify, is_degraded, ribbon
from verge_schema.core import Reading, Sensor
from verge_schema.enums import DataQuality

NOW = datetime(2025, 1, 13, 6, 44, tzinfo=timezone.utc)


def _sensor(**kw) -> Sensor:
    base = dict(sensor_id="CO-04", kind="gas-co", unit="ppm", zone_id="B-04",
                expected_cadence_s=1.0, plausible_min=0.0, plausible_max=500.0)
    base.update(kw)
    return Sensor(**base)


def _reads(values, *, end=NOW, step_s=1.0):
    n = len(values)
    return [
        Reading(sensor_id="CO-04", ts=end - timedelta(seconds=(n - 1 - i) * step_s), value=v)
        for i, v in enumerate(values)
    ]


def test_missing_when_no_readings() -> None:
    assert classify(_sensor(), [], now=NOW) == DataQuality.MISSING


def test_live_when_fresh_and_varying() -> None:
    q = classify(_sensor(), _reads([10, 11, 12, 13, 14]), now=NOW)
    assert q == DataQuality.LIVE
    assert is_degraded(q) is False


def test_stale_when_old() -> None:
    old = _reads([10, 11, 12, 13, 14], end=NOW - timedelta(seconds=60))
    assert classify(_sensor(), old, now=NOW) == DataQuality.STALE


def test_stuck_at_value() -> None:
    assert classify(_sensor(), _reads([42, 42, 42, 42, 42]), now=NOW) == DataQuality.STUCK_AT_VALUE


def test_out_of_range() -> None:
    assert classify(_sensor(), _reads([10, 11, 12, 13, 9999]), now=NOW) == DataQuality.OUT_OF_RANGE


def test_clock_skew() -> None:
    future = _reads([10, 11, 12, 13, 14], end=NOW + timedelta(seconds=30))
    assert classify(_sensor(), future, now=NOW) == DataQuality.CLOCK_SKEWED


def test_ribbon_text() -> None:
    counts = {DataQuality.LIVE: 847, DataQuality.STALE: 12, DataQuality.STUCK_AT_VALUE: 3}
    assert ribbon(counts) == "847 sensors live · 12 stale · 3 suspect · 0 offline"
