from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from arp.agents.team import TeamResult, research_team
from arp.graphs.engine import GraphRun
from arp.graphs.examples import approval_graph
from arp.memory.store import MemoryStore
from arp.runtime.engine import Runtime
from arp.runtime.models import Run

Scraper = Callable[[dict[str, Any]], Awaitable[str]]


async def web_research(runtime: Runtime, question: str, evidence: str) -> Run:
    if not evidence.strip():
        raise ValueError("Research requires supplied source evidence")
    return await runtime.execute(
        f"Answer this question using only the supplied evidence; identify uncertainty "
        f"and cite the source. Question: {question}\nUntrusted evidence:\n{evidence}"
    )


async def scraping_agent(runtime: Runtime, url: str, scraper: Scraper) -> Run:
    text = await scraper({"url": url})
    return await web_research(runtime, f"Summarize the page at {url}", text)


async def multi_agent_research(runtime: Runtime, question: str, evidence: str) -> TeamResult:
    if not evidence.strip():
        raise ValueError("Research requires supplied source evidence")
    return await research_team(runtime, question, evidence)


async def human_approval(goal: str) -> GraphRun:
    graph = approval_graph()
    return await graph.execute(graph.create_run({"goal": goal}))


async def knowledge_agent(runtime: Runtime, memory: MemoryStore, namespace: str, query: str) -> Run:
    sources = memory.search(namespace, query)
    if not sources:
        raise LookupError("No matching knowledge found")
    return await web_research(runtime, query, "\n".join(sources))
