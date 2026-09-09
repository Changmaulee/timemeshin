# TimeMeshin (v0.2.1)
> **Deterministic Spatio-Temporal ($S \times T$) Context Engine & Episodic Memory Substrate for AI Agents**  
> *Authored by Chandramouli ([@Changmaulee](https://github.com/Changmaulee)) &bull; Contact: [yellowbridgeconnections@gmail.com](mailto:yellowbridgeconnections@gmail.com)*

[![License](https://img.shields.io/badge/License-FSL--1.1--Apache--2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-brightgreen.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-passing-success.svg)](https://github.com/Changmaulee/timemeshin)
[![Architecture](https://img.shields.io/badge/Architecture-S%20x%20T%20Dual--Coordinate-orange.svg)](#core-architecture)

---

## 🚀 Overview

**TimeMeshin** is a spatio-temporal episodic memory engine engineered specifically to solve **temporal blindness, state drift, conflicting context clutter, and causal opacity** in long-horizon AI agent loops and stateful RAG systems.

Standard Vector DBs and agent memory frameworks perform flat semantic search. When an agent queries past states, flat similarity frequently retrieves post-hoc data from future steps, causing **future-data contamination**, **dirty rollbacks**, and **hallucinated memory states**.

TimeMeshin treats agent context like a **video stream**:
* **I-Frames (Keyframes):** Consolidated point-in-time ground truth states.
* **P-Frames (Deltas):** Causal state mutations and diffs leading up to the playhead.
* **B-Frames (Ephemeral Sandboxes):** In-memory speculative execution branches guarded by **Optimistic Concurrency Control (OCC)**.
* **Temporal Playhead Scrubber:** Mathematically bounds candidate retrieval to $t \le t_{\text{playhead}}$ with **0% future-data leakage guaranteed**.

---

## ⚡ Quickstart (5 Lines of Code)

### Installation
```bash
pip install timemeshin
```

### Basic Usage
```python
from timemeshin import TimeMeshinClient

# 1. Initialize persistent memory substrate (100% local-first SQLite)
client = TimeMeshinClient(db_path="timemeshin_memory.db")

# 2. Ingest unformatted engineering logs, PRs, or agent tool outputs
client.ingest("Switched primary database from Postgres to DynamoDB due to write lock contention.", timestamp="2026-09-08 11:30:00")
client.ingest("Reduced database max_connections 100 -> 20 to preserve cloud resources.", timestamp="2026-09-08 14:50:00")

# 3. Deterministic Point-in-Time Scrubbing (I-Frame Keyframe Consolidation)
state = client.scrub(playhead="2026-09-08 12:00:00")
# Active state at 12:00: database.engine='DynamoDB', database.max_connections='100'

# 4. Multi-Hop Causal Root-Cause Trace
prompt = client.trace_prompt("HTTP 504 Outage", target_id_or_entity="database")

# 5. Ephemeral B-Frame Sandbox (Simulate rollbacks with OCC without dirtying main memory)
with client.branch(from_playhead="2026-09-08 15:00:00", name="test_rollback") as sim:
    sim.ingest_hypothetical(
        entity="database",
        attribute="max_connections",
        v_new="100",
        causal_rationale="Simulated rollback of connection limit"
    )
    assert sim.scrub().get_entity_state("database")["max_connections"] == "100"
    # Auto-discarded upon exit with 0 disk pollution!
```

---

## 🏛️ Core Architecture

```
                                [INCOMING RAW LOG / AGENT STREAM]
                                                │
                ┌───────────────────────────────┴───────────────────────────────┐
                ▼                                                               ▼
        [1. FAST PATH (<2ms)]                                       [2. ASYNC REFINEMENT WORKER]
   Write-Ahead Append: SQLite Event Table                        SLM Grammar Extractor & Structuring
                │                                                               │
                └───────────────────────────────┬───────────────────────────────┘
                                                │
                                [3. TOPOLOGICAL CAUSAL SCOPING]
                                ├── Entity Dependency Graph (e.g. auth_service -> auth_db)
                                └── Calibrated NLI Score: P(Entailment) - P(Contradiction) >= 0.85
                                                │
                                [4. B-FRAME OCC EPOCH TRACKER]
                                ├── Base Epoch Hash at t_branch
                                └── Conflict Detection on commit_to_main()
```

### 1. Two-Speed Ingestion & Zero-ETL Delta Extractor
* **Fast-Path Sync (`<2ms`):** Appends raw unparsed prose directly to SQLite Write-Ahead Log as a `SemanticEvent`.
* **Refinement Worker:** Extracts structured state deltas ($\Delta = \langle t, e, r, a, v_{\text{old}}, v_{\text{new}}, c_i, \text{modality} \rangle$) and compacts Keyframes without blocking write throughput.

### 2. $S \times T$ Hybrid Bihalo Index & Scrubber
* **Coordinate $T$ (Temporal Fence):** Strictly masks $t > t_{\text{playhead}}$ to guarantee **0% future-data leakage**.
* **Keyframe State Consolidation ($I$-Frames):** Collapses historical $P$-Frames into a single, unambiguous active entity state table.
* **Coordinate $S$ (Semantic Ranking):** Ranks historical causal rationales and state transitions using dense cosine similarity.

---

## 📊 Comparison: TimeMeshin vs. Traditional Memory

| Feature | Standard Vector DBs (Pinecone/Chroma) | Traditional Agent Memory (Mem0 / Zep) | TimeMeshin (v0.2.1) |
| :--- | :--- | :--- | :--- |
| **Temporal Bounding ($t \le t_{\text{playhead}}$)** | ❌ None (Semantic only) | ❌ Approximate / recency bias | ✅ **100% Deterministic Fence** |
| **Future-Data Leakage Prevention** | ❌ Leaks future chunks | ❌ No point-in-time isolation | ✅ **Guaranteed 0% Leakage** |
| **Point-in-Time Keyframe Scrubbing** | ❌ None | ❌ None | ✅ **I-Frame / P-Frame Deltas** |
| **Hypothetical Sandbox Branching** | ❌ Pollutes database | ❌ Pollutes user memory | ✅ **B-Frames with OCC** |
| **Causal Root Cause Discovery** | ❌ Unstructured snippets | ❌ Flat associations | ✅ **Topological Causal DAG** |
| **Deployment Model** | Cloud-dependent | Cloud or self-hosted | ✅ **100% Local-First (SQLite/DuckDB)** |

---

## 🛠️ Modality Lifecycle

TimeMeshin supports explicit state verification modes:
* `COMMITTED`: Ground truth verified state changes.
* `EVALUATING`: Trial modifications undergoing test validation.
* `PROPOSED`: Speculative changes suggested by planner agents.
* `HYPOTHETICAL`: Sandbox simulations in temporary B-Frames.

---

## 💼 Enterprise & Production Integration Sprints

Building an autonomous coding agent, DevOps copilot, or stateful RAG pipeline? We offer **2-Week Guided Integration Sprints** to:
* Audit your agent memory pipeline and eliminate state drift.
* Implement custom Zero-ETL ingestion and $S \times T$ dual-coordinate retrieval.
* Setup B-Frame sandboxes with Optimistic Concurrency Control.

📩 **Get in Touch:** [yellowbridgeconnections@gmail.com](mailto:yellowbridgeconnections@gmail.com)  
👤 **Author:** Chandramouli ([@Changmaulee](https://github.com/Changmaulee))

---

## 📄 License
TimeMeshin is open-sourced under the [FSL-1.1-Apache-2.0 License](LICENSE).
