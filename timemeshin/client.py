"""
High-Level User-Facing Client API for TimeMeshin Next-Gen.
"""

from __future__ import annotations
import datetime
from typing import List, Dict, Any, Optional, Union, Callable
from .models import StateDelta, SemanticEvent, Keyframe, Modality
from .storage import TimeMeshinStorage, LightweightEmbedder
from .extractor import ZeroETLExtractor
from .causality import CausalDAG
from .branching import EphemeralBranch
from .engine import SpatioTemporalEngine


class TimeMeshinClient:
    """
    Next-Gen Deterministic Spatio-Temporal Memory Engine Client.
    """

    def __init__(
        self,
        db_path: str = ":memory:",
        embedder: Optional[LightweightEmbedder] = None,
        custom_llm_extractor: Optional[Callable[[str, str], List[Dict[str, Any]]]] = None,
        causal_threshold: float = 0.55,
        topology_edges: Optional[Dict[str, List[str]]] = None
    ):
        from .causality import TopologyGraph
        self.storage = TimeMeshinStorage(db_path=db_path, embedder=embedder)
        self.extractor = ZeroETLExtractor(custom_llm_extractor=custom_llm_extractor)
        self.topology = TopologyGraph(edges=topology_edges)
        self.causality = CausalDAG(self.storage, confidence_threshold=causal_threshold, topology=self.topology)
        self.engine = SpatioTemporalEngine(self.storage)

    def fast_ingest(self, raw_text: str, timestamp: Optional[str] = None, rack: str = "General") -> SemanticEvent:
        """
        Fast-Path Sync (<2ms): Writes raw text immediately to SQLite write-ahead event log.
        Returns the unparsed SemanticEvent. Can be refined later via `client.refine_pending_events()`.
        """
        import uuid
        if timestamp is None:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        event = SemanticEvent(
            id=f"event_{uuid.uuid4().hex[:8]}",
            timestamp=timestamp,
            summary=raw_text[:120],
            raw_text=raw_text,
            rack=rack,
            topics=[],
            impact_level="INFO",
            metadata={"needs_refinement": True}
        )
        self.storage.save_event(event)
        return event

    def refine_pending_events(self) -> List[StateDelta]:
        """
        Refinement Path: Asynchronously / batch processes unparsed SemanticEvents into structured StateDeltas,
        updates Keyframe compaction tables, and wires the Causal DAG.
        """
        all_events = self.storage.get_events_up_to("9999-12-31 23:59:59")
        pending = [ev for ev in all_events if ev.metadata.get("needs_refinement")]
        refined_deltas: List[StateDelta] = []

        for ev in pending:
            extracted = self.extractor.extract(raw_text=ev.raw_text, timestamp=ev.timestamp, rack=ev.rack)
            for item in extracted:
                if isinstance(item, StateDelta):
                    self.storage.save_delta(item)
                    self.causality.discover_and_wire_edges(item)
                    refined_deltas.append(item)
                elif isinstance(item, SemanticEvent):
                    ev.summary = item.summary
                    ev.topics = item.topics
                    ev.impact_level = item.impact_level

            # Clear needs_refinement flag
            ev.metadata["needs_refinement"] = False
            self.storage.save_event(ev)

        return refined_deltas

    def ingest(self, raw_text: str, timestamp: Optional[str] = None, rack: str = "General") -> List[Union[StateDelta, SemanticEvent]]:
        """
        Zero-ETL automated synchronous ingestion: parses raw unstructured prose into StateDeltas or SemanticEvents,
        indexes embeddings, and self-wires the causal DAG automatically.
        """
        if timestamp is None:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        extracted_items = self.extractor.extract(raw_text=raw_text, timestamp=timestamp, rack=rack)
        for item in extracted_items:
            if isinstance(item, StateDelta):
                self.storage.save_delta(item)
                # Self-wire into Causal DAG
                self.causality.discover_and_wire_edges(item)
            elif isinstance(item, SemanticEvent):
                self.storage.save_event(item)

        return extracted_items

    # Alias for explicit clarity
    ingest_raw = ingest

    def record_delta(
        self,
        entity: str,
        attribute: str,
        v_new: str,
        v_old: Optional[str] = None,
        causal_rationale: str = "",
        timestamp: Optional[str] = None,
        rack: str = "General",
        modality: Modality = Modality.COMMITTED,
        parent_ids: Optional[List[str]] = None
    ) -> StateDelta:
        """
        Records an explicit structured state delta directly.
        """
        import uuid
        ts = timestamp or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        delta = StateDelta(
            id=f"delta_{uuid.uuid4().hex[:8]}",
            timestamp=ts,
            entity=entity,
            rack=rack,
            attribute=attribute,
            v_old=v_old,
            v_new=v_new,
            causal_rationale=causal_rationale,
            modality=modality,
            parent_ids=parent_ids or []
        )
        self.storage.save_delta(delta)
        self.causality.discover_and_wire_edges(delta)
        return delta

    def scrub(self, playhead: Optional[str] = None) -> Keyframe:
        """
        Scrubs playhead to timestamp t and returns the consolidated ground truth state table.
        """
        if playhead is None:
            playhead = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.engine.scrub(playhead=playhead)

    def query(self, query: str, playhead: Optional[str] = None, top_k: int = 5) -> Dict[str, Any]:
        """
        Dual-coordinate (S x T) retrieval with temporal gating, dense semantic ranking, and compiled LLM context.
        """
        if playhead is None:
            playhead = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        res = self.engine.query_st(query=query, playhead=playhead, top_k_mutations=top_k)
        res["state"] = res.get("keyframe_state", {})
        res["events_count"] = len(res.get("relevant_mutations", [])) + len(res.get("relevant_events", []))
        return res

    def query_at(self, timestamp: str, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Legacy helper for querying at timestamp."""
        return self.query(query=query, playhead=timestamp, top_k=top_k)

    def ingest_event(
        self,
        timestamp: str,
        rack: str,
        entity: str,
        value: str,
        reason: str = "",
        modality: str = "COMMITTED",
        parents: Optional[List[str]] = None
    ) -> StateDelta:
        """Legacy helper for explicit event ingestion."""
        return self.record_delta(
            entity=entity,
            attribute="state",
            v_new=value,
            causal_rationale=reason,
            timestamp=timestamp,
            rack=rack,
            modality=Modality(modality),
            parent_ids=parents
        )


    def trace(self, target_id_or_entity: str, playhead: Optional[str] = None) -> List[StateDelta]:
        """
        Traces the causal trajectory leading up to a specific mutation or entity state change.
        """
        if playhead is None:
            playhead = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # If entity name was passed, find the latest delta for that entity up to playhead
        all_deltas = self.storage.get_deltas_up_to(playhead)
        target_id = target_id_or_entity
        for d in reversed(all_deltas):
            if d.entity.lower() == target_id_or_entity.lower():
                target_id = d.id
                break

        return self.causality.trace_root_cause(target_id, playhead=playhead)

    def trace_prompt(self, symptom_desc: str, target_id_or_entity: str, playhead: Optional[str] = None) -> str:
        """
        Returns a prompt-ready markdown string explaining the causal root cause chain.
        """
        if playhead is None:
            playhead = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        all_deltas = self.storage.get_deltas_up_to(playhead)
        target_id = target_id_or_entity
        for d in reversed(all_deltas):
            if d.entity.lower() == target_id_or_entity.lower():
                target_id = d.id
                break

        return self.causality.format_causal_chain_prompt(symptom_desc, target_id, playhead=playhead)

    def branch(self, from_playhead: Optional[str] = None, name: Optional[str] = None) -> EphemeralBranch:
        """
        Spawns a B-Frame speculative sandbox branch for agent counterfactual simulations.
        """
        if from_playhead is None:
            from_playhead = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return EphemeralBranch(parent_storage=self.storage, branch_playhead=from_playhead, branch_name=name)


# Backward compatibility alias
ChronoMeshClient = TimeMeshinClient

