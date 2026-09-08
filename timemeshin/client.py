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


class ChronoMeshClient:
    """
    Plug-and-Play Client for ChronoMesh.
    
    Usage:
        client = ChronoMeshClient(db_path="my_memory.db", api_key="sk-...")
        client.ingest("We switched our database to DynamoDB on Tuesday due to write contention.")
        state = client.scrub(playhead="2026-09-02 15:00")
        print(state)
    """
    def __init__(
        self,
        db_path: str = "chronomesh.db",
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
        Accepts datetime or string (e.g. '2026-09-02 14:00').
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
