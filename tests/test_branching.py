"""
Unit tests for B-Frame Ephemeral Branching Sandbox.
"""

import unittest
from timemeshin import TimeMeshinClient


class TestBranching(unittest.TestCase):

    def setUp(self):
        self.client = TimeMeshinClient(db_path=":memory:")
        # Base state
        self.client.ingest("Switched primary database from Postgres to DynamoDB", timestamp="2026-09-08 10:00:00")
        self.client.ingest("Reduced database max_connections 100 -> 20", timestamp="2026-09-08 14:50:00")

    def test_ephemeral_branch_sandbox_and_discard(self):
        # Base state at 15:00 has max_connections=20
        base_kf = self.client.scrub(playhead="2026-09-08 15:00:00")
        self.assertEqual(base_kf.get_entity_state("database")["max_connections"], "20")

        # Spawn ephemeral branch to test rollback
        with self.client.branch(from_playhead="2026-09-08 15:00:00", name="test_rollback") as sim:
            sim.ingest_hypothetical(
                entity="database",
                attribute="max_connections",
                v_new="100",
                v_old="20",
                causal_rationale="Testing rollback of connection limit"
            )
            sim_kf = sim.scrub()
            self.assertEqual(sim_kf.get_entity_state("database")["max_connections"], "100")
            # Auto-discard on exit without commit

        # Ground truth main timeline must remain untouched!
        main_kf = self.client.scrub(playhead="2026-09-08 15:00:00")
        self.assertEqual(main_kf.get_entity_state("database")["max_connections"], "20")

    def test_ephemeral_branch_commit_to_main(self):
        # Spawn branch and commit
        branch = self.client.branch(from_playhead="2026-09-08 15:00:00", name="prod_fix")
        branch.ingest_hypothetical(
            entity="database",
            attribute="max_connections",
            v_new="100",
            v_old="20",
            causal_rationale="Fixing connection starvation"
        )
        # Evaluate hypothesis
        passed = branch.evaluate_hypothesis(lambda state: state["database"]["max_connections"] == "100")
        self.assertTrue(passed)

        # Commit to main
        branch.commit_to_main(target_timestamp="2026-09-08 15:10:00")

        # Verify ground truth updated after 15:10
        updated_kf = self.client.scrub(playhead="2026-09-08 15:15:00")
        self.assertEqual(updated_kf.get_entity_state("database")["max_connections"], "100")


if __name__ == "__main__":
    unittest.main()
