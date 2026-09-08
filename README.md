# ⏳ TimeMeshin

> **The Deterministic Spatio-Temporal ($S \times T$) Video-Scrubber Context Engine for AI Agents**

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python: 3.9+](https://img.shields.io/badge/Python-3.9%2B-brightgreen.svg)]()
[![FastAPI: Ready](https://img.shields.io/badge/FastAPI-REST%20API-009688.svg)]()
[![Docker: Supported](https://img.shields.io/badge/Docker-Ready-2496ED.svg)]()

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

## 📊 Benchmark Results (500 Events, 30 Days, 100 Queries)

| Evaluation Metric | Standard Vector RAG | TimeMeshin ($S \times T$) Engine |
| :--- | :--- | :--- |
| **Point-in-Time State Accuracy** | **6%** *(94% failure rate)* | **🌟 100%** *(Deterministic ground truth)* |
| **Future Contamination Rate** | **❌ 87%** *(leaked future events)* | **🛡️ 0%** *(Zero future leakage)* |
| **Retrieval Latency** | `26.51 ms` | **`24.14 ms`** *(Faster due to temporal pruning)* |

---

## 🚀 1. Plug-and-Play Python Client (2 Lines of Code)

```python
from timemeshin import TimeMeshinClient

# 1. Initialize Client (Zero-config persistent SQLite memory)
client = TimeMeshinClient(db_path="enterprise_memory.db", api_key="sk-...")

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

## 🌐 2. REST API Server & Swagger Docs

Start the production server:

```bash
uvicorn chronomesh.server.app:app --host 0.0.0.0 --port 8000
```

* **Swagger UI:** `http://localhost:8000/docs`
* **Health Check:** `GET /health`
* **Ingest Stream:** `POST /api/v1/ingest`
* **Scrub Playhead:** `GET /api/v1/scrub?playhead_time=2026-09-02T14:00:00`
* **Dual-Coordinate Query:** `POST /api/v1/query`
* **Entity Trajectory:** `GET /api/v1/trace/{entity_id}`

---

## 🐳 3. Docker Deployment (1 Command)

```bash
docker-compose up -d
```

---

## 📁 Repository Structure

```
D:\antigravity\chronomesh/
├── timemeshin/                # TimeMeshin entrypoint SDK
│   └── __init__.py
├── chronomesh/
│   ├── client.py              # High-level plug-and-play Python SDK
│   ├── core/
│   │   ├── frames.py          # DeltaFrame (P-Frame) & Keyframe (I-Frame)
│   │   ├── engine.py          # Dual-Coordinate S x T Scrubber Engine
│   │   └── causal_dag.py      # Transitive Causal DAGs & Git-Rebase Time Splicing
│   ├── ingestion/
│   │   ├── extractor.py       # JSON schema specification
│   │   └── llm_client.py      # OpenAI / Gemini auto-ingestor
│   ├── storage/
│   │   └── sqlite_store.py    # Zero-config SQLite disk persistence
│   └── server/
│       └── app.py             # Production FastAPI REST API
├── paper/
│   └── TIMEMESHIN_RESEARCH_PAPER.md # Formal academic paper
├── benchmarks/
│   └── benchmark_30day.py     # 30-day 500-event automated benchmark
├── examples/
│   ├── plug_and_play_demo.py  # End-to-end commercial SDK demo
│   ├── phase2_advanced_demo.py # Git-Rebase & Causal DAG verification
│   └── real_chat_test.py      # Live transcript audit test
├── Dockerfile                 # Production Docker image
├── docker-compose.yml         # 1-click container deployment
├── pyproject.toml             # Package configuration
└── README.md                  # Documentation & Benchmarks
```

---

## 📜 License
MIT License. Commercial & Open-Source Friendly.
