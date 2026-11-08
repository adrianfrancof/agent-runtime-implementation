import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from arp.api.app import app, graph_runs


class ApiTests(unittest.TestCase):
    def setUp(self):
        graph_runs.clear()
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        graph_runs.clear()

    def test_authentication_fails_closed(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(self.client.post("/runs", json={"goal": "hi"}).status_code, 503)
        with patch.dict(os.environ, {"ARP_API_KEY": "secret"}, clear=True):
            self.assertEqual(self.client.post("/runs", json={"goal": "hi"}).status_code, 401)
            self.assertEqual(self.client.post("/runs", headers={"X-API-Key": "wrong"}, json={"goal": "hi"}).status_code, 401)
            result = self.client.post("/runs", headers={"X-API-Key": "secret"}, json={"goal": "hi"})
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.json()["status"], "completed")

    def test_approval_workflow_and_replay(self):
        with patch.dict(os.environ, {"ARP_API_KEY": "secret"}, clear=True):
            headers = {"X-API-Key": "secret"}
            result = self.client.post("/approval-runs", headers=headers, json={"goal": "release"})
            self.assertEqual(result.json()["status"], "waiting_approval")
            run_id = result.json()["id"]
            path = f"/approval-runs/{run_id}/decision"
            self.assertEqual(self.client.post(path, headers=headers, json={"approved": True}).json()["status"], "completed")
            self.assertEqual(self.client.post(path, headers=headers, json={"approved": True}).status_code, 409)
