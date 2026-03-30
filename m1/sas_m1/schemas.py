from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str = ""
    user_intent: str = ""
    priority: int = 0


class TaskOut(BaseModel):
    id: uuid.UUID
    title: str
    user_intent: str
    state: str
    priority: int
    approved_plan_hash: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TransitionRequest(BaseModel):
    to_state: str = Field(..., description="Target TaskState name")
    actor: str = Field(
        ...,
        description="system | user | operator_agent | supervisor_agent | policy",
    )
    reason_code: str | None = None
    note: str | None = None


class PlanArtifactOut(BaseModel):
    id: int
    task_id: uuid.UUID
    kind: str
    version: int
    body: dict[str, Any]
    body_hash: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditEventOut(BaseModel):
    id: int
    event_id: uuid.UUID
    ts: datetime
    event_type: str
    task_id: uuid.UUID | None
    actor: str
    payload: dict[str, Any]
    prev_hash: str
    row_hash: str

    model_config = {"from_attributes": True}
