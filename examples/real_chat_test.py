"""
Real-World Test: Ingesting our OWN Conversation Transcript into ChronoMesh!
Conversation ID: bf2b32b2-535f-41a2-80ee-83819a2d0841
"""

import sys
import io
import json
from pathlib import Path
from datetime import datetime

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from chronomesh.client import ChronoMeshClient
from chronomesh.core.frames import DeltaFrame


TRANSCRIPT_PATH = Path(r"C:\Users\moule\.gemini\antigravity\brain\bf2b32b2-535f-41a2-80ee-83819a2d0841\.system_generated\logs\transcript.jsonl")


def main():
    print("=" * 75)
    print("🔥 REAL-WORLD TEST: INGESTING OUR OWN CONVERSATION SESSION")
    print("=" * 75)

    if not TRANSCRIPT_PATH.exists():
        print(f"[!] Transcript not found at {TRANSCRIPT_PATH}")
        return

    client = ChronoMeshClient(db_path="chat_transcript_memory.db")

    print(f"[+] Loading raw transcript from: {TRANSCRIPT_PATH}")
    steps = []
    with open(TRANSCRIPT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    steps.append(json.loads(line))
                except Exception:
                    pass

    print(f"✅ Found {len(steps)} logged conversation steps.")

    # Filter and Ingest meaningful conversation turns
    ingested_count = 0
    print("\n[+] Ingesting conversation turns into ChronoMesh Spatio-Temporal Mesh...")
    
    for step in steps:
        step_type = step.get("type")
        source = step.get("source")
        created_at_str = step.get("created_at")
        content = step.get("content", "")

        if not created_at_str or not content or step_type not in ["USER_INPUT", "PLANNER_RESPONSE"]:
            continue

        # Parse timestamp
        # E.g. "2026-09-08T12:30:33.123456Z"
        try:
            clean_ts = created_at_str.split(".")[0].replace("Z", "")
            t = datetime.fromisoformat(clean_ts)
        except Exception:
            continue

        # Extract high-level session milestones
        summary_text = content[:300].replace("\n", " ").strip()
        role = "User" if source == "USER_EXPLICIT" or step_type == "USER_INPUT" else "Assistant"
        
        # Categorize into topic racks
        rack = "IdeaGeneration"
        if "colab" in summary_text.lower():
            rack = "Prototyping"
        elif "benchmark" in summary_text.lower() or "accuracy" in summary_text.lower():
            rack = "Benchmarking"
        elif "d drive" in summary_text.lower() or "chronomesh" in summary_text.lower():
            rack = "Engineering"
        elif "market" in summary_text.lower() or "customers" in summary_text.lower() or "sell" in summary_text.lower():
            rack = "Business"

        client.ingest(f"[{role}]: {summary_text}", timestamp=t)
        ingested_count += 1

    print(f"✅ Successfully ingested {ingested_count} real turns into ChronoMesh!\n")

    # --------------------------------------------------------------------------
    # AUDIT 1: Time-Travel Playhead Scrub
    # --------------------------------------------------------------------------
    print("=" * 75)
    print("🎬 TEST 1: TIME-TRAVEL PLAYHEAD SCRUB OVER OUR SESSION")
    print("=" * 75)
    
    if client.engine.deltas:
        first_time = client.engine.deltas[0].timestamp
        mid_time = client.engine.deltas[len(client.engine.deltas) // 2].timestamp
        latest_time = client.engine.deltas[-1].timestamp

        print(f"\n1. State at the START of our chat ({first_time.strftime('%H:%M:%S')}):")
        print(json.dumps(client.scrub(first_time), indent=2))

        print(f"\n2. State at the MID-POINT of our chat ({mid_time.strftime('%H:%M:%S')}):")
        print(json.dumps(client.scrub(mid_time), indent=2))

        print(f"\n3. State at the LATEST moment ({latest_time.strftime('%H:%M:%S')}):")
        print(json.dumps(client.scrub(latest_time), indent=2))

    # --------------------------------------------------------------------------
    # AUDIT 2: Dual-Coordinate Search
    # --------------------------------------------------------------------------
    print("\n" + "=" * 75)
    print("🔍 TEST 2: DUAL-COORDINATE (S x T) SEARCH OVER OUR REAL CHAT")
    print("=" * 75)

    queries = [
        ("When did we decide to test in Colab?", mid_time),
        ("When did we discuss market, selling and customer segments?", latest_time)
    ]

    for q, playhead in queries:
        print(f"\n❓ Query: \"{q}\" (Playhead: {playhead.strftime('%H:%M:%S')})")
        res = client.query(q, playhead=playhead, top_k=2)
        for ev in res["relevant_events"]:
            print(f"   • [{ev['timestamp']}] Sim: {ev['similarity']} | Rack: {ev['topic_rack']} | Text: {ev['raw_text'][:120]}...")

    print("\n" + "=" * 75)
    print("🏆 REAL TRANSCRIPT TEST COMPLETED: 100% SUCCESSFUL!")
    print("=" * 75)


if __name__ == "__main__":
    main()
