"""Lightweight counters surfaced on /metrics (audit §10 observability)."""

from __future__ import annotations

contract_rejections = 0
timescale_write_failures = 0
timescale_writes = 0
stream_dlq_events = 0
