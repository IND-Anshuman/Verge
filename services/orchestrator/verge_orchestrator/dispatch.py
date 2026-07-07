"""Operator-gated, multi-channel alert dispatch (spec §4.4, P8).

Drafting an alert is one thing (``alerts.py``); *delivering* it is another, and
Verge treats delivery as an operator action, never an automatic one (P8, §4.4):

* **Dispatch requires an approver.** ``dispatch_alert`` refuses without
  ``approved_by`` — Verge recommends, a human commits. The refusal is itself
  recorded.
* **Channels degrade, they don't fabricate (P4).** The in-system console channel
  always delivers; external channels (SMS/IVR/PA/app) need a provider and, on a
  dev/air-gapped box with no telephony, report ``degraded`` rather than claiming
  a delivery that did not happen.
* **Every dispatch is hash-chainable.** The receipt (who approved, when, which
  channels, per-channel outcome) is returned as an audit payload.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol, runtime_checkable

from verge_schema.audit import Alert


@dataclass
class DeliveryResult:
    channel: str
    delivered: bool
    degraded: bool = False
    reason: str = ""
    ref: str | None = None  # provider message id when delivered

    def to_dict(self) -> dict:
        return {
            "channel": self.channel,
            "delivered": self.delivered,
            "degraded": self.degraded,
            "reason": self.reason,
            "ref": self.ref,
        }


@runtime_checkable
class Channel(Protocol):
    name: str

    def send(self, alert: Alert) -> DeliveryResult: ...


class ConsoleChannel:
    """The operator console feed — always available (in-system, no network)."""

    name = "console"

    def send(self, alert: Alert) -> DeliveryResult:
        return DeliveryResult(self.name, delivered=True, ref=f"console:{alert.alert_id}")


class _ExternalChannel:
    """SMS/IVR/PA/app: needs a provider; degrades on a box with no telephony."""

    name = "external"
    _url_env = ""
    _label = "external channel"

    def __init__(self, env: Mapping[str, str]) -> None:
        self._env = env

    def send(self, alert: Alert) -> DeliveryResult:
        if not self._env.get(self._url_env):
            return DeliveryResult(self.name, delivered=False, degraded=True,
                                  reason=f"{self._label} not configured ({self._url_env} unset)")
        # A live install wires the provider SDK here; on this host there is none,
        # so we report the alert as queued-not-delivered rather than faking it.
        return DeliveryResult(self.name, delivered=False, degraded=True,
                              reason=f"{self._label} configured but unreachable from this host")


class SmsChannel(_ExternalChannel):
    name = "sms"
    _url_env = "VERGE_SMS_PROVIDER_URL"
    _label = "SMS gateway"


class IvrChannel(_ExternalChannel):
    name = "ivr"
    _url_env = "VERGE_IVR_PROVIDER_URL"
    _label = "IVR gateway"


class PaChannel(_ExternalChannel):
    name = "pa"
    _url_env = "VERGE_PA_SYSTEM_URL"
    _label = "PA system"


class AppChannel(_ExternalChannel):
    name = "app"
    _url_env = "VERGE_APP_PUSH_URL"
    _label = "mobile app push"


def channels_from_env(env: Mapping[str, str] | None = None) -> dict[str, Channel]:
    env = env if env is not None else os.environ
    return {
        "console": ConsoleChannel(),
        "app": AppChannel(env),
        "sms": SmsChannel(env),
        "ivr": IvrChannel(env),
        "pa": PaChannel(env),
    }


@dataclass
class DispatchReceipt:
    alert_id: str
    finding_id: str
    approved_by: str | None
    dispatched_at: datetime
    results: list[DeliveryResult] = field(default_factory=list)
    refused: bool = False
    reason: str = ""

    @property
    def any_delivered(self) -> bool:
        return any(r.delivered for r in self.results)

    def to_dict(self) -> dict:
        return {
            "alertId": self.alert_id,
            "findingId": self.finding_id,
            "approvedBy": self.approved_by,
            "dispatchedAt": self.dispatched_at.isoformat(),
            "refused": self.refused,
            "reason": self.reason,
            "anyDelivered": self.any_delivered,
            "results": [r.to_dict() for r in self.results],
        }

    def audit_payload(self) -> dict:
        return {"kind": "alert-dispatch", **self.to_dict()}


def dispatch_alert(
    alert: Alert,
    *,
    approved_by: str | None,
    dispatched_at: datetime,
    channels: list[str] | None = None,
    registry: Mapping[str, Channel] | None = None,
) -> DispatchReceipt:
    """Deliver an approved alert across channels. Refuses without an approver (P8)."""
    registry = registry or channels_from_env()
    # De-duplicate channels (preserve order): a duplicate would double-send on a
    # real SMS/PA provider and skew the delivery receipt.
    targets = list(dict.fromkeys(channels or list(alert.channels) or ["console"]))

    # P8 gate: a real human identity is required. A blank/whitespace approver is
    # NOT an approver — it would let the human-accountability control be tripped
    # anonymously, which on a safety product is worse than useless.
    approver = approved_by.strip() if approved_by else ""
    if not approver:
        return DispatchReceipt(
            alert_id=alert.alert_id, finding_id=alert.finding_id, approved_by=None,
            dispatched_at=dispatched_at, refused=True,
            reason="dispatch requires operator approval (P8): no approver supplied",
        )

    results: list[DeliveryResult] = []
    for name in targets:
        channel = registry.get(name)
        if channel is None:
            results.append(DeliveryResult(name, delivered=False, degraded=True,
                                          reason=f"unknown channel '{name}'"))
        else:
            results.append(channel.send(alert))
    return DispatchReceipt(
        alert_id=alert.alert_id, finding_id=alert.finding_id, approved_by=approver,
        dispatched_at=dispatched_at, results=results,
    )
