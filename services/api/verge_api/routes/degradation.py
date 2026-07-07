"""Operator degradation surface (spec §10.6)."""

from __future__ import annotations

from fastapi import APIRouter, Request

from ..degradation import operator_banners
from ..redpanda_fanout import fanout_enabled
from ..timescale_writer import timescale_status

router = APIRouter(tags=["degradation"])


@router.get("/degradation")
def degradation_status(request: Request) -> dict:
    """Active operator banners derived from live platform posture."""
    s = request.app.state
    banners = operator_banners(
        store=s.store,
        llm=s.llm,
        vision=s.vision,
        readings=s.readings,
        stream_fanout_active=getattr(s, "stream_fanout_active", False),
        stream_fanout_configured=fanout_enabled(),
        timescale=timescale_status(),
    )
    return {"banners": banners, "count": len(banners)}
