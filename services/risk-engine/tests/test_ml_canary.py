"""ML canary zone routing in the scorer."""

from __future__ import annotations

import os

import pytest

pytest.importorskip("sklearn")

from verge_mlops import CANARY
from verge_risk.ml_layer import MODEL_NAME, _get_router, reset_scorer_cache


def test_canary_zone_uses_canary_model_card() -> None:
    reset_scorer_cache()
    os.environ["VERGE_ML_CANARY_ZONES"] = "compound-risk:B-04"
    reset_scorer_cache()
    router = _get_router()
    prod = router.route(MODEL_NAME, zone="B-01")
    canary = router.route(MODEL_NAME, zone="B-04")
    assert prod.stage != CANARY
    assert canary.stage == CANARY
    assert canary.model.version == "1.3.0-rc1"
