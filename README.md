# ⏳ TimeMeshin & TimeMesh Lang (v0.3.0)
### Point-in-Time Ground Truth ($t \le T$), BioMesh 2-Bit DNA ISA & Causal Lineage Substrate for Autonomous AI & Agents
*Deterministic Spatio-Temporal ($S \times T$) Context Engine, Declarative Frame DSL, and High-Throughput System One Decision Gateway*

**Authored by**: Chandramouli ([@Changmaulee](https://github.com/Changmaulee)) • **Contact**: [yellowbridgeconnections@gmail.com](mailto:yellowbridgeconnections@gmail.com)  
**Indian Patent Application No.**: `202641107532` (CBR Date: Sept 7, 2026)  
**License**: Functional Source License (**FSL-1.1-Apache-2.0** / **FSL-1.1-MIT**) & Commercial Enterprise

[![License](https://img.shields.io/badge/License-FSL--1.1--Apache--2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-brightgreen.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-passing-success.svg)](https://github.com/Changmaulee/timemeshin)
[![Architecture](https://img.shields.io/badge/Architecture-S%20x%20T%20Dual--Coordinate-orange.svg)](#core-architecture)
[![ISA](https://img.shields.io/badge/BioMesh-2--Bit%20DNA%20Codon-darkgreen.svg)](#dna-isa)

---

## 🚀 The TimeMesh Ecosystem

The TimeMesh ecosystem consists of two unified pillars:
1. **TimeMeshin Engine**: The persistent Spatio-Temporal ($S \times T$) memory engine, causal DAG tracker, and Python SDK.
2. **TimeMesh Lang (TM-Lang)**: The declarative frame language and **BioMesh 2-Bit DNA Codon ISA** that enables sub-microsecond System One decision-making, zero-backpropagation self-healing, and edge microcontroller execution (Raspberry Pi Pico / RP2350).

---

## 🧬 TimeMesh Lang (Declarative BioMesh DNA ISA)

TimeMesh Lang translates human/agent prose into **2-bit genomic codons** ($A=00, T=01, C=10, G=11$) executing on cloud gateways or bare-metal microcontrollers with sub-microsecond latency.

```text
@ 2026-09-25 10:00:00        // [ATG] OP_SET_PLAYHEAD: Anchor temporal coordinate t <= T
# max_db_connections = 100    // [TAC] OP_COMMIT_IFRAME: Baseline ground-truth keyframe
> max_db_connections = 20     // [CAG] OP_APPLY_PFRAME: Causal state delta mutation
? Simulate 5,000 reqs        // [GAG] OP_EVAL_BFRAME_OCC: Ephemeral System One sandbox (0 disk pollution)
! Rewind to 10:00:00         // [TAA] OP_ZERO_BACKPROP_HOTSWAP: Instant causal rewind & repair
```

### BioMesh Codon Instruction Set Architecture (ISA)

| Sigil | Codon | Biological Function | TimeMesh VM Operation |
| :---: | :---: | :--- | :--- |
| **`@`** | **`ATG`** | **Start Codon (Methionine)** | **`OP_SET_PLAYHEAD`**: Sets temporal fence ($t \le T$), guaranteeing 0% future-data leakage. |
| **`#`** | **`TAC`** | **Keyframe Baseline** | **`OP_COMMIT_IFRAME`**: Consolidates full active state baseline into memory. |
| **`>`** | **`CAG`** | **Forward Mutation** | **`OP_APPLY_PFRAME`**: Applies state mutation and links parent node in the topological causal DAG. |
| **`?`** | **`GAG`** | **Epigenetic Simulation** | **`OP_EVAL_BFRAME_OCC`**: In-memory speculative System One decision gate (OCC). |
| **`!`** | **`TAA`** | **Stop / DNA Repair** | **`OP_ZERO_BACKPROP_HOTSWAP`**: Traces root cause and hot-swaps state without gradient descent. |

---

## ⚡ Quickstart

### 1. Python SDK & Memory Client
```python
from timemeshin import TimeMeshinClient

client = TimeMeshinClient(db_path="timemeshin_memory.db")

# Ingest prose with automatic delta extraction
client.ingest("Switched primary database from Postgres to DynamoDB.", timestamp="2026-09-08 11:30:00")
client.ingest("Reduced database max_connections 100 -> 20.", timestamp="2026-09-08 14:50:00")

# Deterministic point-in-time scrubbing (I-Frame Keyframe consolidation)
state = client.scrub(playhead="2026-09-08 12:00:00")

# Topological Causal Root-Cause Trace
prompt = client.trace_prompt("HTTP 504 Outage", target_id_or_entity="database")
```

### 2. TimeMesh Lang & VM Execution
```python
from timemesh_lang import TMLexer, TimeMeshVM, BioMeshCompiler

script = """
@ 2026-09-25 10:00:00
# database = "Postgres" max_connections = 100
> max_connections = 20
? ticket_type = "refund" amount = 450
! max_connections = 100
"""

# Compile to BioMesh DNA sequence
dna_seq, raw_bytes = BioMeshCompiler.compile_to_dna(script)
print("DNA Bytecode:", dna_seq)

# Execute via TimeMesh VM
vm = TimeMeshVM()
for frame in TMLexer.parse(script):
    res = vm.execute_frame(frame)
    print(f"[{frame.alias}] ->", res)
```

---

## 📊 Performance Benchmarks: TimeMesh vs. Jev (TypeSafe AI) & Cloud LLMs

TimeMesh Lang's B-Frame (`?` / `GAG`) mode functions as a **high-throughput System One decision engine**, offering sub-microsecond compute and significant cost savings over cloud neural models:

| Metric | **Standard Cloud LLM**<br>*(GPT-4o / Claude)* | **Jev (TypeSafe AI)**<br>*(Specialized Neural)* | **TimeMesh Lang / Cloud Gateway**<br>*(B-Frame OCC)* |
| :--- | :---: | :---: | :---: |
| **Server Compute Latency** | `~520.0 ms` | `~15.0 ms` | **`0.017 ms` (`17.0 µs`)** ⚡ |
| **Cost per 1M Decisions** | `~$5,000.00` | `~$4.20 - $20.00` | **`~$0.40`** *(10x-50x cheaper)* 💰 |
| **Edge Microcontroller Support**| ❌ No | ❌ No | **✅ Yes (Raspberry Pi Pico / RP2350)** |
| **Stateful Causal Promotion** | ❌ No | ❌ No | **✅ Native (`>` P-Frame)** |
| **Retroactive Root-Cause Rewind** | ❌ No | ❌ No | **✅ Native (`!` R-Frame)** |

---

## 🏛️ Core Architecture

```
                 [ INCOMING RAW PROSE / AGENT STREAM / TM-LANG SCRIPT ]
                                          │
                 ┌────────────────────────┴────────────────────────┐
                 ▼                                                 ▼
        [ 1. FAST PATH (<2ms) ]                         [ 2. BIOMESH DNA COMPILER ]
      Write-Ahead Append: SQLite Events                 Codon ISA (ATG, TAC, CAG, GAG, TAA)
                 │                                                 │
                 └────────────────────────┬────────────────────────┘
                                          │
                           [ 3. TOPOLOGICAL CAUSAL SCOPING ]
                           ├── Entity Dependency Graph (e.g., auth -> auth_db)
                           └── Calibrated NLI Causal Entailment >= 0.85
                                          │
                           [ 4. B-FRAME OCC EPOCH TRACKER ]
                           ├── In-Memory Speculative Sandbox
                           └── Zero Disk Pollution / Conflict Detection
```

---

## 📦 Directory Structure

* **`timemeshin/`**: Core Spatio-Temporal ($S \times T$) memory engine, SQLite substrate, and MCP server.
* **`timemesh_lang/`**: Declarative Frame Lexer, VM, BioMesh 2-Bit DNA compiler, and OTM tokenizer.
* **`cloud/`**: High-performance FastAPI Cloud Decision Gateway (System One API).
* **`edge/`**: MicroPython / C++ firmware for Raspberry Pi Pico & RP2350 microcontrollers.
* **`benchmarks/`**: Google Colab benchmarks and HTTP load test clients.

---

## 📄 License & Intellectual Property Notice

* **Patented System**: The underlying spatio-temporal spherocylinder memory structures, Voronoi director routing, continuous-discrete temporal attention methods, and BioMesh DNA codon architectures are protected under **Indian Patent Application No. 202641107532 (CBR Date: September 7, 2026)**.
* **Lead Architect & Inventor**: Chandramouli ([@Changmaulee](https://github.com/Changmaulee))
* **Functional Source License (FSL-1.1-Apache-2.0 / FSL-1.1-MIT)**: Free for developers, researchers, and internal non-competing integrations.
* For enterprise licensing or sovereign cloud deployments, contact [yellowbridgeconnections@gmail.com](mailto:yellowbridgeconnections@gmail.com).
