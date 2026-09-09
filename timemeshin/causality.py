"""
Automated Causal Discovery & Transitive Causal DAG Engine for TimeMeshin.
Discovers causal relationships using temporal windows and directional entailment,
and traverses multi-hop causal chains to generate structured root-cause narratives.
"""

from __future__ import annotations
import datetime
from typing import List, Dict, Any, Optional, Set, Tuple
from .models import StateDelta, CausalEdge, Modality
from .storage import TimeMeshinStorage, LightweightEmbedder


class TopologyGraph:
    """
    Tracks runtime architectural dependencies between subsystems to prevent spurious causal links.
    e.g., auth_service -> auth_db -> api_gateway.
    Unrelated subsystems (e.g. frontend_ui -> database) are isolated unless explicit.
    """
    def __init__(self, edges: Optional[Dict[str, List[str]]] = None):
        self.adjacency: Dict[str, Set[str]] = {}
        if edges:
            for src, targets in edges.items():
                self.adjacency.setdefault(src.lower(), set()).update(t.lower() for t in targets)
        else:
            # Default enterprise runtime topology
            self._init_default_topology()

    def _init_default_topology(self):
        defaults = {
            "auth_service": ["database", "auth_db", "redis", "api_gateway"],
            "database": ["api_gateway", "system_health", "observability", "order_service"],
            "redis": ["api_gateway", "system_health", "auth_service"],
            "rate_limit": ["api_gateway", "system_health"],
            "api_gateway": ["system_health", "observability"]
        }
        for src, targets in defaults.items():
            self.adjacency.setdefault(src, set()).update(targets)

    def is_connected(self, source_entity: str, target_entity: str) -> bool:
        src = source_entity.lower()
        tgt = target_entity.lower()
        if src == tgt:
            return True
        # Check direct edge or 2-hop path
        if tgt in self.adjacency.get(src, set()):
            return True
        for intermediate in self.adjacency.get(src, set()):
            if tgt in self.adjacency.get(intermediate, set()):
                return True
        return False


class CausalDAG:
    """
    Manages the Directed Acyclic Graph of causal mutations with Topological Scoping & Calibrated NLI Entailment.
    """

    def __init__(
        self,
        storage: TimeMeshinStorage,
        confidence_threshold: float = 0.55,
        topology: Optional[TopologyGraph] = None
    ):
        self.storage = storage
        self.confidence_threshold = confidence_threshold
        self.topology = topology or TopologyGraph()

    def discover_and_wire_edges(self, delta: StateDelta, max_lookback_minutes: int = 120) -> List[CausalEdge]:
        """
        Discovers causal parents for a newly ingested delta based on temporal proximity,
        topological entity scoping, and calibrated directional semantic entailment.
        """
        # Fetch candidate historical deltas up to delta.timestamp
        all_deltas = self.storage.get_deltas_up_to(delta.timestamp)
        # Exclude the current delta itself
        candidates = [d for d in all_deltas if d.id != delta.id]

        new_edges: List[CausalEdge] = []
        if not candidates:
            return new_edges

        # Parse current timestamp
        t_target = self._parse_time(delta.timestamp)

        for candidate in candidates:
            # 1. Explicit parent pointer check
            if candidate.id in delta.parent_ids:
                edge = CausalEdge(
                    source_id=candidate.id,
                    target_id=delta.id,
                    confidence=1.0,
                    evidence="Explicit parent reference",
                    discovered_automatically=False
                )
                self.storage.save_causal_edge(edge)
                new_edges.append(edge)
                continue

            # 2. Temporal Window check: 0 < t_target - t_candidate <= max_lookback_minutes
            t_cand = self._parse_time(candidate.timestamp)
            if not t_target or not t_cand:
                continue

            diff_minutes = (t_target - t_cand).total_seconds() / 60.0
            if diff_minutes <= 0 or diff_minutes > max_lookback_minutes:
                continue

            # 3. Topological Entity Scoping: Check if candidate and target are architecturally connected
            is_topologically_valid = self.topology.is_connected(candidate.entity, delta.entity)
            cross_entity_mention = (
                candidate.entity.lower() in delta.causal_rationale.lower() or
                delta.entity.lower() in candidate.causal_rationale.lower()
            )

            if not is_topologically_valid and not cross_entity_mention:
                # Reject spurious correlation between isolated components (e.g. frontend CSS vs DB pool)
                continue

            # 4. Directional Calibrated Semantic / Architectural Entailment Score
            affinity = self._compute_causal_affinity(candidate, delta, diff_minutes, max_lookback_minutes)

            if affinity >= self.confidence_threshold:
                evidence_desc = f"Temporal lag {int(diff_minutes)}m; Topology ({candidate.entity}->{delta.entity}); Affinity {affinity:.2f}"
                edge = CausalEdge(
                    source_id=candidate.id,
                    target_id=delta.id,
                    confidence=affinity,
                    evidence=evidence_desc,
                    discovered_automatically=True
                )
                self.storage.save_causal_edge(edge)
                new_edges.append(edge)
                
                # Also record in delta parent_ids if not present
                if candidate.id not in delta.parent_ids:
                    delta.parent_ids.append(candidate.id)
                    self.storage.save_delta(delta)

        return new_edges

    def _compute_causal_affinity(self, prev: StateDelta, curr: StateDelta, diff_minutes: float, max_window: float) -> float:
        """
        Computes calibrated causal entailment score:
        Confidence(A -> B) = P(Entailment(c_A, c_B)) - P(Contradiction(c_A, c_B))
        Integrated with temporal decay and rack progression priors.
        """
        # 1. Temporal decay: closer events have higher causal prior
        temporal_score = 1.0 - (diff_minutes / max_window)

        # 2. Architectural Rack Progression Prior
        rack_progression_matrix = {
            ("Code", "Infra"): 0.85,
            ("Code", "Config"): 0.85,
            ("Code", "Observability"): 0.70,
            ("Config", "Infra"): 0.90,
            ("Config", "Observability"): 0.90,
            ("Infra", "Observability"): 0.95,
            ("Infra", "Infra"): 0.75,
            ("General", "Observability"): 0.60
        }
        rack_score = rack_progression_matrix.get((prev.rack, curr.rack), 0.50)

        # 3. Calibrated Semantic Entailment & Contradiction check
        v1 = prev.embedding or self.storage.embedder.embed(f"{prev.entity} {prev.attribute} {prev.causal_rationale}")
        v2 = curr.embedding or self.storage.embedder.embed(f"{curr.entity} {curr.attribute} {curr.causal_rationale}")
        p_entailment = max(0.0, LightweightEmbedder.cosine_similarity(v1, v2))

        # Check for contradictory signals (e.g., "resolved" -> "failing" without intermediate state)
        p_contradiction = 0.0
        if "resolved" in prev.causal_rationale.lower() and "normal" in prev.causal_rationale.lower():
            p_contradiction = 0.3

        calibrated_semantic_score = max(0.0, p_entailment - p_contradiction)

        # 4. Entity cross-reference boost
        entity_boost = 0.2 if prev.entity.lower() in curr.causal_rationale.lower() or curr.entity.lower() in prev.causal_rationale.lower() else 0.0

        # Composite score
        affinity = (0.25 * temporal_score) + (0.45 * rack_score) + (0.30 * calibrated_semantic_score) + entity_boost
        return min(1.0, max(0.0, affinity))

    def trace_root_cause(self, target_delta_id: str, playhead: Optional[str] = None) -> List[StateDelta]:
        """
        Performs a reverse topological search along causal edges starting from target_delta_id.
        Returns the full chronological lineage leading up to the target.
        """
        if playhead is None:
            playhead = "9999-12-31 23:59:59"

        all_deltas = {d.id: d for d in self.storage.get_deltas_up_to(playhead)}
        if target_delta_id not in all_deltas:
            return []

        # Find all edges
        edges = self.storage.get_causal_edges()
        # target_id -> list of source_ids
        parents_map: Dict[str, List[str]] = {}
        for edge in edges:
            if edge.confidence >= self.confidence_threshold:
                parents_map.setdefault(edge.target_id, []).append(edge.source_id)

        # Traverse backwards (BFS / DFS)
        visited = set()
        queue = [target_delta_id]
        lineage_ids = []

        while queue:
            curr_id = queue.pop(0)
            if curr_id in visited:
                continue
            visited.add(curr_id)
            lineage_ids.append(curr_id)

            for parent_id in parents_map.get(curr_id, []):
                if parent_id in all_deltas and parent_id not in visited:
                    queue.append(parent_id)

        # Retrieve StateDelta objects and sort chronologically
        lineage_deltas = [all_deltas[did] for did in lineage_ids if did in all_deltas]
        lineage_deltas.sort(key=lambda d: d.timestamp)
        return lineage_deltas

    def format_causal_chain_prompt(self, symptom_desc: str, target_delta_id: str, playhead: Optional[str] = None) -> str:
        """
        Formats a multi-hop causal trajectory into a prompt-ready markdown string for LLMs.
        """
        chain = self.trace_root_cause(target_delta_id, playhead)
        if not chain:
            return f"No causal history found for {symptom_desc}."

        lines = [f"### [CAUSAL TIMELINE FOR: {symptom_desc} (Target ID: {target_delta_id})]:"]
        for i, d in enumerate(chain):
            indent = "  " * i
            prefix = "|--> " if i > 0 else ""
            old_str = f" from {d.v_old}" if d.v_old else ""
            lines.append(
                f"{indent}{prefix}{d.timestamp} | {d.entity}.{d.attribute} updated{old_str} -> {d.v_new} [{d.rack}]"
            )
            if d.causal_rationale:
                lines.append(f"{indent}     Rationale: {d.causal_rationale}")

        return "\n".join(lines)

    @staticmethod
    def _parse_time(ts_str: str) -> Optional[datetime.datetime]:
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d"
        ]
        for fmt in formats:
            try:
                return datetime.datetime.strptime(ts_str, fmt)
            except ValueError:
                continue
        return None
