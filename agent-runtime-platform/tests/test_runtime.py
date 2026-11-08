import asyncio
import unittest

from arp.runtime.engine import Runtime
from arp.runtime.model import DemoModel
from arp.runtime.models import Decision, RunStatus
from arp.security.policy import ToolPolicy
from arp.tools.registry import default_registry


class ScriptedModel:
    def __init__(self, decision):
        self.decision = decision

    async def decide(self, goal, events, tools):
        return self.decision


class RuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def test_demo_runs_tool_then_finishes(self):
        runtime = Runtime(DemoModel(), default_registry(), ToolPolicy(frozenset({"echo"})))
        run = await runtime.execute("test goal")
        self.assertEqual(run.status, RunStatus.COMPLETED)
        self.assertEqual([e["type"] for e in run.events], ["tool_requested", "tool_result", "completed"])
        self.assertEqual(run.result, "Demo completed: test goal")

    async def test_disallowed_tool_fails_closed(self):
        model = ScriptedModel(Decision("tool", tool="echo", arguments={"text": "a"}))
        runtime = Runtime(model, default_registry(), ToolPolicy(frozenset()))
        run = await runtime.execute("goal")
        self.assertEqual(run.status, RunStatus.FAILED)
        self.assertIn("PermissionDenied", run.error)

    async def test_loop_exhaustion_is_a_failure(self):
        model = ScriptedModel(Decision("tool", tool="echo", arguments={"text": "a"}))
        runtime = Runtime(model, default_registry(), ToolPolicy(frozenset({"echo"})), max_steps=2)
        run = await runtime.execute("goal")
        self.assertEqual(run.status, RunStatus.FAILED)
        self.assertIn("Maximum reasoning steps", run.error)

    async def test_timeout_is_a_failure(self):
        class SlowModel:
            async def decide(self, goal, events, tools):
                await asyncio.sleep(1)
                return Decision("final", content="late")
        runtime = Runtime(SlowModel(), default_registry(), ToolPolicy(frozenset()), timeout_seconds=0.01)
        run = await runtime.execute("goal")
        self.assertEqual(run.status, RunStatus.FAILED)
        self.assertIn("TimeoutError", run.error)

    async def test_blank_goal_rejected(self):
        runtime = Runtime(DemoModel(), default_registry(), ToolPolicy(frozenset()))
        with self.assertRaises(ValueError):
            await runtime.execute("  ")
