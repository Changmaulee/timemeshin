"""
Core data models and primitives for TimeMeshin Next-Gen Spatio-Temporal Engine.
"""

from __future__ import annotations
import enum
import time
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Union


class Modality(str, enum.Enum):
    """Modal state / epistemic status of an event or mutation."""
    COMMITTED = "COMMITTED"    # Immutable, ground-truth historical facts
    EVALUATING = "EVALUATING"  # Active trials, benchmarks, or tests
    PROPOSED = "PROPOSED"      # Speculative designs, proposals, or unmerged PRs
    HYPOTHETICAL = "HYPOTHETICAL"  # B-Frame speculative simulation state


@dataclass
class StateDelta:
    """
    Structured state mutation (P-Frame Delta): Δ = ⟨id, t, entity, rack, attribute, v_old, v_new, rationale, modality, parents⟩.
    """
    id: str
    timestamp: str  # ISO-8601 or comparable format e.g. "2026-09-08 14:10:00"
    entity: str     # e.g., "auth_db", "payment_gateway", "rate_limiter"
    rack: str       # Topic / architectural category e.g., "Infra", "Code", "Config", "Observability"
    attribute: str  # e.g., "max_connections", "version", "status", "timeout_ms"
    v_old: Optional[str] = None
    v_new: str = ""
    causal_rationale: str = ""
    modality: Modality = Modality.COMMITTED
    parent_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["modality"] = self.modality.value
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> StateDelta:
        d = dict(data)
        if isinstance(d.get("modality"), str):
            d["modality"] = Modality(d["modality"])
        return cls(**d)


@dataclass
class SemanticEvent:
    """
    Unstructured semantic event anchored to the playhead timeline when no specific state mutation is detected.
    """
    id: str
    timestamp: str
    summary: str
    raw_text: str
    rack: str = "General"
    topics: List[str] = field(default_factory=list)
    impact_level: str = "INFO"  # INFO, WARNING, CRITICAL
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SemanticEvent:
        return cls(**data)


@dataclass
class Keyframe:
    """
    Consolidated Point-in-Time snapshot (I-Frame) representing the folded state of all entities at t.
    """
    timestamp: str
    state_table: Dict[str, Dict[str, Any]]  # entity -> {attribute: v_current, "_meta": {...}}
    source_delta_ids: List[str] = field(default_factory=list)

    def get_entity_state(self, entity: str) -> Optional[Dict[str, Any]]:
        return self.state_table.get(entity)

    def get(self, key: str, default: Any = None) -> Any:
        return self.state_table.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self.state_table[key]

    def __contains__(self, key: str) -> bool:
        return key in self.state_table



@dataclass
class CausalEdge:
    """Directed edge in the Transitive Causal DAG."""
    source_id: str
    target_id: str
    confidence: float
    evidence: str = ""
    discovered_automatically: bool = True


class BranchConflictError(Exception):
    """Raised when an ephemeral branch attempts to commit against a mutated/stale base timeline (OCC violation)."""
    pass

