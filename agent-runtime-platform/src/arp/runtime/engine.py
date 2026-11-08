from __future__ import annotations

import asyncio

from arp.runtime.model import Model
from arp.runtime.models import Run, RunStatus
from arp.security.policy import ToolPolicy
from arp.tools.registry import ToolRegistry


class Runtime:
    def __init__(
        self, model: Model, registry: ToolRegistry, policy: ToolPolicy, *,
        max_steps: int = 8, timeout_seconds: float = 30,
    ) -> None:
        if max_steps < 1 or timeout_seconds <= 0:
            raise ValueError("Execution bounds must be positive")
        self.model = model
        self.registry = registry
        self.policy = policy
        self.max_steps = max_steps
        self.timeout_seconds = timeout_seconds

    async def execute(self, goal: str) -> Run:
        if not goal.strip() or len(goal) > 32000:
            raise ValueError("Goal must contain 1 to 32000 characters")
        run = Run(goal=goal)
        try:
            async with asyncio.timeout(self.timeout_seconds):
                for step in range(1, self.max_steps + 1):
                    decision = await self.model.decide(
                        goal, list(run.events), self.registry.descriptions(self.policy)
                    )
                    if decision.kind == "final":
                        if not decision.content:
                            raise ValueError("Model returned empty final content")
                        run.result = decision.content
                        run.status = RunStatus.COMPLETED
                        run.record("completed", step=step)
                        return run
                    if decision.kind != "tool" or not decision.tool:
                        raise ValueError("Model returned an invalid tool decision")
                    run.record("tool_requested", step=step, tool=decision.tool)
                    observation = await self.registry.invoke(
                        decision.tool, decision.arguments, self.policy
                    )
                    run.record("tool_result", step=step, tool=decision.tool, output=observation)
                raise RuntimeError("Maximum reasoning steps exceeded")
        except Exception as exc:
            run.status = RunStatus.FAILED
            run.error = f"{type(exc).__name__}: {exc}"
            run.record("failed", error=run.error)
            return run
