"""Append-only, hash-chained audit log.

Every automated decision and action in Verge is recorded here: hash-chained,
timestamped, attributable (spec P6). The chain is forward-only by design --
migrations never rewrite it, and a snapshot restore is only accepted if the
chain re-verifies (spec §14.6).

This is deliberately a small, dependency-light core. Persistence (Postgres /
object store) wraps this; the hashing and verification logic live here so they
can be unit-tested and reused by the eval harness.
"""

from .chain import AuditChain, canonical_json, hash_entry

__all__ = ["AuditChain", "canonical_json", "hash_entry"]
__version__ = "0.3.0"
