---
name: timemeshin
description: >-
  Deterministic Spatio-Temporal (Semantics x Timeline) Video-Scrubber Context Engine for Antigravity.
  Use when tracking evolving project architectures, configuration state mutations, causal decision histories,
  or when retrieving point-in-time ground truth across multi-step development sessions.
---

# TimeMeshin: Antigravity Episodic Memory & Timeline Skill

This skill equips Antigravity with **TimeMeshin**-the deterministic spatio-temporal context engine that tracks state mutations like a video file with **I-Frames (Keyframes)**, **P-Frames (Deltas)**, and a **Reversible Playhead Scrubber**.

---

## When to Use This Skill

1. **Stateful Project History:** Tracking architectural migrations, dependency changes, and active configurations over time without hallucinating past/future states.
2. **Point-in-Time Auditing:** When the user asks: *"What was our database choice on Day 2?"* or *"What was the configuration before we refactored?"*
3. **Causal Reasoning & Root Cause Analysis:** Tracing *why* a decision or breaking change occurred using the Transitive Causal DAG.
4. **Retroactive Time Splicing:** Splicing late-arriving logs/notes into the past using Git-rebase keyframe re-compaction.

---

## Quick Python Usage within Antigravity

```python
from timemeshin import TimeMeshinClient

# 1. Initialize Memory Engine (persistent SQLite storage)
client = TimeMeshinClient(db_path="timemeshin_memory.db")

# 2. Record State Mutation (Delta)
client.ingest("Switched primary database from Postgres to DynamoDB due to write lock contention.")

# 3. Scrub Playhead to any Timestamp
state = client.scrub(playhead="2026-09-08 14:00")

# 4. Dual-Coordinate Query (Semantics x Timeline)
result = client.query("Why did we change the database?", playhead="2026-09-08 14:00")

# 5. Entity Trajectory
history = client.trace("Database")
```

---

## Core Principles

* **Coordinate T (Temporal Fence):** Always bounds candidate retrieval to <= t_playhead to guarantee 0% future-data leakage.
* **Coordinate S (Semantic Ranking):** Ranks historical causal deltas leading up to the playhead using dense cosine similarity.
* **Modality Support:** Distinguishes COMMITTED facts from EVALUATING trials and PROPOSED ideas.