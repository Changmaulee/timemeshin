"""
Unit tests for Automated Causal DAG Discovery and Multi-Hop Traversal.
"""

import unittest
from timemeshin import TimeMeshinClient


class TestCausalityDAG(unittest.TestCase):

    def setUp(self):
        self.client = TimeMeshinClient(db_path=":memory:", causal_threshold=0.45)

    def test_automated_causal_discovery_and_multihop_trace(self):
        # Scenario: Outage chain
        # 14:42 - Code: PR #402 merged (auth_service updated)
        # 14:50 - Infra: DB max_connections reduced 100 -> 20
        # 15:00 - Observability: HTTP 504 Gateway Timeouts detected
        self.client.ingest("PR #402 merged (auth_service updated)", timestamp="2026-09-08 14:42:00", rack="Code")
        self.client.ingest("Reduced database max_connections 100 -> 20", timestamp="2026-09-08 14:50:00", rack="Infra")
        self.client.ingest("HTTP 504 Gateway Timeouts detected on API gateway", timestamp="2026-09-08 15:00:00", rack="Observability")

        # Trace root cause for the 504 outage
        chain = self.client.trace("api_gateway", playhead="2026-09-08 15:05:00")
        self.assertGreaterEqual(len(chain), 2)

        # Check prompt formatting
        prompt = self.client.trace_prompt("HTTP 504 Outage", "api_gateway", playhead="2026-09-08 15:05:00")
        self.assertIn("CAUSAL TIMELINE", prompt)
        self.assertIn("max_connections", prompt)


if __name__ == "__main__":
    unittest.main()
