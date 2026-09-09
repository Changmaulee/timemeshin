# Project Memory (TimeMeshin)

This project uses **TimeMeshin** (Deterministic Spatio-Temporal Video-Scrubber Context Engine) for state tracking, historical configuration retrieval, and causal decision tracing.

### Guidelines for Claude:
- When asked "Why did we make an architectural change / pick X in the past?", run:
  `python -m timemeshin query "<question>" --playhead "<date/time>"`
- When asked "What was our configuration or architecture on <date>?", run:
  `python -m timemeshin scrub --playhead "<date/time>"`
- When applying major architectural refactors, migrations, or dependency changes, run:
  `python -m timemeshin ingest "<what changed and why>"`

### Python SDK Usage:
```python
from timemeshin import TimeMeshinClient

client = TimeMeshinClient(db_path="timemeshin_memory.db")
# Record mutation
client.ingest("Migrated database from Postgres to DynamoDB")
# Point-in-time state
state = client.scrub(playhead="2026-09-08 14:00:00")
# Causal DAG query
result = client.query("Why did we change the database?", playhead="2026-09-08 14:00:00")
```
