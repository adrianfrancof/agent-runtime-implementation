"""Run from the installed project: python examples/local_demo.py."""
import asyncio

from arp.graphs.examples import approval_graph
from arp.runtime.engine import Runtime
from arp.runtime.model import DemoModel
from arp.security.policy import ToolPolicy
from arp.tools.registry import default_registry


async def main():
    runtime = Runtime(DemoModel(), default_registry(), ToolPolicy(frozenset({"echo"})))
    run = await runtime.execute("Demonstrate the runtime")
    print("Agent:", run.status, run.result)

    graph = approval_graph()
    approval = graph.create_run({"goal": "Publish a demonstration"})
    await graph.execute(approval)
    print("Before approval:", approval.status, approval.state["proposal"])
    await graph.approve(approval, True)
    print("After approval:", approval.status, approval.state["result"])


if __name__ == "__main__":
    asyncio.run(main())
