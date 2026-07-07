"""Edge autonomy mode: fail-operational local scoring + store-and-forward (P1/P7)."""

from __future__ import annotations

from verge_edge import EdgeAutonomy
from verge_risk import STARTER_RULES, load_rules, run_stream
from verge_twin import load_plant

Z = "B-04"
PERMIT = {"type": "permit", "ts": "2025-01-14T06:00:00+00:00", "permitId": "P1",
          "kind": "hot-work", "zoneId": Z, "validFrom": "2025-01-14T06:00:00+00:00",
          "validTo": "2025-01-14T09:00:00+00:00"}


def _readings() -> list[dict]:
    values = [(0, 60.0), (2, 75.0), (4, 88.0)]
    return [
        {"type": "reading", "ts": f"2025-01-14T06:0{m}:00+00:00", "sensorId": "LEL-04",
         "kind": "gas-lel", "unit": "%LEL", "zoneId": Z, "value": v}
        for m, v in values
    ]


def _real_engine():
    plant = load_plant()
    rules = load_rules(STARTER_RULES)

    def evaluate(events: list[dict]) -> list:
        out: list = []
        run_stream(events, rules, out.append, thresholds=plant.thresholds_by_kind(),
                   window=12, min_confidence=0.0)
        return out

    return evaluate


def test_online_forwards_immediately():
    a = EdgeAutonomy(lambda e: [])
    sent: list[dict] = []
    a.ingest(PERMIT, sent.append)
    assert sent == [PERMIT]
    assert a.buffered == 0 and a.mode == "central"


def test_offline_buffers_and_holds():
    a = EdgeAutonomy(lambda e: [])
    a.go_offline()
    sent: list[dict] = []
    a.ingest(PERMIT, sent.append)
    for r in _readings():
        a.ingest(r, sent.append)
    assert sent == []  # nothing goes upstream while offline
    assert a.mode == "autonomous"
    assert a.stats()["offlineEvents"] == 4


def test_fail_operational_detection_offline():
    """The safety core still fires with no central connectivity (P1)."""
    a = EdgeAutonomy(_real_engine())
    a.go_offline()
    sink: list[dict] = []
    a.ingest(PERMIT, sink.append)
    for r in _readings():
        a.ingest(r, sink.append)
    findings = a.evaluate_local()
    assert any("Hot work" in f.title and f.zone_id == Z for f in findings)


def test_reconnect_flushes_in_order():
    a = EdgeAutonomy(lambda e: [])
    a.go_offline()
    events = [PERMIT, *_readings()]
    for e in events:
        a.ingest(e, lambda _x: None)
    sent: list[dict] = []
    n = a.reconnect(sent.append)
    assert n == len(events)
    assert sent == events  # order preserved
    assert a.online and a.stats()["offlineEvents"] == 0
