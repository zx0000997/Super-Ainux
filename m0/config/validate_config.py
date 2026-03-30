#!/usr/bin/env python3
"""
Validate non-secret runtime JSON + presence of split secret env files (M0).
Does not print secret values.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("Install python3-jsonschema (Debian: apt install python3-jsonschema)", file=sys.stderr)
    sys.exit(2)


def load_env_keys(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, _, v = line.partition("=")
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate SAS M0 runtime config + secret files.")
    ap.add_argument("--runtime", type=Path, required=True, help="Path to sas-runtime.json")
    ap.add_argument(
        "--operator-env",
        type=Path,
        required=True,
        help="Path to operator secrets env (e.g. /etc/super-ainux/operator.env)",
    )
    ap.add_argument(
        "--supervisor-env",
        type=Path,
        required=True,
        help="Path to supervisor secrets env (separate file per SAS key separation).",
    )
    ap.add_argument(
        "--schema",
        type=Path,
        default=None,
        help="JSON Schema path (default: alongside this script).",
    )
    ap.add_argument(
        "--allow-same-provider",
        action="store_true",
        help="Skip heterogenous provider check (not for production).",
    )
    args = ap.parse_args()

    schema_path = args.schema
    if schema_path is None:
        schema_path = Path(__file__).resolve().parent / "schema" / "sas-runtime-config.schema.json"

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    data = json.loads(args.runtime.read_text(encoding="utf-8"))

    Validator = jsonschema.validators.validator_for(schema)
    Validator.check_schema(schema)
    Validator(schema).validate(data)

    op = data["operator"]["provider_id"]
    sp = data["supervisor"]["provider_id"]
    if not args.allow_same_provider and op == sp:
        print(
            "operator.provider_id and supervisor.provider_id must differ (heterogenous models).",
            file=sys.stderr,
        )
        return 1

    for label, path in (
        ("operator", args.operator_env),
        ("supervisor", args.supervisor_env),
    ):
        if not path.is_file():
            print(f"Missing {label} env file: {path}", file=sys.stderr)
            return 1

    if args.operator_env.resolve() == args.supervisor_env.resolve():
        print("operator-env and supervisor-env must be different files.", file=sys.stderr)
        return 1

    op_env = load_env_keys(args.operator_env)
    sp_env = load_env_keys(args.supervisor_env)

    if not op_env.get("OPERATOR_API_KEY"):
        print("operator env must define non-empty OPERATOR_API_KEY", file=sys.stderr)
        return 1
    if not sp_env.get("SUPERVISOR_API_KEY"):
        print("supervisor env must define non-empty SUPERVISOR_API_KEY", file=sys.stderr)
        return 1

    # Cross-leak detection: same key name carrying both secrets in one file is OK if files differ;
    # if operator file contains SUPERVISOR_API_KEY, warn
    if "SUPERVISOR_API_KEY" in op_env and op_env["SUPERVISOR_API_KEY"]:
        print("operator env file must not contain SUPERVISOR_API_KEY", file=sys.stderr)
        return 1
    if "OPERATOR_API_KEY" in sp_env and sp_env["OPERATOR_API_KEY"]:
        print("supervisor env file must not contain OPERATOR_API_KEY", file=sys.stderr)
        return 1

    print("OK: runtime schema valid, provider split OK, secret files present and separated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
