"""Timescale writer is optional and never raises."""

from verge_api.timescale_writer import maybe_write_timescale


def test_timescale_writer_skips_without_dsn() -> None:
    event = {
        "type": "reading",
        "ts": "2025-01-13T07:00:00+00:00",
        "sensorId": "LEL-04",
        "value": 91.5,
    }
    assert maybe_write_timescale(event, env={}) == {"configured": False, "written": False}
