"""
Unit tests for TimeMeshin Core Engine, Extractor, and S x T Querying.
"""

import unittest
from timemeshin import TimeMeshinClient, Modality, StateDelta, SemanticEvent


class TestTimeMeshinEngine(unittest.TestCase):

    def setUp(self):
        self.client = TimeMeshinClient(db_path=":memory:")

    def test_zero_etl_extractor_and_ingest(self):
        # 1. Ingest unstructured text with state change
        items = self.client.ingest(
            "Switched primary database from Postgres to DynamoDB due to write lock contention.",
            timestamp="2026-09-08 10:00:00"
        )
        self.assertEqual(len(items), 1)
        self.assertIsInstance(items[0], StateDelta)
        self.assertEqual(items[0].entity, "database")
        self.assertEqual(items[0].v_old, "Postgres")
        self.assertEqual(items[0].v_new, "DynamoDB")

        # 2. Ingest generic unstructured prose (fallback to SemanticEvent)
        events = self.client.ingest(
            "Weekly team sync: discussed quarterly OKRs and planned migration schedule.",
            timestamp="2026-09-08 11:00:00"
        )
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], SemanticEvent)
        self.assertIn("migration", events[0].topics)

    def test_temporal_fence_and_keyframe_folding(self):
        # Timeline of mutations
        self.client.ingest("Set rate_limit max_requests from 100 to 500", timestamp="2026-09-08 09:00:00")
        self.client.ingest("Switched primary database from Postgres to DynamoDB", timestamp="2026-09-08 10:00:00")
        self.client.ingest("Updated rate_limit max_requests from 500 -> 1000", timestamp="2026-09-08 12:00:00")
        self.client.ingest("Switched primary database from DynamoDB to Aurora", timestamp="2026-09-08 15:00:00")

        # Scrub at t = 10:30 (before Aurora and before rate_limit=1000)
        kf_1030 = self.client.scrub(playhead="2026-09-08 10:30:00")
        db_state = kf_1030.get_entity_state("database")
        rl_state = kf_1030.get_entity_state("rate_limit")

        self.assertIsNotNone(db_state)
        self.assertEqual(db_state.get("engine"), "DynamoDB")
        self.assertIsNotNone(rl_state)
        self.assertEqual(rl_state.get("max_requests"), "500")

        # Scrub at t = 16:00 (after Aurora and rate_limit=1000)
        kf_1600 = self.client.scrub(playhead="2026-09-08 16:00:00")
        self.assertEqual(kf_1600.get_entity_state("database").get("engine"), "Aurora")
        self.assertEqual(kf_1600.get_entity_state("rate_limit").get("max_requests"), "1000")

    def test_st_bihalo_query(self):
        self.client.ingest("Switched primary database from Postgres to DynamoDB due to high write contention.", timestamp="2026-09-08 10:00:00")
        self.client.ingest("Reduced database max_connections 100 -> 20", timestamp="2026-09-08 14:50:00")

        # Query at t = 11:00 (max_connections must not leak!)
        res_early = self.client.query("Why did we change the database?", playhead="2026-09-08 11:00:00")
        self.assertIn("DynamoDB", res_early["compiled_prompt_context"])
        self.assertNotIn("max_connections", res_early["compiled_prompt_context"])

        # Query at t = 15:00
        res_late = self.client.query("Why did we reduce connections?", playhead="2026-09-08 15:00:00")
        self.assertIn("max_connections", res_late["compiled_prompt_context"])


if __name__ == "__main__":
    unittest.main()
