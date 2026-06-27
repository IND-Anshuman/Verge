# deploy/

Single-box dev / hackathon stack (spec §8). Production is the same services on
K3s in the OT-DMZ with the LLM provider swapped to on-prem Ollama/vLLM and no
egress.

```bash
cp .env.example .env      # from repo root; or edit deploy/.env
make up                   # docker compose up -d
make logs                 # tail
make down
```

| Service | Port | Purpose |
|---------|------|---------|
| Redpanda | 19092 | canonical event spine (Kafka API) |
| Postgres + PostGIS | 5432 | permits, plant layout, geo zones, audit |
| TimescaleDB | 5433 | sensor time-series, rate-of-rise features |
| Neo4j | 7474/7687 | compound-risk knowledge graph |
| MinIO | 9000/9001 | evidence packs, frames, reports |
| Redis | 6379 | jobs / SSE fan-out |
| Keycloak | 8080 | OIDC / RBAC |

`initdb/` runs once on first volume create: PostGIS extension + core tables,
Timescale hypertable + 1-minute continuous aggregate. The `audit_entry` table is
append-only by convention (P6) — application code never issues UPDATE/DELETE
against it.
