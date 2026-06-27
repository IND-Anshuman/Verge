-- Verge time-series plane (sensor readings + lead-time features).
CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS reading (
    sensor_id    TEXT NOT NULL,
    ts           TIMESTAMPTZ NOT NULL,
    value        DOUBLE PRECISION NOT NULL,
    data_quality TEXT NOT NULL DEFAULT 'live'
);

SELECT create_hypertable('reading', 'ts', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS reading_sensor_ts_idx ON reading (sensor_id, ts DESC);

-- Continuous rate-of-rise is the B1 baseline and a forecaster input; a
-- 1-minute bucket keeps the dashboard cheap while the engine reads raw.
CREATE MATERIALIZED VIEW IF NOT EXISTS reading_1m
WITH (timescaledb.continuous) AS
SELECT sensor_id,
       time_bucket('1 minute', ts) AS bucket,
       avg(value) AS avg_value,
       max(value) AS max_value
FROM reading
GROUP BY sensor_id, bucket
WITH NO DATA;
