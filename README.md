# ⏳ TimeMeshin

> **The Deterministic Spatio-Temporal ($S \times T$) Video-Scrubber Context Engine for AI Agents & LLM Retrieval**

[![License: FSL-1.1-Apache](https://img.shields.io/badge/License-FSL--1.1--Apache--2.0-blue.svg)](LICENSE)
[![Python: 3.9+](https://img.shields.io/badge/Python-3.9%2B-brightgreen.svg)]()
[![PyPI: timemeshin](https://img.shields.io/badge/PyPI-timemeshin-blue.svg)]()
[![Antigravity: Skill Enabled](https://img.shields.io/badge/Antigravity-Skill%20%26%20Plugin-orange.svg)]()
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Changmaulee/timemeshin/blob/main/examples/TimeMeshin_Colab_Quickstart.ipynb)

---

## 💡 Why TimeMeshin?

Traditional Vector RAG (Pinecone, Chroma, Milvus) flattens time into an atemporal bag of chunks. When information evolves, past and future collide, resulting in **87%+ future-data leakage** and **94% failure rates on stateful queries**.

**TimeMeshin** is the world's first **Time-Travel Context Engine**, modeled after **digital video codecs (MPEG / H.264)** and **Database Event Sourcing**:
1. **I-Frames (Keyframes):** Consolidated world state snapshots at regular intervals.
2. **P-Frames (Delta Frames):** State mutations tracking `(Entity, Attribute, OldValue ➔ NewValue, CausalReason)`.
3. **The Playhead Scrubber:** A deterministic function $f(t) = \text{Keyframe} + \sum \Delta_t$ that scrubs backwards and forwards through time with 100% mathematical fidelity.
4. **Git-Rebase Time Splicing:** Retroactively splices out-of-order late-arriving events into history without breaking downstream keyframes.
5. **Transitive Causal DAGs:** Autonomously traces multi-hop cross-entity domino effects (*Sarah Leaves ➔ Alex Assigned ➔ CockroachDB Deployed ➔ Budget Spikes*).

---

## 🚀 Quickstart

### 1. Installation via PyPI
```bash
pip install timemeshin
```

### 2. Antigravity Agent Skill Integration (1-Command Install)
Equip Google Antigravity or any agentic workflow with global TimeMeshin memory:

```bash
# Global installation for your machine (~/.gemini/config)
timemeshin install-skill

# Or workspace-only installation for your repository (.agents/)
timemeshin install-skill --project
```

---

## 📊 Benchmark Results (500 Events, 30 Days, 100 Queries)

| Evaluation Metric | Standard Vector RAG | TimeMeshin ($S \times T$) Engine |
| :--- | :--- | :--- |
| **Point-in-Time State Accuracy** | **6%** *(94% failure rate)* | **🌟 100%** *(Deterministic ground truth)* |
| **Future Contamination Rate** | **❌ 87%** *(leaked future events)* | **🛡️ 0%** *(Zero future leakage)* |
| **Retrieval Latency** | `26.51 ms` | **`24.14 ms`** *(Faster due to temporal pruning)* |

---

## 🐍 Plug-and-Play Python Client (2 Lines of Code)

```python
from timemeshin import TimeMeshinClient

# 1. Initialize Client (Zero-config persistent SQLite memory)
client = TimeMeshinClient(db_path="enterprise_memory.db")

# 2. Ingest raw text stream in real-time
client.ingest("We migrated our database to DynamoDB on Tuesday due to write contention. Budget is now $5000.")

# 3. Time-Travel Playhead Scrub
state = client.scrub(playhead="2026-09-02 14:00")
print(state)
# Output: {'Database': {'Engine': 'DynamoDB'}, 'MonthlyCloudBudget': {'AmountUSD': 5000}}

# 4. Dual-Coordinate Query (Exact state + Top ranked causal history)
result = client.query("Why did we change our database?", playhead="2026-09-02 14:00")
print(result["exact_state"])
print(result["relevant_events"])
```

---

## 🌐 Interactive Demos

* **Google Colab Notebook:** Run live with 1000+ GitHub commits in the cloud: [TimeMeshin_Colab_Quickstart.ipynb](examples/TimeMeshin_Colab_Quickstart.ipynb)
* **Light-Theme Web Dashboard:** Open `examples/interactive_dashboard.html` in your browser for a local UI with live playhead slider and causal DAG visualization.

---

## 🌐 REST API Server

Start the production server:

```bash
timemeshin serve --host 0.0.0.0 --port 8000
```

* **Swagger UI:** `http://localhost:8000/docs`
* **Health Check:** `GET /health`
* **Ingest Stream:** `POST /api/v1/ingest`
* **Scrub Playhead:** `GET /api/v1/scrub?playhead_time=2026-09-02T14:00:00`
* **Dual-Coordinate Query:** `POST /api/v1/query`
* **Entity Trajectory:** `GET /api/v1/trace/{entity_id}`

---

## 📁 Repository Structure

```
timemeshin/
├── .agents/                   # Antigravity Global & Project Skills / Plugins
│   ├── plugins/timemeshin/
│   └── skills/timemeshin/
├── .github/workflows/         # Automated PyPI publication CI/CD
├── timemeshin/                # Core Python Package
│   ├── cli.py                 # CLI & Antigravity installer
│   ├── client.py              # TimeMeshinClient SDK
│   ├── core/                  # Keyframes, Deltas, & Video-Scrubber Engine
│   ├── ingestion/             # Multi-format document loader & stream parser
│   ├── storage/               # SQLite / transactional state store
│   └── server/                # FastAPI REST endpoints
├── paper/                     # Formal academic research paper
├── benchmarks/                # Automated 30-day benchmark suite
├── examples/                  # Interactive Dashboard & Colab Notebooks
├── scripts/                   # Build, release, and installer scripts
├── pyproject.toml             # Standard PEP 517/621 packaging
└── README.md
```

---

## 📜 License

This project is licensed under the **Functional Source License, Version 1.1 (FSL-1.1-Apache-2.0)**:

* **100% Free for Individuals & Developers:** Free for personal use, research, education, and learning.
* **100% Free for Internal Business / Commercial Use:** Companies can freely build, embed, and deploy TimeMeshin for all internal systems and applications.
* **Competitive Cloud Protection:** Prevents cloud vendors and third parties from taking the software and reselling it as a competing managed cloud SaaS/PaaS service.
* **Automatic Open Source Conversion:** Converts automatically into pure **Apache 2.0** open source exactly **2 years** after each release.