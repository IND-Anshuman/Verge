"""VERGE_SEED gate helpers (Phase 0 truth gate)."""

from __future__ import annotations

from verge_api.demo_seed import seed_enabled, seed_mode


def test_seed_mode_defaults_to_demo() -> None:
    assert seed_mode({}) == "demo"
    assert seed_enabled({}) is True


def test_seed_mode_off_aliases() -> None:
    for raw in ("off", "false", "0", "no", "none"):
        assert seed_mode({"VERGE_SEED": raw}) == "off"
        assert seed_enabled({"VERGE_SEED": raw}) is False


def test_seed_mode_demo_aliases() -> None:
    for raw in ("demo", "on", "true", "1", "yes"):
        assert seed_mode({"VERGE_SEED": raw}) == "demo"
