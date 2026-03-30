"""FSM unit tests (no DB)."""

from sas_m1.fsm import TaskState, allowed_targets, can_transition


def test_happy_path_edges() -> None:
    assert can_transition(TaskState.New, TaskState.Planning)
    assert can_transition(TaskState.Planning, TaskState.PendingReview)
    assert can_transition(TaskState.PendingReview, TaskState.Approved)
    assert can_transition(TaskState.Approved, TaskState.Executing)


def test_invalid_edge() -> None:
    assert not can_transition(TaskState.New, TaskState.Approved)


def test_blocked_can_resume() -> None:
    assert TaskState.Executing in allowed_targets(TaskState.BlockedCredential)
