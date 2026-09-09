"""
S x T Bihalo Query Engine and Playhead Scrubber.
Combines Temporal Fencing (T) with Dense Semantic Search (S) and Keyframe State Folding.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
from .models import StateDelta, SemanticEvent, Keyframe, Modality
from .storage import TimeMeshinStorage, LightweightEmbedder


class SpatioTemporalEngine:
    """
    Executes S x T Bihalo Queries, Playhead Scrubbing, and LLM Context Compilation.
    """

    def __init__(self, storage: TimeMeshinStorage):
        self.storage = storage

    def scrub(self, playhead: str) -> Keyframe:
        """
        Reconstructs the consolidated ground-truth state table for all active entities at playhead t.
        """
        return self.storage.fold_keyframe(playhead)

    def query_st(
        self,
        query: str,
        playhead: str,
        top_k_mutations: int = 5,
        top_k_events: int = 3
    ) -> Dict[str, Any]:
        """
        Executes a dual-coordinate S x T query:
        1. Temporal Filter: t <= playhead (100% Deterministic, 0% Future Leakage)
        2. Semantic Ranking: Dense Cosine Similarity on query embedding vs. historical rationales
        3. Keyframe Unfolding: Active system configuration state table at playhead
        """
        # Embed user query
        q_vec = self.storage.embedder.embed(query)

        # 1. Fetch filtered records (Temporal Gate)
        candidate_deltas = self.storage.get_deltas_up_to(playhead)
        candidate_events = self.storage.get_events_up_to(playhead)

        # 2. Score & Rank Deltas by Semantic Coordinate S
        scored_deltas: List[Tuple[float, StateDelta]] = []
        for d in candidate_deltas:
            d_vec = d.embedding or self.storage.embedder.embed(f"{d.entity} {d.attribute} {d.v_new} {d.causal_rationale}")
            sim = LightweightEmbedder.cosine_similarity(q_vec, d_vec)
            scored_deltas.append((sim, d))

        scored_deltas.sort(key=lambda x: x[0], reverse=True)
        top_deltas = [d for score, d in scored_deltas[:top_k_mutations]]

        # 3. Score & Rank Events by Semantic Coordinate S
        scored_events: List[Tuple[float, SemanticEvent]] = []
        for ev in candidate_events:
            ev_vec = ev.embedding or self.storage.embedder.embed(f"{ev.summary} {ev.raw_text} {' '.join(ev.topics)}")
            sim = LightweightEmbedder.cosine_similarity(q_vec, ev_vec)
            scored_events.append((sim, ev))

        scored_events.sort(key=lambda x: x[0], reverse=True)
        top_events = [ev for score, ev in scored_events[:top_k_events]]

        # 4. Fold Active Keyframe State Table
        active_keyframe = self.storage.fold_keyframe(playhead)

        # 5. Compile Prompt Context
        compiled_context = self._compile_prompt_context(
            query=query,
            playhead=playhead,
            keyframe=active_keyframe,
            top_deltas=top_deltas,
            top_events=top_events
        )

        return {
            "query": query,
            "playhead": playhead,
            "keyframe_state": active_keyframe.state_table,
            "relevant_mutations": [d.to_dict() for d in top_deltas],
            "relevant_events": [ev.to_dict() for ev in top_events],
            "compiled_prompt_context": compiled_context
        }

    def _compile_prompt_context(
        self,
        query: str,
        playhead: str,
        keyframe: Keyframe,
        top_deltas: List[StateDelta],
        top_events: List[SemanticEvent]
    ) -> str:
        """
        Compiles clean, consolidated, zero-hallucination context for LLMs.
        """
        lines = []
        lines.append(f"=== TIMEMESHIN CONTEXT (Playhead: {playhead}) ===")
        lines.append(f"QUERY: {query}\n")

        # Active System Configuration (Ground Truth State Table)
        lines.append("## [1. ACTIVE ENTITY STATE TABLE (Point-in-Time Ground Truth)]")
        if keyframe.state_table:
            for entity, attrs in keyframe.state_table.items():
                attr_strs = [f"{k}={v}" for k, v in attrs.items() if not k.startswith("_")]
                rack = attrs.get("_rack", "General")
                updated = attrs.get("_last_updated", "unknown")
                lines.append(f"- **{entity}** [{rack}] (Updated: {updated}): {', '.join(attr_strs)}")
        else:
            lines.append("No active entity state recorded prior to playhead.")

        # Relevant Historical State Mutations & Causal Rationales
        lines.append("\n## [2. RELEVANT CAUSAL STATE MUTATIONS (S x T Ranked)]")
        if top_deltas:
            for d in top_deltas:
                old_info = f" (from {d.v_old})" if d.v_old else ""
                lines.append(f"- [{d.timestamp}] **{d.entity}.{d.attribute}** -> `{d.v_new}`{old_info} [{d.rack}, {d.modality.value}]")
                if d.causal_rationale:
                    lines.append(f"  * Rationale: {d.causal_rationale}")
        else:
            lines.append("No relevant historical mutations found.")

        # Anchored Semantic Events
        if top_events:
            lines.append("\n## [3. RELEVANT TIMELINE EVENTS]")
            for ev in top_events:
                lines.append(f"- [{ev.timestamp}] **[{ev.impact_level}]** {ev.summary} (Topics: {', '.join(ev.topics)})")

        lines.append("\n=== END OF TIMEMESHIN CONTEXT ===")
        return "\n".join(lines)
