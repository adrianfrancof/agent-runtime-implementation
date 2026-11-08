import unittest

from arp.memory.store import InMemoryStore
from arp.tools.browser import validate_url
from arp.tools.registry import ToolError


class MemoryAndBrowserTests(unittest.TestCase):
    def test_namespace_and_case_insensitive_retrieval(self):
        memory = InMemoryStore()
        memory.add("a", "Project Alpha")
        memory.add("b", "Project Alpha secret")
        self.assertEqual(memory.search("a", "ALPHA"), ["Project Alpha"])

    def test_url_allowlist(self):
        hosts = frozenset({"example.com"})
        validate_url("https://example.com/path", hosts)
        for url in (
            "http://example.com", "https://example.com.evil.test",
            "https://example.com@evil.test", "https://example.com:8443",
            "https://127.0.0.1", "file:///etc/passwd",
        ):
            with self.subTest(url=url), self.assertRaises(ToolError):
                validate_url(url, hosts)
