"""
Real-World Test: Ingesting Conversation 32819188-4fcd-41ab-bcc5-29cd0acd9298 into ChronoMesh
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

CONV_ID = "32819188-4fcd-41ab-bcc5-29cd0acd9298"
TRANSCRIPT_PATH = Path(rf"C:\Users\moule\.gemini\antigravity\brain\{CONV_ID}\.system_generated\logs\transcript.jsonl")


def main():
    print("=" * 80)
    print(f"🎬 CHRONOMESH AUDIT: CONVERSATION [{CONV_ID}]")
    print("=" * 80)

    if not TRANSCRIPT_PATH.exists():
        print(f"[!] Transcript not found at {TRANSCRIPT_PATH}")
        return

    db_file = f"conv_{CONV_ID[:8]}.db"
    client = ChronoMeshClient(db_path=db_file)

    print(f"[+] Reading transcript file: {TRANSCRIPT_PATH}")
    steps = []
    with open(TRANSCRIPT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    steps.append(json.loads(line))
                except Exception:
                    pass

    print(f"✅ Loaded {len(steps)} raw log steps.")

    # Ingest turns
    user_turns = 0
    assistant_turns = 0
    
    print("\n[+] Ingesting conversation stream into ChronoMesh Spatio-Temporal Index...")
    
    for step in steps:
        step_type = step.get("type")
        source = step.get("source")
        created_at_str = step.get("created_at")
        content = step.get("content", "")

        if not created_at_str or not content or step_type not in ["USER_INPUT", "PLANNER_RESPONSE"]:
            continue

        try:
            clean_ts = created_at_str.split(".")[0].replace("Z", "")
            t = datetime.fromisoformat(clean_ts)
        except Exception:
            continue

        role = "User" if source == "USER_EXPLICIT" or step_type == "USER_INPUT" else "Assistant"
        if role == "User":
            user_turns += 1
        else:
            assistant_turns += 1

        summary = content[:400].replace("\n", " ").strip()
        client.ingest(f"[{role}]: {summary}", timestamp=t)

    total_deltas = len(client.engine.deltas)
    print(f"✅ Ingestion Complete!")
    print(f"   • Total Dialogue Turns Ingested : {user_turns + assistant_turns} (User: {user_turns}, Assistant: {assistant_turns})")
    print(f"   • Total ChronoMesh Deltas Formed: {total_deltas}")
    print(f"   • Total Keyframes Compiled      : {len(client.engine.keyframes)}")

    if not client.engine.deltas:
        print("[!] No timestamped deltas extracted.")
        return

    # Timeline bounds
    t_start = client.engine.deltas[0].timestamp
    t_end = client.engine.deltas[-1].timestamp
    duration_min = (t_end - t_start).total_seconds() / 60

    print(f"   • Timeline Window               : {t_start.strftime('%Y-%m-%d %H:%M:%S')} ➔ {t_end.strftime('%Y-%m-%d %H:%M:%S')} ({duration_min:.1f} mins)")

    # --------------------------------------------------------------------------
    # PLAYHEAD SCRUBPING ACROSS 4 TIMELINE STATIONS
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("⏱️ PLAYHEAD SCRUBBING AUDIT (4 STATIONS ALONG THE TIMELINE)")
    print("=" * 80)

    checkpoints = [
        ("Station 1: 0% (Start of Session)", t_start),
        ("Station 2: 33% (Early Discussion)", t_start + (t_end - t_start) * 0.33),
        ("Station 3: 66% (Deep Work Phase)", t_start + (t_end - t_start) * 0.66),
        ("Station 4: 100% (Session Close)", t_end)
    ]

    for label, checkpoint_time in checkpoints:
        print(f"\n📍 {label} [Playhead: {checkpoint_time.strftime('%H:%M:%S')}]:")
        state = client.scrub(checkpoint_time)
        print(f"   • Active State: {json.dumps(state, indent=4)}")

    # --------------------------------------------------------------------------
    # DUAL-COORDINATE SEARCH OVER EXTERNAL CHAT
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("🔍 DUAL-COORDINATE (S x T) QUERY AUDIT")
    print("=" * 80)

    # Sample query across external chat
    q = "What was the main topic or task discussed?"
    res = client.query(q, playhead=t_end, top_k=3)
    print(f"❓ Query: \"{q}\"")
    print(f"🎬 Playhead Locked At: {res['playhead_time']}")
    print("📌 Top Relevant Historical Turns:")
    for ev in res["relevant_events"]:
        print(f"   • [{ev['timestamp']}] Sim: {ev['similarity']} | Text: {ev['raw_text'][:120]}...")

    print("\n" + "=" * 80)
    print(f"🌟 AUDIT OF [{CONV_ID}] COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    main()
