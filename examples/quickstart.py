"""
TimeMeshin Quickstart Example
Demonstrates basic usage of Keyframes, Deltas, Playhead Scrubbing, and Entity Tracing.
"""

from datetime import datetime, timedelta
import json
import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from timemeshin import DeltaFrame, TimeMeshinEngine


def dummy_embed(text: str) -> np.ndarray:
    """Mock 384-d vector for fast local demo."""
    rng = np.random.RandomState(abs(hash(text)) % (2**32))
    v = rng.randn(384)
    return v / np.linalg.norm(v)


def main():
    print("[*] Initializing TimeMeshin Engine...")
    engine = TimeMeshinEngine(keyframe_interval_days=2)

    t0 = datetime(2026, 9, 1, 9, 0)

    # 1. Append Stream Events
    events = [
        (t0, "Database", "Infra", "Engine", "None", "PostgreSQL", "Initial architecture choice", "We deployed PostgreSQL on AWS RDS."),
        (t0 + timedelta(hours=3), "TeamLead", "Org", "Person", "None", "Sarah", "Appointed tech lead", "Sarah is leading backend engineering."),
        (t0 + timedelta(days=1, hours=4), "Database", "Infra", "Engine", "PostgreSQL", "DynamoDB", "Write contention under load", "Migrated database to DynamoDB."),
        (t0 + timedelta(days=2, hours=1), "TeamLead", "Org", "Person", "Sarah", "Alex", "Leadership handoff", "Alex took over lead engineer role.")
    ]

    for t, entity, rack, attr, old_v, new_v, reason, text in events:
        delta = DeltaFrame(
            timestamp=t,
            entity_id=entity,
            topic_rack=rack,
            attribute=attr,
            old_value=old_v,
            new_value=new_v,
            causal_reason=reason,
            raw_text=text,
            embedding=dummy_embed(f"{entity} {attr} {reason}")
        )
        engine.record_delta(delta)

    # Build periodic Keyframes (I-Frames)
    engine.build_periodic_keyframes()
    print("[+] Recorded events and compiled periodic keyframes.\n")

    # 2. Point-in-Time Scrubbing
    scrub_time = t0 + timedelta(days=1, hours=8)
    print(f"--> Scrubbing Playhead to: {scrub_time.strftime('%Y-%m-%d %H:%M')}")
    state = engine.scrub_state(scrub_time)
    print(json.dumps(state, indent=2))

    # 3. Entity Trajectory
    print("\n--> Tracing Trajectory for 'Database':")
    trajectory = engine.trace_entity("Database")
    for step in trajectory:
        print(f"  * [{step['timestamp']}] {step['change']} | Reason: {step['reason']}")


if __name__ == "__main__":
    main()
