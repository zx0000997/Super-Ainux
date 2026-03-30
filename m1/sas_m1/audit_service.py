from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from sas_m1.config import settings
from sas_m1.models import AuditEvent


def _canonical_json(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_row_hash(
    prev_hash: str,
    event_id: uuid.UUID,
    ts: datetime,
    event_type: str,
    payload: dict,
) -> str:
    raw = (
        f"{prev_hash}|{event_id}|{ts.isoformat()}|{event_type}|{_canonical_json(payload)}"
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def latest_row_hash(db: Session) -> str:
    row = db.scalars(select(AuditEvent).order_by(AuditEvent.id.desc()).limit(1)).first()
    if row is None:
        return settings.genesis_audit_hash
    return row.row_hash


def append_audit(
    db: Session,
    *,
    event_type: str,
    actor: str,
    payload: dict,
    task_id: uuid.UUID | None = None,
    event_id: uuid.UUID | None = None,
) -> AuditEvent:
    """
    Append-only audit entry with hash chain (spec §5.5).
    Only trusted services call this — not Operator client processes.
    """
    eid = event_id or uuid.uuid4()
    ts = datetime.now(timezone.utc)
    prev = latest_row_hash(db)
    row_h = compute_row_hash(prev, eid, ts, event_type, payload)
    ev = AuditEvent(
        event_id=eid,
        ts=ts,
        event_type=event_type,
        task_id=task_id,
        actor=actor,
        payload=payload,
        prev_hash=prev,
        row_hash=row_h,
    )
    db.add(ev)
    return ev
