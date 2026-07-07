# verge-contracts

Versioned **data contracts** for canonical events (spec §14 Phase 4 — schema
registry). Everything downstream of the edge plane assumes clean
`reading`/`permit`/`shift` events; this makes that assumption explicit and
checkable, so bad data is rejected at the boundary rather than guessed at (P3).

Dependency-free (no jsonschema) — validates on an air-gapped box (P2). Contracts
are versioned, so the wire format can evolve without a silent break.

```python
from verge_contracts import ContractRegistry

reg = ContractRegistry()
result = reg.validate_event({"type": "reading", "ts": "2025-01-14T06:00:00+00:00",
                             "sensorId": "LEL-04", "kind": "gas-lel", "unit": "%LEL",
                             "zoneId": "B-04", "value": 71.0})
result.valid, result.contract_version   # True, "1.0.0"
```

## CLI

`verge validate` checks a canonical-event JSONL stream — pairs with `verge ingest`:

```bash
verge ingest --demo historian | verge validate
# -> 6/6 events conform (0 invalid)
```

Exit code is non-zero if any event violates its contract, so it drops into CI or
a pre-ingest gate.

## Contracts (v1)

| Event | Required | Optional |
|-------|----------|----------|
| `reading` | `ts, sensorId, kind, unit, zoneId, value` | — |
| `permit` | `ts, permitId, kind, zoneId` | `validFrom, validTo, equipmentId` |
| `shift` | `ts, zoneId, event∈{changeover-start,changeover-end}` | — |

Field types: `str`, `number` (not bool), `bool`, `iso-datetime`.
