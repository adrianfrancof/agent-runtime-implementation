import unittest

from arp.memory.store import InMemoryStore
from arp.runtime.engine import Runtime
from arp.runtime.model import DemoModel
from arp.runtime.models import RunStatus
from arp.security.policy import ToolPolicy
from arp.tools.registry import default_registry
from arp.workflows.reference import (
    human_approval, knowledge_agent, multi_agent_research, scraping_agent, web_research,
)


class WorkflowTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.runtime = Runtime(DemoModel(), default_registry(), ToolPolicy(frozenset({"echo"})))

    async def test_research_and_multi_agent(self):
        research = await web_research(self.runtime, "What happened?", "Source: a fact")
        self.assertEqual(research.status, RunStatus.COMPLETED)
        team = await multi_agent_research(self.runtime, "What happened?", "Source: a fact")
        self.assertEqual(len(team.messages), 2)
        self.assertEqual(team.synthesis.status, RunStatus.COMPLETED)
        with self.assertRaises(ValueError):
            await web_research(self.runtime, "question", "")

    async def test_scraping_composes_supplied_adapter(self):
        async def fake_scraper(arguments):
            self.assertEqual(arguments["url"], "https://example.com")
            return "x" * 12000
        result = await scraping_agent(self.runtime, "https://example.com", fake_scraper)
        self.assertEqual(result.status, RunStatus.COMPLETED)

    async def test_approval_and_knowledge(self):
        approval = await human_approval("release")
        self.assertEqual(approval.status, RunStatus.WAITING_APPROVAL)
        store = InMemoryStore()
        store.add("tenant-a", "Alpha is a project")
        result = await knowledge_agent(self.runtime, store, "tenant-a", "Alpha")
        self.assertEqual(result.status, RunStatus.COMPLETED)
        with self.assertRaises(LookupError):
            await knowledge_agent(self.runtime, store, "tenant-b", "Alpha")
