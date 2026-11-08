from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from arp.runtime.models import RunStatus

GraphState = dict[str, Any]


@dataclass(frozen=True)
class Transition:
    next_node: str | None = None
    approval_required: bool = False


Node = Callable[[GraphState], Awaitable[Transition]]


@dataclass
class GraphRun:
    state: GraphState
    next_node: str | None
    id: str = field(default_factory=lambda: str(uuid4()))
    status: RunStatus = RunStatus.RUNNING
    steps: int = 0
    error: str | None = None
    history: list[str] = field(default_factory=list)


class Graph:
    def __init__(self, nodes: dict[str, Node], start: str, *, max_steps: int = 20) -> None:
        if start not in nodes or max_steps < 1:
            raise ValueError("Graph requires a valid start and positive step bound")
        self.nodes = dict(nodes)
        self.start = start
        self.max_steps = max_steps

    def create_run(self, state: GraphState) -> GraphRun:
        return GraphRun(state=dict(state), next_node=self.start)

    async def execute(self, run: GraphRun) -> GraphRun:
        if run.status != RunStatus.RUNNING:
            raise ValueError("Only running graphs can execute")
        try:
            while run.next_node is not None:
                if run.steps >= self.max_steps:
                    raise RuntimeError("Maximum graph steps exceeded")
                name = run.next_node
                if name not in self.nodes:
                    raise ValueError(f"Unknown graph node: {name}")
                transition = await self.nodes[name](run.state)
                run.steps += 1
                run.history.append(name)
                run.next_node = transition.next_node
                if transition.approval_required:
                    if run.next_node is None:
                        raise ValueError("Approval transition requires a continuation")
                    run.status = RunStatus.WAITING_APPROVAL
                    return run
            run.status = RunStatus.COMPLETED
        except Exception as exc:
            run.status = RunStatus.FAILED
            run.error = f"{type(exc).__name__}: {exc}"
        return run

    async def approve(self, run: GraphRun, approved: bool) -> GraphRun:
        if run.status != RunStatus.WAITING_APPROVAL:
            raise ValueError("Graph is not awaiting approval")
        run.history.append("approval_granted" if approved else "approval_rejected")
        if not approved:
            run.status = RunStatus.REJECTED
            return run
        run.status = RunStatus.RUNNING
        return await self.execute(run)
