# TimeMeshin (v0.2.1)
> **Deterministic Spatio-Temporal ($S \times T$) Context Engine & Episodic Memory Substrate for AI Agents**  
> *Authored by Chandramouli ([@Changmaulee](https://github.com/Changmaulee))*

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-brightgreen.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-passing-success.svg)](https://github.com/Changmaulee/timemeshin)

---

## 🚀 Overview

**TimeMeshin** is a spatio-temporal episodic memory engine engineered specifically to solve the temporal blindness, conflicting context clutter, and causal opacity of standard Vector RAG.

By unifying a **Hard Temporal Fence ($T$)** with **Dense Semantic Vector Ranking ($S$)**, **Topological Causal Discovery**, and **Optimistic Concurrency Control (OCC) on B-Frames**, TimeMeshin provides 100% deterministic, point-in-time ground truth for AI agents without future-data contamination or dirty state commits.

---

## 🏛️ Core Architectural Upgrades

```
                                [INCOMING RAW LOG STREAM]
                                            │
               ┌────────────────────────────┴────────────────────────────┐
               ▼                                                         ▼
       [1. FAST PATH (<2ms)]                                [2. ASYNC REFINEMENT WORKER]
  Write-Ahead Append: SQLite Event Table                 SLM Grammar Extractor & Structuring
               │                                                         │
               └────────────────────────────┬────────────────────────────┘
                                            │
                             [3. TOPOLOGICAL CAUSAL SCOPING]
                             ├── Entity Dependency Graph (e.g. auth_service -> auth_db)
                             └── Calibrated NLI Score: P(Entailment) - P(Contradiction) >= 0.85
                                            │
                             [4. B-FRAME OCC EPOCH TRACKER]
                             ├── Base Epoch Hash at t_branch
                             └── Conflict Detection on commit_to_main()
```

### 1. Two-Speed Ingestion & Zero-ETL Delta Extractor (`extractor.py`, `client.py`)
* **Fast-Path Sync (`<2ms`):** Appends raw unparsed engineering prose directly to SQLite Write-Ahead Log as a `SemanticEvent`.
* **Refinement Worker:** Extracts structured state deltas ($\Delta = \langle t, e, r, a, v_{\text{old}}, v_{\text{new}}, c_i, \text{modality} \rangle$) and compacts Keyframes without blocking write throughput.

### 2. $S \times T$ Hybrid Bihalo Index & Scrubber (`engine.py`, `storage.py`)
* **Coordinate $T$ (Temporal Fence):** Strictly masks $t > t_{\text{playhead}}$ to guarantee **0% future-data leakage**.
* **Keyframe State Consolidation ($I$-Frames):** Collapses historical $P$-Frames into a single, unambiguous active entity state table.
* **Coordinate $S$ (Semantic Ranking):** Ranks historical causal rationales and state transitions using dense cosine similarity.

### 3. Self-Wiring Causal DAG with Topological Scoping (`causality.py`)
* **Spurious Correlation Rejection:** Enforces runtime architectural topology boundaries (`auth_service` $\to$ `database` $\to$ `api_gateway`). Unrelated noisy commits (e.g. frontend CSS changes) are scoped out before computing embeddings.
* **Calibrated Directional NLI:** Computes $\text{Confidence}(A \to B) = P(\text{Entailment}) - P(\text{Contradiction})$ with configurable gating.
* **Multi-Hop Traversal:** Traverses dependency graphs backwards to output chronological root-cause chains directly into LLM prompts.

### 4. $B$-Frame Ephemeral Branching with OCC (`branching.py`)
* **Sandboxed Counterfactuals:** In-memory Copy-on-Write (CoW) sandbox ($S_{\text{branch}}(t) = S(t) \oplus \Delta_{\text{hypothetical}}$) for agents to test rollbacks, migrations, and multi-step plans.
* **Ghost Rebase Prevention (OCC):** Tracks SHA-256 vector clock epochs on the base timeline. If the underlying timeline receives out-of-order mutations during a simulation, `commit_to_main()` detects timeline drift and raises `BranchConflictError`.

---

## 📦 Quickstart Python Usage

```python
from timemeshin import TimeMeshinClient

# 1. Initialize persistent SQLite substrate
client = TimeMeshinClient(db_path="timemeshin_memory.db")

# 2. Ingest raw unstructured text (Fast-Path or Synchronous)
client.ingest("Initial setup: primary database set to Postgres (max_connections=100).", timestamp="2026-09-08 09:00:00")
client.ingest("Switched primary database from Postgres to DynamoDB due to write lock contention.", timestamp="2026-09-08 11:30:00")
client.ingest("PR #402 merged (auth_service updated to v2.0 with aggressive connection pooling).", timestamp="2026-09-08 14:42:00")
client.ingest("Reduced database max_connections 100 -> 20 to preserve cloud resources.", timestamp="2026-09-08 14:50:00")
client.ingest("HTTP 504 Gateway Timeouts detected on API gateway due to pool exhaustion.", timestamp="2026-09-08 15:00:00")

# 3. Deterministic Point-in-Time Scrubbing (t = 12:00 Noon)
kf = client.scrub(playhead="2026-09-08 12:00:00")
print(kf.get_entity_state("database"))
# Returns: {'engine': 'DynamoDB', 'max_connections': '100', '_last_updated': '2026-09-08 11:30:00'}

# 4. S x T Dual-Coordinate Query with Compiled Prompt
result = client.query("What was our database engine and configuration?", playhead="2026-09-08 12:00:00")
print(result["compiled_prompt_context"])

# 5. Multi-Hop Causal Root-Cause Trace
causal_narrative = client.trace_prompt("HTTP 504 Outage", target_id_or_entity="api_gateway", playhead="2026-09-08 15:05:00")
print(causal_narrative)

# 6. B-Frame Speculative Counterfactual Simulation (Guarded by OCC)
with client.branch(from_playhead="2026-09-08 15:00:00", name="sim_rollback") as sim:
    sim.ingest_hypothetical(
        entity="database",
        attribute="max_connections",
        v_new="100",
        v_old="20",
        causal_rationale="Simulated hotfix: restore connection pool"
    )
    assert sim.scrub().get_entity_state("database")["max_connections"] == "100"
    # Auto-discarded upon context exit! Master timeline remains untouched.
```

---

## 📊 Live Benchmark Comparison

To run the live 5-suite benchmark:
```bash
python benchmark.py
```

| Capability / Benchmark Suite | Standard Vector RAG | TimeMeshin v0.2.1 ($S \times T$) | Outcome |
| :--- | :--- | :--- | :--- |
| **1. Point-in-Time Auditing** | ❌ **Failed:** Leaks future events into prompt | ✅ **Passed:** Mask $t \le t_{\text{target}}$ delivers exact ground truth | **0% temporal leakage** |
| **2. Multi-Hop Causal Discovery** | ❌ **Failed:** Unconnected vector clusters | ✅ **Passed:** Self-wired DAG traverses PR $\to$ DB $\to$ Outage | **Deterministic causality** |
| **3. Agent Simulation Sandbox** | ❌ **Failed:** Read-only / impossible to branch | ✅ **Passed:** In-memory copy-on-write sandbox | **Safe counterfactuals** |
| **4. Spurious Correlation Rejection** | ❌ **Failed:** Noise commits link to outages | ✅ **Passed:** Topological scoping rejects unrelated CSS commits | **Causal precision** |
| **5. Ghost Rebase Detection (OCC)** | ❌ **Failed:** Silent corruption on drift | ✅ **Passed:** Vector clock catches timeline mutations | **Transactional safety** |

---

## 🧪 Running Tests

```bash
python -m unittest discover tests
```

---

## 📄 License

Apache-2.0. Authored by Chandramouli ([@Changmaulee](https://github.com/Changmaulee)).
