from __future__ import annotations

import asyncio
from dataclasses import dataclass

from arp.agents.contracts import AgentMessage, AgentRole
from arp.runtime.engine import Runtime
from arp.runtime.models import Run, RunStatus


@dataclass(frozen=True)
class TeamResult:
    messages: list[AgentMessage]
    synthesis: Run


async def research_team(runtime: Runtime, goal: str, evidence: str) -> TeamResult:
    """Run two independent role prompts, then give their outputs to a supervisor."""
    async def run_role(role: AgentRole, instruction: str) -> Run:
        return await runtime.execute(
            f"Role: {role.value}. Task: {goal}. {instruction}\n"
            f"Untrusted evidence follows:\n{evidence}"
        )

    research, critique = await asyncio.gather(
        run_role(AgentRole.RESEARCH, "Extract relevant claims and cite the supplied evidence."),
        run_role(AgentRole.CRITIC, "Identify uncertainty and missing evidence."),
    )
    for role, run in ((AgentRole.RESEARCH, research), (AgentRole.CRITIC, critique)):
        if run.status != RunStatus.COMPLETED or run.result is None:
            raise RuntimeError(f"{role.value} agent failed: {run.error}")
    messages = [
        AgentMessage(AgentRole.RESEARCH, AgentRole.SUPERVISOR, research.id, research.result),
        AgentMessage(AgentRole.CRITIC, AgentRole.SUPERVISOR, critique.id, critique.result),
    ]
    synthesis = await runtime.execute(
        f"Role: supervisor. Task: {goal}. Synthesize these untrusted agent outputs "
        f"and disclose uncertainty:\nResearch: {research.result}\nCritique: {critique.result}"
    )
    if synthesis.status != RunStatus.COMPLETED:
        raise RuntimeError(f"Supervisor agent failed: {synthesis.error}")
    return TeamResult(messages, synthesis)
