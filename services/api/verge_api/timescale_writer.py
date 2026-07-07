"""Optional TimescaleDB sink for high-volume sensor readings (M9/M10).

When TIMESCALE_DSN or VERGE_TIMESCALE_DSN is set, ingested readings are
copied to the Timescale hypertable defined in deploy/initdb/timescale.sql.
Failures never block the API ingest path but are counted for ops visibility.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)


def _dsn(env: dict[str, str]) -> str | None:
    return env.get("TIMESCALE_DSN") or env.get("VERGE_TIMESCALE_DSN")


def timescale_status(*, env: dict[str, str] | None = None) -> dict:
    """Probe Timescale when configured; never raises."""
    env = env or dict(os.environ)
    dsn = _dsn(env)
    if not dsn:
        return {"configured": False, "degraded": False, "readings": 0}
    try:
        from sqlalchemy import create_engine, text

        with create_engine(dsn, future=True).connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM reading")).scalar_one()
        return {"configured": True, "degraded": False, "readings": int(count)}
    except Exception as exc:
        return {
            "configured": True,
            "degraded": True,
            "readings": 0,
            "reason": type(exc).__name__,
        }


def query_sensor_series(
    sensor_ids: list[str],
    *,
    limit: int = 120,
    env: dict[str, str] | None = None,
) -> dict[str, list[dict]]:
    """Load recent reading points from Timescale for telemetry charts."""
    env = env or dict(os.environ)
    dsn = _dsn(env)
    if not dsn or not sensor_ids:
        return {}
    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(dsn, future=True)
        out: dict[str, list[dict]] = {}
        stmt = text(
            "SELECT ts, value FROM reading WHERE sensor_id = :sensor_id "
            "ORDER BY ts DESC LIMIT :limit"
        )
        with engine.connect() as conn:
            for sid in sensor_ids:
                rows = conn.execute(stmt, {"sensor_id": sid, "limit": limit}).all()
                if not rows:
                    continue
                points = [
                    {"ts": r[0].isoformat(), "value": float(r[1])}
                    for r in reversed(rows)
                ]
                out[sid] = points
        return out
    except Exception:
        return {}


def maybe_write_timescale(event: dict, *, env: dict[str, str] | None = None) -> dict:
    """Insert one canonical reading into Timescale; return structured result."""
    env = env or dict(os.environ)
    dsn = _dsn(env)
    if not dsn:
        return {"configured": False, "written": False}
    if event.get("type") != "reading":
        return {"configured": True, "written": False, "reason": "not-reading"}

    sensor_id = event.get("sensorId")
    if not sensor_id:
        return {"configured": True, "written": False, "reason": "missing-sensorId"}

    try:
        ts = datetime.fromisoformat(event["ts"])
        value = float(event["value"])
    except (KeyError, TypeError, ValueError) as exc:
        return {"configured": True, "written": False, "reason": type(exc).__name__}

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
        return {"configured": True, "written": True}
    except Exception as exc:
        logger.warning("timescale write failed for %s: %s", sensor_id, exc)
        return {"configured": True, "written": False, "reason": type(exc).__name__}
