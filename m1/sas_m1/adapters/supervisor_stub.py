"""
M1 stub Supervisor adapter — no external LLM calls.
Produces an immutable-shaped approved package stub + content hash (M3 will harden).
"""

from __future__ import annotations

from sas_m1.json_util import sha256_hex


def build_approved_package_stub(operator_plan_body: dict) -> tuple[dict, str]:
    approved = {
        "schema_version": 1,
        "operator_plan": operator_plan_body,
        "supervisor": {
            "stub": True,
            "approved": True,
            "note": "M1 stub approval — replace with real Supervisor review in M3+",
        },
    }
    return approved, sha256_hex(approved)
