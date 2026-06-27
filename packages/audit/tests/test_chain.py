"""The audit chain must detect any tampering and survive a faithful rebuild."""

from datetime import UTC, datetime, timedelta

from verge_audit import AuditChain, canonical_json
from verge_audit.chain import GENESIS_HASH, IntegrityError


def _ts(i: int) -> datetime:
    return datetime(2025, 1, 13, 6, 0, tzinfo=UTC) + timedelta(seconds=i)


def _build(n: int = 5) -> AuditChain:
    chain = AuditChain()
    for i in range(n):
        chain.append(
            actor="maya",
            kind="finding-event",
            payload={"findingId": f"F-{i}", "toState": "acknowledged"},
            timestamp=_ts(i),
        )
    return chain


def test_empty_head_is_genesis() -> None:
    assert AuditChain().head == GENESIS_HASH


def test_chain_links_and_verifies() -> None:
    chain = _build()
    assert len(chain) == 5
    chain.verify()  # must not raise
    entries = list(chain)
    assert entries[0].prev_hash == GENESIS_HASH
    for a, b in zip(entries, entries[1:], strict=False):
        assert b.prev_hash == a.hash


def test_tamper_is_detected() -> None:
    chain = _build()
    # Mutate a payload in the middle without recomputing -- chain must break.
    list(chain)[2].payload["toState"] = "closed"
    try:
        chain.verify()
    except IntegrityError as e:
        assert e.index == 2
    else:
        raise AssertionError("tampering went undetected")


def test_rebuild_from_rows() -> None:
    chain = _build()
    rows = [e.to_dict() for e in chain]
    # Map wire dict -> from_entries expected keys
    restored = AuditChain.from_entries(
        {
            "entryId": r["entryId"],
            "timestamp": r["timestamp"],
            "actor": r["actor"],
            "kind": r["kind"],
            "payload": r["payload"],
            "prevHash": r["prevHash"],
        }
        for r in rows
    )
    assert restored.head == chain.head


def test_canonical_json_is_stable() -> None:
    a = canonical_json({"b": 1, "a": 2})
    b = canonical_json({"a": 2, "b": 1})
    assert a == b == '{"a":2,"b":1}'
