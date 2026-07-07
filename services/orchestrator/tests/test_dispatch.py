"""Operator-gated multi-channel alert dispatch (spec §4.4, P8)."""

from __future__ import annotations

from datetime import UTC, datetime

from verge_orchestrator import channels_from_env, dispatch_alert
from verge_schema.audit import Alert

NOW = datetime(2026, 7, 7, tzinfo=UTC)


def _alert() -> Alert:
    return Alert(
        alert_id="AL-F1", finding_id="F1",
        channels=["console", "sms", "pa"], languages=["en", "hi"],
        body="[en] SAFETY ALERT ...", issued_at=NOW,
    )


def test_dispatch_refuses_without_approver():
    receipt = dispatch_alert(_alert(), approved_by=None, dispatched_at=NOW)
    assert receipt.refused is True
    assert not receipt.results
    assert "approval" in receipt.reason


def test_whitespace_approver_does_not_bypass_the_p8_gate():
    # A blank/whitespace approver is not a real human identity — must be refused.
    for approver in ("   ", "\t", ""):
        receipt = dispatch_alert(_alert(), approved_by=approver, dispatched_at=NOW)
        assert receipt.refused is True


def test_duplicate_channels_are_not_double_sent():
    receipt = dispatch_alert(_alert(), approved_by="maya", dispatched_at=NOW,
                             channels=["console", "console", "sms"])
    channels = [r.channel for r in receipt.results]
    assert channels.count("console") == 1  # de-duplicated


def test_console_delivers_external_channels_degrade():
    receipt = dispatch_alert(_alert(), approved_by="maya", dispatched_at=NOW)
    by_channel = {r.channel: r for r in receipt.results}
    assert by_channel["console"].delivered is True
    # No SMS/PA provider configured on this host -> degraded, not delivered.
    assert by_channel["sms"].delivered is False and by_channel["sms"].degraded
    assert by_channel["pa"].delivered is False and by_channel["pa"].degraded
    assert receipt.any_delivered is True  # console got through


def test_external_channel_configured_still_honest_when_unreachable():
    registry = channels_from_env({"VERGE_SMS_PROVIDER_URL": "https://sms.example"})
    receipt = dispatch_alert(_alert(), approved_by="maya", dispatched_at=NOW,
                             channels=["sms"], registry=registry)
    sms = receipt.results[0]
    assert not sms.delivered and sms.degraded and "unreachable" in sms.reason


def test_unknown_channel_is_reported_degraded():
    receipt = dispatch_alert(_alert(), approved_by="maya", dispatched_at=NOW,
                             channels=["telepathy"])
    assert receipt.results[0].degraded and "unknown channel" in receipt.results[0].reason


def test_receipt_audit_payload_shape():
    receipt = dispatch_alert(_alert(), approved_by="maya", dispatched_at=NOW,
                             channels=["console"])
    payload = receipt.audit_payload()
    assert payload["kind"] == "alert-dispatch"
    assert payload["approvedBy"] == "maya"
    assert payload["anyDelivered"] is True
