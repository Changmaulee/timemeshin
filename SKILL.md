---
name: timemeshin
description: >-
  Deterministic Spatio-Temporal (Semantics x Timeline) Video-Scrubber Context Engine for Antigravity, Claude Code, and AI Agents.
  Use when tracking evolving project architectures, configuration state mutations, causal decision histories,
  or when retrieving point-in-time ground truth across multi-step development sessions.
---

# TimeMeshin: Episodic Memory & Timeline Skill (v0.2.1)

## When to Use This Skill
1. **Stateful Project History:** Tracking architectural migrations and configuration state over time with 0% future-data leakage.
2. **Point-in-Time Auditing:** When asked: *"What was our setup on Day 2?"* or *"What was the configuration before refactoring?"*
3. **Causal Reasoning:** Tracing *why* a decision occurred using the Transitive Causal DAG.
4. **Agent Counterfactuals:** Running speculative "What-If" simulations on in-memory B-Frames without polluting ground truth.

## Quick Commands
- **Record a decision / mutation:**
  `python -m timemeshin ingest "<entity> <attribute> changed from <old> to <new> because <reason>"`
- **Query past state / why:**
  `python -m timemeshin query "<question>" --playhead "<date/time>"`
- **Scrub to date:**
  `python -m timemeshin scrub --playhead "<date/time>"`
- **Launch REST Server:**
  `python -m timemeshin serve --port 8000`
