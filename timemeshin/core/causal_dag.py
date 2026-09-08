"""
Timeless Phase 2 Core Engine:
1. Retroactive Out-of-Order Event Splicing & Keyframe Invalidation (Git-Rebase for Context).
2. Probabilistic & Modal State Superposition (COMMITTED, EVALUATING, PROPOSED, DEPRECATED).
3. Canonical Entity Alias Resolution Graph.
4. Cross-Entity Transitive Causal Directed Acyclic Graph (ST-DAG).
"""

import io
import json
import re
import sys
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass


class StateModality(str, Enum):
    COMMITTED = "COMMITTED"        # Hard active state (e.g., "We switched to DynamoDB")
    EVALUATING = "EVALUATING"      # Trial / Superposition (e.g., "We are testing Redis caching")
    PROPOSED = "PROPOSED"          # Future intent / Idea (e.g., "Considering moving to GCP")
    DEPRECATED = "DEPRECATED"      # Phasing out
    ROLLED_BACK = "ROLLED_BACK"    # Reverted


class ModalStateValue:
    """Represents a state with modality and confidence score."""
    def __init__(self, value: Any, modality: StateModality = StateModality.COMMITTED, confidence: float = 1.0, notes: str = ""):
        self.value = value
        self.modality = modality
        self.confidence = confidence
        self.notes = notes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "modality": self.modality.value if isinstance(self.modality, StateModality) else str(self.modality),
            "confidence": round(self.confidence, 2),
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ModalStateValue":
        mod = StateModality(d.get("modality", StateModality.COMMITTED.value))
        return cls(
            value=d.get("value"),
            modality=mod,
            confidence=float(d.get("confidence", 1.0)),
            notes=d.get("notes", "")
        )


class AdvancedDelta:
    """Phase 2 P-Frame with UUID, Causal Links, Modality, and Aliases."""
    def __init__(
        self,
        delta_id: str,
        timestamp: datetime,
        entity_id: str,
        topic_rack: str,
        attribute: str,
        old_value: Any,
        new_value: Any,
        modality: StateModality = StateModality.COMMITTED,
        confidence: float = 1.0,
        causal_reason: str = "",
        raw_text: str = "",
        caused_by_ids: Optional[List[str]] = None,
        embedding: Optional[np.ndarray] = None
    ):
        self.delta_id = delta_id
        self.timestamp = timestamp
        self.entity_id = entity_id
        self.topic_rack = topic_rack
        self.attribute = attribute
        self.old_value = old_value
        self.new_value = new_value
        self.modality = modality
        self.confidence = confidence
        self.causal_reason = causal_reason
        self.raw_text = raw_text
        self.caused_by_ids = caused_by_ids or []
        self.embedding = embedding

    def to_dict(self) -> Dict[str, Any]:
        return {
            "delta_id": self.delta_id,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "entity_id": self.entity_id,
            "topic_rack": self.topic_rack,
            "attribute": self.attribute,
            "change": f"{self.attribute}: '{self.old_value}' ➔ '{self.new_value}'",
            "modality": self.modality.value if isinstance(self.modality, StateModality) else str(self.modality),
            "confidence": self.confidence,
            "reason": self.causal_reason,
            "caused_by": self.caused_by_ids,
            "raw_text": self.raw_text
        }


class EntityAliasGraph:
    """Resolves arbitrary linguistic synonyms and aliases to canonical entity IDs."""
    def __init__(self):
        self.alias_map: Dict[str, str] = {}

    def register_alias(self, canonical_id: str, aliases: List[str]):
        for a in aliases:
            self.alias_map[a.lower().strip()] = canonical_id

    def resolve(self, mention: str) -> str:
        clean = mention.lower().strip()
        return self.alias_map.get(clean, mention)


class TimelessPhase2Engine:
    """
    Advanced Spatio-Temporal Engine implementing all 4 Phase 2 breakthroughs.
    """
    def __init__(self, keyframe_interval_days: int = 5):
        self.deltas: List[AdvancedDelta] = []
        self.delta_lookup: Dict[str, AdvancedDelta] = {}
        self.keyframes: List[Tuple[datetime, Dict[str, Dict[str, Dict[str, Any]]]]] = []
        self.keyframe_interval_days = keyframe_interval_days
        self.alias_graph = EntityAliasGraph()
        
        # Default alias registrations
        self.alias_graph.register_alias("Database", ["the database", "our main db", "postgres cluster", "the rds box", "storage layer"])
        self.alias_graph.register_alias("MonthlyCloudBudget", ["cloud budget", "aws bill", "monthly spend", "infra cost", "budget"])
        self.alias_graph.register_alias("TeamLead", ["tech lead", "engineering manager", "lead engineer", "lead"])

    def record_delta(self, delta: AdvancedDelta) -> None:
        """
        Records delta with automatic Retroactive Invalidation if inserted in the past.
        """
        delta.entity_id = self.alias_graph.resolve(delta.entity_id)
        
        is_retroactive = False
        if self.deltas and delta.timestamp < self.deltas[-1].timestamp:
            is_retroactive = True

        self.deltas.append(delta)
        self.delta_lookup[delta.delta_id] = delta
        self.deltas.sort(key=lambda d: d.timestamp)

        if is_retroactive:
            self._invalidate_and_rebuild_keyframes(since_time=delta.timestamp)
        else:
            self._maybe_create_keyframe(delta.timestamp)

    def _invalidate_and_rebuild_keyframes(self, since_time: datetime) -> None:
        """Git-Rebase style Keyframe reconstruction for retroactive insertions."""
        self.keyframes = [kf for kf in self.keyframes if kf[0] < since_time]
        
        if self.deltas:
            curr_t = since_time
            last_t = self.deltas[-1].timestamp
            while curr_t <= last_t:
                state = self.scrub_state(curr_t)
                self.keyframes.append((curr_t, state))
                curr_t += timedelta(days=self.keyframe_interval_days)

    def _maybe_create_keyframe(self, timestamp: datetime) -> None:
        if not self.keyframes:
            self.keyframes.append((timestamp, self.scrub_state(timestamp)))
        else:
            last_kf_time = self.keyframes[-1][0]
            if (timestamp - last_kf_time).days >= self.keyframe_interval_days:
                self.keyframes.append((timestamp, self.scrub_state(timestamp)))

    def scrub_state(self, playhead_time: datetime, include_uncommitted: bool = True) -> Dict[str, Dict[str, Any]]:
        """
        Reconstructs world state at timestamp T, accounting for modalities (COMMITTED vs EVALUATING).
        """
        base_state: Dict[str, Dict[str, ModalStateValue]] = {}
        last_kf_time = datetime.min

        for kf_t, kf_state in reversed(self.keyframes):
            if kf_t <= playhead_time:
                # kf_state is stored as nested dicts
                for e, attrs in kf_state.items():
                    base_state[e] = {}
                    for a, d in attrs.items():
                        base_state[e][a] = ModalStateValue.from_dict(d)
                last_kf_time = kf_t
                break

        # Replay deltas between last keyframe and playhead_time
        for d in self.deltas:
            if last_kf_time < d.timestamp <= playhead_time:
                if d.entity_id not in base_state:
                    base_state[d.entity_id] = {}
                
                base_state[d.entity_id][d.attribute] = ModalStateValue(
                    value=d.new_value,
                    modality=d.modality,
                    confidence=d.confidence,
                    notes=d.causal_reason
                )

        # Format output
        output: Dict[str, Dict[str, Any]] = {}
        for entity, attrs in base_state.items():
            output[entity] = {}
            for attr, modal_val in attrs.items():
                if not include_uncommitted and modal_val.modality != StateModality.COMMITTED:
                    continue
                output[entity][attr] = modal_val.to_dict()
        return output

    def trace_transitive_causal_dag(self, target_delta_id: str) -> List[Dict[str, Any]]:
        """
        TRANSITIVE CAUSAL TRACER:
        Traverses the cross-entity Directed Acyclic Graph backward to discover root causes.
        """
        visited: Set[str] = set()
        causal_chain: List[Dict[str, Any]] = []

        def dfs(did: str):
            if did in visited or did not in self.delta_lookup:
                return
            visited.add(did)
            d = self.delta_lookup[did]
            for parent_id in d.caused_by_ids:
                dfs(parent_id)
            causal_chain.append(d.to_dict())

        dfs(target_delta_id)
        return causal_chain
