from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from sas_m1.database import get_db
from sas_m1.models import AuditEvent
from sas_m1.schemas import AuditEventOut

router = APIRouter(prefix="/v1/audit", tags=["audit"])


@router.get("", response_model=list[AuditEventOut])
def list_audit(
    db: Session = Depends(get_db),
    task_id: uuid.UUID | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> list[AuditEvent]:
    q = select(AuditEvent).order_by(AuditEvent.id.asc())
    if task_id is not None:
        q = q.where(AuditEvent.task_id == task_id)
    q = q.offset(offset).limit(limit)
    return list(db.scalars(q).all())
