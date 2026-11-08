import unittest

from arp.graphs.engine import Graph, Transition
from arp.graphs.examples import approval_graph
from arp.runtime.models import RunStatus


class GraphTests(unittest.IsolatedAsyncioTestCase):
    async def test_approval_pauses_and_continues_once(self):
        graph = approval_graph()
        run = graph.create_run({"goal": "release"})
        await graph.execute(run)
        self.assertEqual(run.status, RunStatus.WAITING_APPROVAL)
        self.assertNotIn("result", run.state)
        await graph.approve(run, True)
        self.assertEqual(run.status, RunStatus.COMPLETED)
        self.assertEqual(run.history, ["prepare", "approval_granted", "publish"])
        with self.assertRaises(ValueError):
            await graph.approve(run, True)

    async def test_rejection_does_not_run_continuation(self):
        graph = approval_graph()
        run = graph.create_run({"goal": "release"})
        await graph.execute(run)
        await graph.approve(run, False)
        self.assertEqual(run.status, RunStatus.REJECTED)
        self.assertNotIn("result", run.state)

    async def test_graph_cycle_is_bounded(self):
        async def loop(state):
            return Transition(next_node="loop")
        graph = Graph({"loop": loop}, "loop", max_steps=2)
        run = graph.create_run({})
        await graph.execute(run)
        self.assertEqual(run.status, RunStatus.FAILED)
        self.assertEqual(run.steps, 2)

    async def test_unknown_node_fails(self):
        async def node(state):
            return Transition(next_node="missing")
        graph = Graph({"start": node}, "start")
        run = await graph.execute(graph.create_run({}))
        self.assertEqual(run.status, RunStatus.FAILED)
        self.assertIn("Unknown graph node", run.error)
