"""IsolationForest anomaly layer (spec §4.1) — registry-backed artifacts + canary routing.

Production and canary models load from the MLOps registry with digest verification.
Zones in ``VERGE_ML_CANARY_ZONES`` route to the canary model; others use production.
Canary/shadow-stage scores tag findings ``shadow=True`` until promotion.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from verge_mlops.canary import parse_canary_zones
from verge_mlops.registry import CANARY, DEMO_REGISTRY, SHADOW, ModelCard, ModelRegistry
from verge_mlops.router import ModelRouter, RouteDecision
from verge_schema.enums import EstimateQuality, FindingState, LeadTimeBand
from verge_schema.findings import ContributingSignal, RiskFinding

from .runner import StreamState

MODEL_NAME = "compound-risk"


@dataclass
class ScorerBundle:
    model: object
    feature_dim: int
    source: str  # registry | synthetic
    model_id: str | None = None
    version: str | None = None
    stage: str | None = None


@dataclass
class FeatureVector:
    zone_id: str
    values: list[float]
    sensor_ids: list[str]


def _features_from_state(state: StreamState, zone_id: str) -> FeatureVector | None:
    """Build a multivariate vector: mean LEL, max LEL, slope, sensor count."""
    vals: list[float] = []
    sids: list[str] = []
    for sid, dq in state.readings.items():
        sensor = state.sensors.get(sid)
        if sensor is None or sensor.zone_id != zone_id:
            continue
        if not str(sensor.kind).startswith("gas"):
            continue
        pts = list(dq)
        if not pts:
            continue
        vals.extend([pts[-1].value, (pts[-1].value - pts[0].value)])
        sids.append(sid)
    if len(vals) < 2:
        return None
    vals.append(float(len(sids)))
    return FeatureVector(zone_id=zone_id, values=vals, sensor_ids=sids)


def _fit_synthetic_scorer() -> ScorerBundle | None:
    try:
        from sklearn.ensemble import IsolationForest
    except ImportError:
        return None
    import numpy as np

    rng = np.random.default_rng(42)
    normal = rng.normal(loc=[25.0, 2.0, 30.0, 1.0, 2.0], scale=[8, 3, 10, 1, 0.5], size=(200, 5))
    model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    model.fit(normal)
    return ScorerBundle(model=model, feature_dim=5, source="synthetic", stage="synthetic")


def _registry() -> ModelRegistry:
    reg_path = os.environ.get("VERGE_MODEL_REGISTRY")
    if reg_path and Path(reg_path).exists():
        return ModelRegistry(reg_path)
    return ModelRegistry.read_only(DEMO_REGISTRY)


def _canary_zone_map() -> dict[str, set[str]]:
    raw = os.environ.get("VERGE_ML_CANARY_ZONES", "compound-risk:B-04,B-05")
    return parse_canary_zones(raw)


def _load_scorer_for_card(card: ModelCard) -> ScorerBundle | None:
    from verge_mlops.artifacts import artifact_root, load_sklearn_bundle

    if not card.artifact_ref:
        return None
    reg_path = os.environ.get("VERGE_MODEL_REGISTRY")
    root = artifact_root(reg_path or DEMO_REGISTRY)
    bundle = load_sklearn_bundle(card, root=root)
    return ScorerBundle(
        model=bundle["model"],
        feature_dim=int(bundle.get("feature_dim", 5)),
        source="registry",
        model_id=card.model_id,
        version=card.version,
        stage=card.stage,
    )


_ROUTER: ModelRouter | None = None
_SCORERS: dict[str, ScorerBundle] = {}
_SYNTHETIC: ScorerBundle | None = None


def _get_router() -> ModelRouter:
    global _ROUTER
    if _ROUTER is None:
        _ROUTER = ModelRouter(_registry(), _canary_zone_map())
    return _ROUTER


def _scorer_for_decision(decision: RouteDecision) -> ScorerBundle | None:
    global _SYNTHETIC
    if not decision.routed or decision.model is None:
        return None
    card = decision.model
    cached = _SCORERS.get(card.model_id)
    if cached is not None:
        return cached
    try:
        scorer = _load_scorer_for_card(card)
    except Exception:
        scorer = None
    if scorer is None:
        if _SYNTHETIC is None:
            _SYNTHETIC = _fit_synthetic_scorer()
        return _SYNTHETIC
    _SCORERS[card.model_id] = scorer
    return scorer


def reset_scorer_cache() -> None:
    """Test helper — force reload on next score."""
    global _ROUTER, _SCORERS, _SYNTHETIC
    _ROUTER = None
    _SCORERS = {}
    _SYNTHETIC = None


def ml_findings(
    state: StreamState,
    *,
    zone_ids: list[str] | None = None,
    min_score: float = -0.15,
) -> list[RiskFinding]:
    """Score zones; emit findings when IsolationForest flags an outlier."""
    router = _get_router()
    zone_ids = zone_ids or sorted({s.zone_id for s in state.sensors.values()})
    out: list[RiskFinding] = []
    now = state.now
    if now is None:
        return []

    for zone_id in zone_ids:
        decision = router.route(MODEL_NAME, zone=zone_id)
        scorer = _scorer_for_decision(decision)
        if scorer is None:
            continue
        fv = _features_from_state(state, zone_id)
        if fv is None:
            continue
        dim = scorer.feature_dim
        vec = (fv.values + [0.0] * dim)[:dim]
        score = float(scorer.model.decision_function([vec])[0])
        if score >= min_score:
            continue
        stage = decision.stage or scorer.stage
        shadow = stage in (CANARY, SHADOW)
        signals = [
            ContributingSignal(
                kind="reading",
                ref_id=sid,
                summary="anomaly feature contributor",
                ts=now,
            )
            for sid in fv.sensor_ids[:3]
        ]
        basis = f"iforest score={score:.3f}"
        if scorer.version:
            basis += f" model={scorer.version} stage={stage or scorer.source}"
        lineage_prefix = f"ml:{scorer.model_id or MODEL_NAME}"
        out.append(RiskFinding(
            finding_id=f"F-ML-{now:%Y%m%dT%H%M%S}-{zone_id}",
            created_at=now,
            zone_id=zone_id,
            title="ML: multivariate gas anomaly (IsolationForest)",
            state=FindingState.NEW,
            confidence=round(min(0.95, 0.75 + abs(score)), 3),
            contributing_signals=signals,
            lead_time_band=LeadTimeBand.WATCH,
            lead_time_basis=basis,
            estimate_quality=EstimateQuality.MEDIUM,
            lineage=[lineage_prefix, *[f"reading:{s}" for s in fv.sensor_ids]],
            shadow=shadow,
        ))
    return out
