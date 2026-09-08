import os
import unittest
import tempfile
import shutil
from datetime import datetime
from timemeshin import TimeMeshinClient
from timemeshin.server.app import app
from fastapi.testclient import TestClient

class TestTimeMeshinCore(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_file = os.path.join(self.test_dir, "test_ci.db")
        self.client = TimeMeshinClient(db_path=self.db_file)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_ingestion_and_fencing(self):
        # Ingest Day 1
        self.client.ingest_event(
            timestamp="2026-09-01 10:00:00",
            rack="Infrastructure",
            entity="Database",
            value="PostgreSQL",
            reason="Initial setup"
        )
        # Ingest Day 2
        self.client.ingest_event(
            timestamp="2026-09-02 12:00:00",
            rack="Infrastructure",
            entity="Database",
            value="DynamoDB",
            reason="Lock contention"
        )

        # Scrub Day 1 (before Day 2)
        s1 = self.client.scrub(playhead="2026-09-01 18:00:00")
        db1 = s1.get("Database", {}).get("state", s1.get("Database"))
        self.assertEqual(db1, "PostgreSQL")

        # Scrub Day 2 (after switch)
        s2 = self.client.scrub(playhead="2026-09-02 18:00:00")
        db2 = s2.get("Database", {}).get("state", s2.get("Database"))
        self.assertEqual(db2, "DynamoDB")

    def test_dual_coordinate_query(self):
        self.client.ingest_event(
            timestamp="2026-09-01 10:00:00",
            rack="Security",
            entity="Auth",
            value="OAuth2",
            reason="Modern auth"
        )
        res = self.client.query_at(timestamp="2026-09-01 12:00:00", query="auth")
        self.assertIn("state", res)
        self.assertGreaterEqual(res["events_count"], 1)

    def test_fastapi_endpoints(self):
        test_client = TestClient(app)
        resp = test_client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "healthy")

if __name__ == "__main__":
    unittest.main()
