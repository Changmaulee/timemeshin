"""
Tests for Production-Hardened Vectors in TimeMeshin v0.2.1:
1. Spurious Causal Correlation Prevention (Topological Entity Scoping)
2. Ghost Rebase & OCC Epoch Conflict Detection (BranchConflictError)
3. Two-Speed Ingestion Protocol (Fast-Path WAL & Async Refinement)
"""

import unittest
from timemeshin import TimeMeshinClient, BranchConflictError, StateDelta, SemanticEvent


class TestProductionHardening(unittest.TestCase):

    def setUp(self):
        self.client = TimeMeshinClient(db_path=":memory:", causal_threshold=0.50)

    def test_spurious_correlation_rejection(self):
        # Scenario: Two concurrent PRs, one unrelated to backend outage
        # 14:40 - PR #401 merged: Update frontend button CSS (Unrelated)
        # 14:42 - PR #402 merged: auth_service updated (Related)
        # 14:50 - DB max_connections reduced
        # 15:00 - HTTP 504 Gateway Timeouts
        self.client.ingest("PR #401 merged: update frontend button CSS styling", timestamp="2026-09-08 14:40:00", rack="Code")
        self.client.ingest("PR #402 merged (auth_service updated)", timestamp="2026-09-08 14:42:00", rack="Code")
        self.client.ingest("Reduced database max_connections 100 -> 20", timestamp="2026-09-08 14:50:00", rack="Infra")
        self.client.ingest("HTTP 504 Gateway Timeouts detected on API gateway", timestamp="2026-09-08 15:00:00", rack="Observability")

        # Trace root cause for API gateway
        chain = self.client.trace("api_gateway", playhead="2026-09-08 15:05:00")
        chain_entities = [d.entity.lower() for d in chain]

        # Verify auth_service and database are in the causal lineage, but PR #401 (frontend CSS) is EXCLUDED!
        self.assertIn("database", chain_entities)
        self.assertIn("auth_service", chain_entities)
        self.assertNotIn("pr_401", chain_entities)

    def test_ghost_rebase_and_occ_conflict_detection(self):
        # Base setup
        self.client.ingest("Switched primary database from Postgres to DynamoDB", timestamp="2026-09-08 10:00:00")
        self.client.ingest("Reduced database max_connections 100 -> 20", timestamp="2026-09-08 11:00:00")

        # Agent spawns branch at 12:00
        branch = self.client.branch(from_playhead="2026-09-08 12:00:00", name="agent_worker")
        branch.ingest_hypothetical(
            entity="database",
            attribute="max_connections",
            v_new="100",
            causal_rationale="Simulating fix"
        )

        # While agent is working, a retroactive/out-of-order delta mutates the underlying timeline at 10:30
        self.client.ingest("Set database pool_timeout from 30s to 60s", timestamp="2026-09-08 10:30:00")

        # Attempting to commit branch without rebase MUST raise BranchConflictError
        with self.assertRaises(BranchConflictError):
            branch.commit_to_main(target_timestamp="2026-09-08 12:30:00")

        # After rebase, commit succeeds!
        branch.rebase()
        committed = branch.commit_to_main(target_timestamp="2026-09-08 12:30:00")
        self.assertEqual(len(committed), 1)

    def test_two_speed_ingestion_protocol(self):
        # 1. Fast path ingestion (<2ms write-ahead append)
        ev = self.client.fast_ingest("Reduced database max_connections 100 -> 20", timestamp="2026-09-08 14:50:00")
        self.assertIsInstance(ev, SemanticEvent)
        self.assertTrue(ev.metadata.get("needs_refinement"))

        # 2. Refinement pass (background worker processing)
        refined_deltas = self.client.refine_pending_events()
        self.assertEqual(len(refined_deltas), 1)
        self.assertEqual(refined_deltas[0].entity, "database")
        self.assertEqual(refined_deltas[0].v_new, "20")

        # Verify state is updated in keyframe
        kf = self.client.scrub("2026-09-08 15:00:00")
        self.assertEqual(kf.get_entity_state("database")["max_connections"], "20")


if __name__ == "__main__":
    unittest.main()
