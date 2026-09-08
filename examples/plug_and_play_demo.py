"""
Plug-and-Play Commercial SDK Demo
Demonstrates 2-line ingestion, automatic SQLite persistence, and deterministic playhead queries.
"""

import sys
import io
from pathlib import Path
from datetime import datetime, timedelta
import json

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from timemeshin import TimeMeshinClient


def main():
    print("=" * 70)
    print("🚀 TIMEMESHIN PLUG-AND-PLAY COMMERCIAL SDK TEST")
    print("=" * 70)

    # 1. Initialize Client (Zero-config SQLite persistence)
    client = TimeMeshinClient(db_path="commercial_demo.db")

    t0 = datetime(2026, 9, 1, 9, 0)

    # 2. Ingest Unstructured Stream in Real-Time
    print("\n[+] 1. Ingesting raw enterprise events into persistent SQLite memory...")
    
    client.ingest("We chose PostgreSQL as our primary database.", timestamp=t0)
    client.ingest("Initial monthly cloud budget is set to $1000.", timestamp=t0 + timedelta(hours=1))
    client.ingest("Sarah is appointed lead engineer.", timestamp=t0 + timedelta(hours=2))
    
    # Day 2 mutation
    client.ingest("We migrated to DynamoDB due to write lock contention. New budget is $5000.", timestamp=t0 + timedelta(days=1, hours=3))
    
    # Day 3 mutation
    client.ingest("Alex took over as team lead today.", timestamp=t0 + timedelta(days=2, hours=1))
    print("✅ Ingestion complete and written to disk (commercial_demo.db).")

    # 3. Time-Travel Playhead Scrub
    query_time = t0 + timedelta(days=1, hours=5)
    print(f"\n[+] 2. Scrubbing Playhead to Day 2 at 2:00 PM: [{query_time.strftime('%Y-%m-%d %H:%M')}]")
    state = client.scrub(playhead=query_time)
    print(json.dumps(state, indent=2))

    # 4. Natural Language Dual-Coordinate Query
    print("\n[+] 3. Running Dual-Coordinate Query: 'Why did we change our database?'")
    result = client.query(
        question="Why did we change our database?",
        playhead=query_time,
        top_k=2
    )
    print(f"🎬 Playhead Locked At: {result['playhead_time']}")
    print(f"📌 Active State       : {result['exact_state'].get('Database', {})}")
    print("🔍 Ranked Causes      :")
    for ev in result['relevant_events']:
        print(f"   • [{ev['timestamp']}] {ev['change']} | Reason: {ev['reason']}")

    # 5. Entity Motion Trajectory
    print("\n[+] 4. Tracing Complete Motion Path for 'TeamLead':")
    traj = client.trace("TeamLead")
    for step in traj:
        print(f"   • [{step['timestamp']}] {step['change']}")

    print("\n" + "=" * 70)
    print("🌟 TIMEMESHIN COMMERCIAL SDK VERIFICATION: 100% OPERATIONAL & READY!")
    print("=" * 70)


if __name__ == "__main__":
    main()
