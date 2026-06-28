"""Durability + audit integrity across a restart — the reason persistence exists.

A hash-chained audit that evaporates on restart is not an audit (P6). These
tests prove the SQL store survives a process restart and that a tampered audit
record is rejected when the chain is rebuilt.
"""

from datetime import UTC, datetime

import pytest
from sqlalchemy import select, update
from verge_api import db
from verge_api.sql_store import SqlStore
from verge_audit.chain import IntegrityError
from verge_schema.enums import FeedbackVerdict
from verge_schema.enums import FindingState as S
from verge_schema.findings import RiskFinding

T0 = datetime(2025, 1, 13, 6, 30, tzinfo=UTC)


def _f(fid: str, *, shadow: bool = False) -> RiskFinding:
    return RiskFinding(finding_id=fid, created_at=T0, zone_id="B-04", title=f"f {fid}",
                       confidence=0.85, lead_time_band="NEAR", shadow=shadow,
                       lineage=[f"reading:{fid}"])


def test_findings_audit_and_feedback_survive_restart(tmp_path) -> None:
    url = f"sqlite:///{tmp_path}/verge.db"

    s1 = SqlStore(url)
    s1.add_finding(_f("F-A"))
    s1.add_finding(_f("F-B", shadow=True))
    s1.transition("F-A", S.ACKNOWLEDGED, "maya")
    s1.add_feedback("F-A", "maya", FeedbackVerdict.FALSE_ALARM, reason_code="noise")
    head1, len1, fpr1 = s1.audit_head(), s1.audit_len(), s1.fpr()
    del s1

    s2 = SqlStore(url)  # "restart": fresh process, same file
    assert s2.get_finding("F-A").state == "acknowledged"  # transition persisted
    assert {f.finding_id for f in s2.list_findings(shadow=None)} == {"F-A", "F-B"}
    assert [f.finding_id for f in s2.list_findings(shadow=True)] == ["F-B"]
    assert s2.fpr() == fpr1
    # audit chain rebuilt from the DB is identical AND re-verifies (P6)
    assert s2.audit_len() == len1
    assert s2.audit_head() == head1
    assert s2.audit_verify() is True


def test_tampered_audit_row_is_rejected_on_load(tmp_path) -> None:
    url = f"sqlite:///{tmp_path}/verge.db"
    s1 = SqlStore(url)
    s1.add_finding(_f("F-A"))
    s1.add_finding(_f("F-B"))
    del s1

    # Tamper: rewrite a persisted audit payload without recomputing the hash.
    eng = db.make_engine(url)
    with eng.begin() as conn:
        first = conn.execute(select(db.audit_entry.c.seq).order_by(db.audit_entry.c.seq)).first()
        conn.execute(update(db.audit_entry).where(db.audit_entry.c.seq == first[0])
                     .values(payload={"findingId": "TAMPERED", "title": "evil"}))

    # Rebuilding the chain must detect the break and refuse to load.
    with pytest.raises(IntegrityError):
        SqlStore(url)
