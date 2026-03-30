from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sas_m1.adapters import build_approved_package_stub, generate_operator_plan_body
from sas_m1.audit_service import append_audit
from sas_m1.database import get_db
from sas_m1.fsm import TaskState, can_transition
from sas_m1.models import PlanArtifact, PlanArtifactKind, Task, utcnow
from sas_m1.schemas import PlanArtifactOut, TaskCreate, TaskOut, TransitionRequest

router = APIRouter(prefix="/v1/tasks", tags=["tasks"])


def _get_task(db: Session, task_id: uuid.UUID) -> Task:
    t = db.get(Task, task_id)
    if t is None:
        raise HTTPException(status_code=404, detail="task not found")
    return t


def _next_plan_version(db: Session, task_id: uuid.UUID) -> int:
    v = db.scalar(
        select(func.max(PlanArtifact.version)).where(PlanArtifact.task_id == task_id)
    )
    return (v or 0) + 1


@router.post("", response_model=TaskOut)
def create_task(body: TaskCreate, db: Session = Depends(get_db)) -> Task:
    t = Task(
        title=body.title,
        user_intent=body.user_intent,
        priority=body.priority,
        state=TaskState.New.value,
    )
    db.add(t)
    db.flush()
    append_audit(
        db,
        event_type="task.created",
        actor="system",
        payload={"title": body.title, "priority": body.priority},
        task_id=t.id,
    )
    db.commit()
    db.refresh(t)
    return t


@router.get("", response_model=list[TaskOut])
def list_tasks(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    state: str | None = None,
) -> list[Task]:
    q = select(Task).order_by(Task.created_at.desc())
    if state is not None:
        q = q.where(Task.state == state)
    q = q.offset(offset).limit(limit)
    return list(db.scalars(q).all())


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: uuid.UUID, db: Session = Depends(get_db)) -> Task:
    return _get_task(db, task_id)


@router.post("/{task_id}/transition", response_model=TaskOut)
def transition_task(
    task_id: uuid.UUID,
    body: TransitionRequest,
    db: Session = Depends(get_db),
) -> Task:
    t = _get_task(db, task_id)
    try:
        current = TaskState(t.state)
        target = TaskState(body.to_state)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"invalid state: {e}") from e
    if not can_transition(current, target):
        raise HTTPException(
            status_code=409,
            detail=f"transition not allowed: {current.value} -> {target.value}",
        )
    old = t.state
    t.state = target.value
    t.updated_at = utcnow()
    append_audit(
        db,
        event_type="task.state_transition",
        actor=body.actor,
        payload={
            "from_state": old,
            "to_state": target.value,
            "reason_code": body.reason_code,
            "note": body.note,
        },
        task_id=t.id,
    )
    db.commit()
    db.refresh(t)
    return t


@router.post("/{task_id}/actions/submit-operator-plan-stub", response_model=TaskOut)
def submit_operator_plan_stub(task_id: uuid.UUID, db: Session = Depends(get_db)) -> Task:
    """
    Trusted service: runs stub Operator, stores plan artifact, moves Planning -> PendingReview.
    Audit is written here (Operator process never writes audit directly — spec §5.5).
    """
    t = _get_task(db, task_id)
    if t.state != TaskState.Planning.value:
        raise HTTPException(
            status_code=409,
            detail=f"task must be in Planning, got {t.state}",
        )
    body, h = generate_operator_plan_body(
        task_id=t.id, title=t.title, user_intent=t.user_intent
    )
    ver = _next_plan_version(db, t.id)
    pa = PlanArtifact(
        task_id=t.id,
        kind=PlanArtifactKind.operator_plan,
        version=ver,
        body=body,
        body_hash=h,
    )
    db.add(pa)
    t.state = TaskState.PendingReview.value
    t.updated_at = utcnow()
    append_audit(
        db,
        event_type="plan.operator_stub_submitted",
        actor="operator_agent",
        payload={"body_hash": h, "version": ver, "kind": PlanArtifactKind.operator_plan},
        task_id=t.id,
    )
    db.commit()
    db.refresh(t)
    return t


@router.post("/{task_id}/actions/submit-supervisor-approval-stub", response_model=TaskOut)
def submit_supervisor_approval_stub(task_id: uuid.UUID, db: Session = Depends(get_db)) -> Task:
    t = _get_task(db, task_id)
    if t.state != TaskState.PendingReview.value:
        raise HTTPException(
            status_code=409,
            detail=f"task must be in PendingReview, got {t.state}",
        )
    op = db.scalars(
        select(PlanArtifact)
        .where(
            PlanArtifact.task_id == t.id,
            PlanArtifact.kind == PlanArtifactKind.operator_plan,
        )
        .order_by(PlanArtifact.version.desc())
    ).first()
    if op is None:
        raise HTTPException(status_code=409, detail="missing operator plan artifact")
    approved_body, h = build_approved_package_stub(op.body)
    ver = _next_plan_version(db, t.id)
    pa = PlanArtifact(
        task_id=t.id,
        kind=PlanArtifactKind.approved_package_stub,
        version=ver,
        body=approved_body,
        body_hash=h,
    )
    db.add(pa)
    t.approved_plan_hash = h
    t.state = TaskState.Approved.value
    t.updated_at = utcnow()
    append_audit(
        db,
        event_type="plan.approved_package_stub",
        actor="supervisor_agent",
        payload={"body_hash": h, "version": ver, "kind": PlanArtifactKind.approved_package_stub},
        task_id=t.id,
    )
    db.commit()
    db.refresh(t)
    return t


@router.get("/{task_id}/plans", response_model=list[PlanArtifactOut])
def list_plans(task_id: uuid.UUID, db: Session = Depends(get_db)) -> list[PlanArtifact]:
    _get_task(db, task_id)
    q = (
        select(PlanArtifact)
        .where(PlanArtifact.task_id == task_id)
        .order_by(PlanArtifact.version.asc())
    )
    return list(db.scalars(q).all())
