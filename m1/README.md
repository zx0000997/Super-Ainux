# M1 — Task FSM API, audit skeleton, stub adapters

Implements [docs/SAS_SYSTEM_SPEC.zh.md](../docs/SAS_SYSTEM_SPEC.zh.md) milestone **M1**:

- **`tasks` table** (SQLite by default): create, list, get, **state transitions** with validated edges.
- **`plan_artifacts`**: Operator stub plan + Supervisor stub **approved package** (content hashed).
- **`audit_events`**: append-only log with **hash chain** (`prev_hash` → `row_hash`); written only by this trusted API (not by a separate “Operator process”).
- **Stub adapters** (`sas_m1/adapters/`): deterministic JSON, no LLM calls.

## Run locally (Python 3.11–3.12 recommended)

```bash
cd m1
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export SAS_M1_DATABASE_URL=sqlite:///./sas_m1.db   # optional
uvicorn sas_m1.main:app --reload --host 127.0.0.1 --port 18081
```

- OpenAPI: http://127.0.0.1:18081/docs  
- Health: http://127.0.0.1:18081/health  

## Run with Podman/Docker

```bash
cd m1/deploy
podman compose -f compose.yaml up -d --build
curl -s http://127.0.0.1:18081/health
```

## Typical happy-path calls

1. `POST /v1/tasks` — create (`New`).
2. `POST /v1/tasks/{id}/transition` — `{ "to_state": "Planning", "actor": "user" }`.
3. `POST /v1/tasks/{id}/actions/submit-operator-plan-stub` — `Planning` → `PendingReview`.
4. `POST /v1/tasks/{id}/actions/submit-supervisor-approval-stub` — `PendingReview` → `Approved`, sets `approved_plan_hash`.
5. Further transitions via `POST .../transition` (e.g. `Approved` → `Executing` → …).

Audit trail: `GET /v1/audit?task_id=<uuid>`.

Full walkthrough: [docs/M1_API.zh.md](../docs/M1_API.zh.md).
