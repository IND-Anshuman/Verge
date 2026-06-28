"""Pick the store backend from the environment.

    VERGE_STORE=memory   (default) — InMemoryStore
    VERGE_STORE=sql      — SqlStore at VERGE_DB_URL (default sqlite:///verge.db;
                           in production a postgresql+psycopg://... URL)

SqlStore (and SQLAlchemy) is imported lazily so memory-mode deployments and the
test suite need no DB driver.
"""

from __future__ import annotations

import os

from .store import InMemoryStore
from .store_base import StoreProtocol


def make_store(env: dict[str, str] | None = None) -> StoreProtocol:
    env = env if env is not None else dict(os.environ)
    if env.get("VERGE_STORE", "memory").lower() == "sql":
        from .sql_store import SqlStore

        return SqlStore(env.get("VERGE_DB_URL", "sqlite:///verge.db"))
    return InMemoryStore()
