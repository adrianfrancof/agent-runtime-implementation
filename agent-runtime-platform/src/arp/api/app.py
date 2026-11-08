from __future__ import annotations

import hmac
import os
from dataclasses import asdict
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from arp.graphs.engine import GraphRun
from arp.graphs.examples import approval_graph
from arp.runtime.engine import Runtime
from arp.runtime.model import DemoModel, OpenAIModel
from arp.security.policy import ToolPolicy
from arp.tools.registry import default_registry

app = FastAPI(title="Agent Runtime Platform", version="0.1.0")
graph = approval_graph()
graph_runs: dict[str, GraphRun] = {}


def authenticate(x_api_key: Annotated[str | None, Header()] = None) -> None:
    expected = os.environ.get("ARP_API_KEY")
    if not expected:
        raise HTTPException(status_code=503, detail="ARP_API_KEY is not configured")
    if not x_api_key or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="Invalid API key")


class RunRequest(BaseModel):
    goal: str = Field(min_length=1, max_length=4000)


class ApprovalRequest(BaseModel):
    approved: bool


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/runs", dependencies=[Depends(authenticate)])
async def execute_run(request: RunRequest) -> dict:
    model_name = os.environ.get("ARP_OPENAI_MODEL")
    model = OpenAIModel(model_name) if model_name else DemoModel()
    runtime = Runtime(model, default_registry(), ToolPolicy(frozenset({"echo"})))
    try:
        run = await runtime.execute(request.goal)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return asdict(run)


@app.post("/approval-runs", dependencies=[Depends(authenticate)])
async def create_approval_run(request: RunRequest) -> dict:
    if not request.goal.strip():
        raise HTTPException(status_code=422, detail="Goal must not be blank")
    run = graph.create_run({"goal": request.goal})
    await graph.execute(run)
    graph_runs[run.id] = run
    return asdict(run)


@app.post("/approval-runs/{run_id}/decision", dependencies=[Depends(authenticate)])
async def decide_approval(run_id: str, request: ApprovalRequest) -> dict:
    run = graph_runs.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Approval run not found")
    try:
        await graph.approve(run, request.approved)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return asdict(run)
