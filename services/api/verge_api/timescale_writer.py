"""Optional TimescaleDB sink for high-volume sensor readings (M9/M10).

When TIMESCALE_DSN or VERGE_TIMESCALE_DSN is set, ingested readings are
best-effort copied to the Timescale hypertable defined in deploy/initdb/timescale.sql.
Failures never block the API ingest path.
"""

from __future__ import annotations

import os
from datetime import datetime


def _dsn(env: dict[str, str]) -> str | None:
    return env.get("TIMESCALE_DSN") or env.get("VERGE_TIMESCALE_DSN")


def maybe_write_timescale(event: dict, *, env: dict[str, str] | None = None) -> bool:
    """Insert one canonical reading into Timescale; return True if written."""
    env = env or dict(os.environ)
    dsn = _dsn(env)
    if not dsn or event.get("type") != "reading":
        return False

    sensor_id = event.get("sensorId")
    if not sensor_id:
        return False

    try:
        ts = datetime.fromisoformat(event["ts"])
        value = float(event["value"])
    except (KeyError, TypeError, ValueError):
        return False

    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(dsn, future=True)
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO reading (sensor_id, ts, value, data_quality) "
                    "VALUES (:sensor_id, :ts, :value, 'live')"
                ),
                {"sensor_id": sensor_id, "ts": ts, "value": value},
            )
        return True
    except Exception:
        return False
