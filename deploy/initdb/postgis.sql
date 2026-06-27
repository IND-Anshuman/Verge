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

-- Append-only, hash-chained audit (P6). No UPDATE/DELETE in application code.
CREATE TABLE IF NOT EXISTS audit_entry (
    entry_id   TEXT PRIMARY KEY,
    ts         TIMESTAMPTZ NOT NULL,
    actor      TEXT NOT NULL,
    kind       TEXT NOT NULL,
    payload    JSONB NOT NULL,
    hash       TEXT NOT NULL,
    prev_hash  TEXT
);
CREATE INDEX IF NOT EXISTS audit_entry_ts_idx ON audit_entry (ts);
