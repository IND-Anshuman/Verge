"""Edge autonomy mode (spec §14 Phase 4; P1 fail-operational, P7 edge-first).

If the link to the central bus/API drops, the plant does not go blind. The edge
box keeps running the **deterministic safety core locally** on the events it is
still receiving, so detection → alert continues on-prem with no cloud and no
central dependency (P1). Meanwhile every event is store-and-forwarded, so nothing
is lost; on reconnect the buffer flushes upstream in order (P7).

The safety engine is *injected* as a callable, so the edge-gateway package stays
dependency-light (schema only) — the composition (rules + SIMOPS + plant) is
wired by the caller, exactly as the live CLI wires it.
"""

from __future__ import annotations

from collections.abc import Callable

from .buffer import StoreAndForward

# events -> findings (whatever the caller's composed engine returns)
EvaluateFn = Callable[[list[dict]], list]


class EdgeAutonomy:
    """Coordinates central-vs-autonomous operation without ever losing events."""

    def __init__(self, evaluate: EvaluateFn, *, maxlen: int = 100_000) -> None:
        self._saf = StoreAndForward(maxlen=maxlen)
        self._evaluate = evaluate
        self._offline_events: list[dict] = []

    @property
    def online(self) -> bool:
        return self._saf.online

    @property
    def mode(self) -> str:
        return "central" if self.online else "autonomous"

    @property
    def buffered(self) -> int:
        return self._saf.buffered

    @property
    def dropped(self) -> int:
        return self._saf.dropped

    def go_offline(self) -> None:
        """Central link lost — switch to autonomous (local) evaluation."""
        self._saf.go_offline()

    def ingest(self, event: dict, upstream_sink: Callable[[dict], None]) -> None:
        """Forward upstream if online; otherwise buffer + hold for local scoring."""
        self._saf.submit(event, upstream_sink)
        if not self.online:
            self._offline_events.append(event)

    def evaluate_local(self) -> list:
        """Fail-operational: run the safety core locally on the offline events.

        Detection continues at the edge with no central connectivity (P1)."""
        return self._evaluate(list(self._offline_events))

    def reconnect(self, upstream_sink: Callable[[dict], None]) -> int:
        """Central link restored — flush buffered events upstream, in order."""
        n = self._saf.reconnect(upstream_sink)
        self._offline_events.clear()
        return n

    def stats(self) -> dict:
        return {
            "mode": self.mode,
            "online": self.online,
            "buffered": self.buffered,
            "dropped": self.dropped,
            "offlineEvents": len(self._offline_events),
        }
