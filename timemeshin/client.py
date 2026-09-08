from datetime import datetime
import json
from typing import Any, Dict, List, Optional
import numpy as np

from .core.engine import ChronoMeshEngine
from .core.frames import DeltaFrame
from .ingestion.llm_client import LLMDeltaExtractor
from .storage.sqlite_store import SQLiteStorage


def default_embed_fn(text: str) -> np.ndarray:
    """Default lightweight local embedding or fallback."""
    try:
        from sentence_transformers import SentenceTransformer
        if not hasattr(default_embed_fn, "_model"):
            default_embed_fn._model = SentenceTransformer('all-MiniLM-L6-v2')
        return default_embed_fn._model.encode(text)
    except Exception:
        # Fallback deterministic pseudo-vector if sentence-transformers not installed
        rng = np.random.RandomState(abs(hash(text)) % (2**32))
        v = rng.randn(384)
        return v / np.linalg.norm(v)


class TimeMeshinClient:
    """
    Plug-and-Play Client for TimeMeshin.
    
    Usage:
        client = TimeMeshinClient(db_path="my_memory.db")
        client.ingest_event(timestamp="2026-09-01 09:00", rack="Infrastructure", entity="Database", value="DynamoDB", reason="Write lock contention")
        result = client.query_at(timestamp="2026-09-01 12:00", query="database")
        print(result["state"])
    """
    def __init__(
        self,
        db_path: str = "timemeshin.db",
        api_key: Optional[str] = None,
        keyframe_interval_days: int = 5,
        embed_fn=None
    ):
        self.db_path = db_path
        self.storage = SQLiteStorage(db_path=db_path)
        self.engine = ChronoMeshEngine(keyframe_interval_days=keyframe_interval_days)
        self.embed_fn = embed_fn or default_embed_fn
        self.extractor = LLMDeltaExtractor(api_key=api_key, embed_fn=self.embed_fn)
        
        # Hydrate from SQLite database on startup
        self._load_from_storage()

    def _load_from_storage(self) -> None:
        saved_deltas = self.storage.load_all_deltas()
        for d in saved_deltas:
            self.engine.record_delta(d)
        
        saved_keyframes = self.storage.load_all_keyframes()
        self.engine.keyframes = saved_keyframes
        if not self.engine.keyframes and self.engine.deltas:
            self.engine.build_periodic_keyframes()

    def ingest_event(
        self,
        timestamp: Any,
        rack: str = "General",
        entity: str = "Item",
        value: Any = None,
        reason: str = "",
        old_value: Any = None,
        attribute: str = "state",
        confidence: float = 1.0,
        modality: str = "COMMITTED"
    ) -> Dict[str, Any]:
        """
        Directly ingests a structured state delta (P-Frame) into the timeline.
        """
        event_time = self._parse_time(timestamp)
        semantic_summary = f"[{rack}] {entity} changed to {value} (reason: {reason})"
        embedding = self.embed_fn(semantic_summary)
        
        delta = DeltaFrame(
            timestamp=event_time,
            entity_id=entity,
            topic_rack=rack,
            attribute=attribute,
            old_value=old_value,
            new_value=value,
            causal_reason=reason,
            raw_text=semantic_summary,
            embedding=embedding
        )
        
        self.engine.record_delta(delta)
        self.storage.save_delta(delta)
        
        if len(self.engine.deltas) % 5 == 0:
            self.engine.build_periodic_keyframes()
            for kf in self.engine.keyframes:
                self.storage.save_keyframe(kf)
                
        return delta.to_dict()

    def ingest(self, text: str, timestamp: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Ingests unstructured text into the spatio-temporal memory.
        Automatically extracts deltas, generates embeddings, updates engine, and writes to SQLite.
        """
        event_time = timestamp or datetime.utcnow()
        deltas = self.extractor.extract_deltas_from_text(text, timestamp=event_time)
        
        recorded = []
        for d in deltas:
            self.engine.record_delta(d)
            self.storage.save_delta(d)
            recorded.append(d.to_dict())

        # Update keyframes periodically
        self.engine.build_periodic_keyframes()
        for kf in self.engine.keyframes:
            self.storage.save_keyframe(kf)

        return recorded

    def _parse_time(self, t: Any) -> datetime:
        if isinstance(t, datetime):
            return t
        if isinstance(t, str):
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
                try:
                    return datetime.strptime(t, fmt)
                except ValueError:
                    pass
            try:
                return datetime.fromisoformat(t.replace("Z", "+00:00"))
            except ValueError:
                pass
        return datetime.utcnow()

    def scrub(self, playhead: Any, filter_rack: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Reconstructs the exact, 100% deterministic ground-truth state at any point in time.
        Accepts datetime or string (e.g. '2026-09-02 14:00').
        """
        playhead_dt = self._parse_time(playhead)
        return self.engine.scrub_state(playhead_dt, filter_rack=filter_rack)

    def query_at(
        self,
        timestamp: Any,
        query: str = "",
        top_k: int = 5,
        filter_rack: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Convenient playhead time-travel query returning state snapshot, events, and causal summary.
        """
        playhead_dt = self._parse_time(timestamp)
        raw_state = self.engine.scrub_state(playhead_dt, filter_rack=filter_rack)
        
        # Flatten state: if entity has single 'state' or 'value' attribute, extract directly
        flat_state = {}
        for entity, attrs in raw_state.items():
            if isinstance(attrs, dict):
                if len(attrs) == 1 and ("state" in attrs or "value" in attrs):
                    flat_state[entity] = list(attrs.values())[0]
                else:
                    flat_state[entity] = attrs
            else:
                flat_state[entity] = attrs
                
        # Retrieve causal history leading up to this time
        if hasattr(self.engine, 'get_deltas_up_to'):
            deltas_up_to = self.engine.get_deltas_up_to(playhead_dt, filter_rack=filter_rack)
        else:
            all_deltas = getattr(self.engine, 'deltas', getattr(self.engine, 'delta_log', []))
            deltas_up_to = [
                d for d in all_deltas
                if getattr(d, 'timestamp', datetime.min) <= playhead_dt and (filter_rack is None or getattr(d, 'topic_rack', None) == filter_rack)
            ]
        
        causal_steps = []
        for d in deltas_up_to[-6:]:
            ent = getattr(d, 'entity_id', getattr(d, 'entity', 'Item'))
            val = getattr(d, 'new_value', getattr(d, 'value', ''))
            reason = getattr(d, 'causal_reason', getattr(d, 'reason', 'Delta'))
            ts_str = d.timestamp.strftime('%Y-%m-%d %H:%M') if hasattr(d, 'timestamp') and isinstance(d.timestamp, datetime) else str(getattr(d, 'timestamp', ''))
            causal_steps.append(f"[{ts_str}] {ent} ➔ {val} ({reason or 'Delta'})")
            
        causal_summary = " ➔\n".join(causal_steps) if causal_steps else "Initial State Established"
        
        return {
            "timestamp": playhead_dt,
            "state": flat_state,
            "raw_state": raw_state,
            "causal_summary": causal_summary,
            "events_count": len(deltas_up_to)
        }

    def query(
        self,
        question: str,
        playhead: Any,
        top_k: int = 3,
        filter_rack: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Dual-Coordinate S x T Query:
        Returns the exact state snapshot + top ranked causal events leading up to playhead.
        """
        playhead_dt = self._parse_time(playhead)
        q_vec = self.embed_fn(question)
        return self.engine.dual_search(
            query_vector=q_vec,
            playhead_time=playhead_dt,
            top_k=top_k,
            filter_rack=filter_rack
        )

    def trace(self, entity_id: str, up_to_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Returns the full historical trajectory of a specific entity."""
        return self.engine.trace_entity(entity_id, up_to_time=up_to_time)


# Backward compatibility alias
ChronoMeshClient = TimeMeshinClient

