"""ML layer loads production artifact from registry."""

from __future__ import annotations

import os

import pytest

pytest.importorskip("sklearn")

from verge_risk.ml_layer import _get_router, reset_scorer_cache


def test_scorer_loads_from_registry_artifact() -> None:
    reset_scorer_cache()
    os.environ.pop("VERGE_ML_CANARY_ZONES", None)
    reset_scorer_cache()
    router = _get_router()
    decision = router.route("compound-risk", zone="B-01")
    assert decision.routed
    assert decision.model is not None
    assert decision.model.model_id == "compound-risk-1.2.0"

