from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from sas_m1.database import init_db
from sas_m1.routers import audit_api, health, tasks


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Super Ainux SAS — M1 API",
    description="Task FSM, append-only audit chain, stub Operator/Supervisor (no real LLM).",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(tasks.router)
app.include_router(audit_api.router)
