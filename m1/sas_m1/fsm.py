from __future__ import annotations

from enum import Enum
from typing import Mapping, Set


class TaskState(str, Enum):
    """Reference lifecycle per SAS_SYSTEM_SPEC §5.2 + blocking §8."""

    New = "New"
    Planning = "Planning"
    PendingReview = "PendingReview"
    Approved = "Approved"
    Executing = "Executing"
    Verifying = "Verifying"
    Completed = "Completed"
    Delivered = "Delivered"
    Failed = "Failed"
    BlockedPayment = "BlockedPayment"
    BlockedCredential = "BlockedCredential"


# Directed edges: from_state -> allowed to_states
_ALLOWED: Mapping[TaskState, Set[TaskState]] = {
    TaskState.New: {TaskState.Planning},
    TaskState.Planning: {TaskState.PendingReview, TaskState.Failed},
    TaskState.PendingReview: {TaskState.Approved, TaskState.Planning, TaskState.Failed},
    TaskState.Approved: {TaskState.Executing, TaskState.Failed},
    TaskState.Executing: {
        TaskState.Verifying,
        TaskState.Failed,
        TaskState.BlockedPayment,
        TaskState.BlockedCredential,
    },
    TaskState.BlockedPayment: {TaskState.Executing, TaskState.Planning, TaskState.Failed},
    TaskState.BlockedCredential: {TaskState.Executing, TaskState.Planning, TaskState.Failed},
    TaskState.Verifying: {TaskState.Completed, TaskState.Executing, TaskState.Failed},
    TaskState.Completed: {TaskState.Delivered, TaskState.Failed},
    TaskState.Delivered: set(),
    TaskState.Failed: set(),
}


def allowed_targets(state: TaskState) -> Set[TaskState]:
    return set(_ALLOWED.get(state, set()))


def can_transition(from_state: TaskState, to_state: TaskState) -> bool:
    return to_state in _ALLOWED.get(from_state, set())
