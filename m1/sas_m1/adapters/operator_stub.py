"""
M1 stub Operator adapter — no external LLM calls.
Real Operator integration replaces this in later milestones.
"""

from __future__ import annotations

import uuid

from sas_m1.json_util import sha256_hex


def generate_operator_plan_body(
    *,
    task_id: uuid.UUID,
    title: str,
    user_intent: str,
) -> tuple[dict, str]:
    body = {
        "stub": "operator",
        "schema_version": 1,
        "task_id": str(task_id),
        "title": title,
        "intent_excerpt": user_intent[:2000],
        "steps": [
            {
                "action": "noop",
                "detail": "M1 placeholder — bind real model + tools in M3+",
            }
        ],
    }
    return body, sha256_hex(body)
