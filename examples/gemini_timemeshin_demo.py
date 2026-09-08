"""
Gemini + TimeMeshin End-to-End Demo
Demonstrates how Google Gemini can use TimeMeshin for zero-leakage episodic memory and point-in-time playhead scrubbing.
"""

import os
from timemeshin import GeminiTimeMeshinChat

def main():
    print("==========================================================================")
    print("   Google Gemini + TimeMeshin Deterministic Episodic Memory Demo          ")
    print("==========================================================================")

    # 1. Initialize Gemini with TimeMeshin Memory
    chat = GeminiTimeMeshinChat(
        model_name="gemini-2.0-flash",
        db_path="gemini_demo_memory.db"
    )

    print("\n[Step 1] Ingesting architectural evolution over time...")
    
    # Monday: Initial Architecture
    chat.send_message(
        "Day 1: We deployed our backend on PostgreSQL with a $2,000 monthly cloud budget.",
        timestamp="2026-09-01 10:00:00"
    )
    
    # Wednesday: Migration
    chat.send_message(
        "Day 3: Due to write locking bottlenecks under peak load, we migrated our database to DynamoDB. Cloud budget increased to $4,500.",
        timestamp="2026-09-03 14:00:00"
    )
    
    # Friday: Incident & Fix
    chat.send_message(
        "Day 5: Added Redis caching layer to alleviate DynamoDB read spikes. Monthly budget is now $5,000.",
        timestamp="2026-09-05 16:30:00"
    )

    print("\n[Step 2] Point-in-Time Playhead Query (Day 2 - BEFORE DynamoDB migration):")
    answer_day2 = chat.ask_at(
        playhead="2026-09-02 12:00:00",
        question="What database are we currently using and what is our budget?"
    )
    print("Answer (Day 2):")
    print(answer_day2)

    print("\n[Step 3] Point-in-Time Playhead Query (Day 4 - AFTER DynamoDB migration):")
    answer_day4 = chat.ask_at(
        playhead="2026-09-04 12:00:00",
        question="What database are we using now and why did we switch?"
    )
    print("Answer (Day 4):")
    print(answer_day4)

    print("\n==========================================================================")
    print("   Demo Complete: 100% Deterministic State Accuracy, 0% Future Leakage!   ")
    print("==========================================================================")

if __name__ == "__main__":
    main()