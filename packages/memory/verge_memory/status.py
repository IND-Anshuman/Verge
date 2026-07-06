"""Cognee dataset health checks."""

from __future__ import annotations

import os

from .client import CogneeClient
from .datasets import dataset_name
from .retrieve import ensure_seeded


def dataset_health(
    *,
    client: CogneeClient | None = None,
    env: dict[str, str] | None = None,
) -> dict:
    env = env or dict(os.environ)
    dataset = dataset_name(env)
    client = client or CogneeClient.from_env(env)

    seeded = ensure_seeded(client, dataset)
    if not seeded.ok:
        return {
            "dataset": dataset,
            "configured": client.settings.ready,
            "degraded": True,
            "reason": seeded.reason,
        }

    probe = client.search(dataset, "Verge memory health probe", top_k=1)
    if not probe.ok:
        return {
            "dataset": dataset,
            "configured": client.settings.ready,
            "degraded": True,
            "reason": probe.reason,
        }

    return {"dataset": dataset, "configured": True, "degraded": False}
