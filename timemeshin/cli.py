"""
TimeMeshin CLI
Command-line interface for TimeMeshin: deterministic spatio-temporal video-scrubber context engine.
"""

import sys
import os
import shutil
import argparse
from pathlib import Path

SKILL_MD_CONTENT = """---
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
"""

PLUGIN_JSON_CONTENT = """{
  "name": "timemeshin",
  "version": "0.1.0",
  "description": "Deterministic Spatio-Temporal (S x T) Video-Scrubber Context Engine for Antigravity"
}
"""

AGENTS_RULE_CONTENT = """# TimeMeshin Deterministic Temporal Memory Guidelines

When interacting with codebases, architecture histories, or multi-step engineering sessions:
1. **Never Hallucinate Past/Future States:** Always evaluate historical questions strictly against the playhead timestamp (t <= T).
2. **Track Causal Lineage:** Record mutations with explicit causal parents when updating system states.
3. **Modal Distinctions:** Treat COMMITTED states as ground truth and EVALUATING/PROPOSED states as speculative branches.
"""

def install_skill(global_install=True, target_dir=None):
    """Installs the TimeMeshin skill into Antigravity configurations."""
    if target_dir:
        base_path = Path(target_dir)
    elif global_install:
        base_path = Path.home() / ".gemini" / "config"
    else:
        base_path = Path.cwd() / ".agents"

    # 1. Install standalone skill
    skill_dir = base_path / "skills" / "timemeshin"
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(SKILL_MD_CONTENT.strip(), encoding="utf-8")
    print(f"  [OK] Installed TimeMeshin Skill to: {skill_file}")

    # 2. Install full plugin bundle
    plugin_dir = base_path / "plugins" / "timemeshin"
    plugin_skill_dir = plugin_dir / "skills" / "timemeshin"
    plugin_rules_dir = plugin_dir / "rules"
    
    plugin_skill_dir.mkdir(parents=True, exist_ok=True)
    plugin_rules_dir.mkdir(parents=True, exist_ok=True)
    
    (plugin_dir / "plugin.json").write_text(PLUGIN_JSON_CONTENT.strip(), encoding="utf-8")
    (plugin_skill_dir / "SKILL.md").write_text(SKILL_MD_CONTENT.strip(), encoding="utf-8")
    (plugin_rules_dir / "AGENTS.md").write_text(AGENTS_RULE_CONTENT.strip(), encoding="utf-8")
    
    print(f"  [OK] Installed TimeMeshin Plugin Bundle to: {plugin_dir}")
    print("\nTimeMeshin is now active in Antigravity!")

def main():
    parser = argparse.ArgumentParser(
        prog="timemeshin",
        description="TimeMeshin: Deterministic Spatio-Temporal Video-Scrubber Context Engine"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # install-skill / init-agent
    install_parser = subparsers.add_parser("install-skill", help="Install TimeMeshin skill into Antigravity")
    install_parser.add_argument("--project", action="store_true", help="Install into current project's .agents/ directory instead of global ~/.gemini/config")
    install_parser.add_argument("--path", type=str, default=None, help="Custom installation target directory")

    init_parser = subparsers.add_parser("init-agent", help="Alias for install-skill")
    init_parser.add_argument("--project", action="store_true", help="Install into current project's .agents/ directory")
    init_parser.add_argument("--path", type=str, default=None, help="Custom installation target directory")

    # info
    subparsers.add_parser("info", help="Display TimeMeshin engine information")

    # serve
    serve_parser = subparsers.add_parser("serve", help="Launch the TimeMeshin REST API server")
    serve_parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port number")
    serve_parser.add_argument("--db", type=str, default="timemeshin.db", help="Database file path")

    args = parser.parse_args()

    if args.command in ("install-skill", "init-agent"):
        print("Installing TimeMeshin Agent Skill & Plugin into Antigravity...")
        install_skill(global_install=not args.project, target_dir=args.path)
    elif args.command == "info":
        print("TimeMeshin Engine v0.1.0")
        print("Architecture: Spatio-Temporal (S x T) Video-Codec Context Engine")
        print("License: Apache 2.0")
        print("Repository: https://github.com/Changmaulee/timemeshin")
    elif args.command == "serve":
        try:
            import uvicorn
            from timemeshin.server.api import create_app
            app = create_app(db_path=args.db)
            print(f"Starting TimeMeshin API server on http://{args.host}:{args.port}...")
            uvicorn.run(app, host=args.host, port=args.port)
        except ImportError:
            print("Error: FastAPI and Uvicorn are required for server mode. Run: pip install 'timemeshin[server]'")
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()