# TimeMeshin Deterministic Temporal Memory Guidelines

When interacting with codebases, architecture histories, or multi-step engineering sessions:
1. **Never Hallucinate Past/Future States:** Always evaluate historical questions strictly against the playhead timestamp (t <= T).
2. **Track Causal Lineage:** Record mutations with explicit causal parents when updating system states.
3. **Modal Distinctions:** Treat COMMITTED states as ground truth and EVALUATING/PROPOSED states as speculative branches.