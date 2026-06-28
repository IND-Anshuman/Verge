-- Verge relational + geo plane (permits, plant layout, zones).
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS zone (
    zone_id      TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    purdue_level INT,
    geom         GEOMETRY(Polygon, 4326)
);

CREATE TABLE IF NOT EXISTS equipment (
    equipment_id TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    kind         TEXT NOT NULL,
    zone_id      TEXT REFERENCES zone(zone_id)
);

CREATE TABLE IF NOT EXISTS permit (
    permit_id    TEXT PRIMARY KEY,
    kind         TEXT NOT NULL,
    zone_id      TEXT REFERENCES zone(zone_id),
    equipment_id TEXT REFERENCES equipment(equipment_id),
    valid_from   TIMESTAMPTZ NOT NULL,
    valid_to     TIMESTAMPTZ NOT NULL,
    status       TEXT NOT NULL DEFAULT 'open'
);

-- The findings / feedback / audit_entry / sensor_health tables are owned and
-- created by the API's durable store (verge_api/db.py, SQLAlchemy) so the same
-- schema runs on Postgres and SQLite. The audit_entry table is append-only by
-- design (P6) — application code never issues UPDATE/DELETE against it.
