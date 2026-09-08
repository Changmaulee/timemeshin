import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from .frames import DeltaFrame, Keyframe


class ChronoMeshEngine:
    """
    Spatio-Temporal (S x T) Dual-Coordinate Retrieval Engine.
    
    Coordinates:
      - Temporal Axis (T): Hard deterministic playhead boundaries.
      - Semantic Axis (S): Dense vector cosine ranking over historical deltas.
      - Topic Racks (R): Logical partition drawers (Infrastructure, Finance, etc.)
    """
    def __init__(self, keyframe_interval_days: int = 5):
        self.deltas: List[DeltaFrame] = []
        self.keyframes: List[Keyframe] = []
        self.keyframe_interval_days = keyframe_interval_days
        self.racks: set = set()
        self.entities: set = set()

    @property
    def delta_log(self) -> List[DeltaFrame]:
        """Provides access to chronological stream of recorded deltas."""
        return self.deltas

    def get_deltas_up_to(self, timestamp: datetime, filter_rack: Optional[str] = None) -> List[DeltaFrame]:
        """Returns all deltas occurring on or before timestamp."""
        return [
            d for d in self.deltas
            if d.timestamp <= timestamp and (filter_rack is None or d.topic_rack == filter_rack)
        ]

    def record_delta(self, delta: DeltaFrame) -> None:
        """Appends a state mutation (P-Frame) to the chronological stream."""
        self.deltas.append(delta)
        self.racks.add(delta.topic_rack)
        self.entities.add(delta.entity_id)
        self.deltas.sort(key=lambda d: d.timestamp)


    def create_keyframe(self, timestamp: datetime) -> Keyframe:
        """Compacts all state up to timestamp into a consolidated I-Frame."""
        state = self.scrub_state(timestamp)
        kf = Keyframe(timestamp, state)
        self.keyframes.append(kf)
        self.keyframes.sort(key=lambda k: k.timestamp)
        return kf

    def build_periodic_keyframes(self) -> None:
        """Automatically builds periodic Keyframes across the recorded timeline."""
        if not self.deltas:
            return
        
        first_t = self.deltas[0].timestamp
        last_t = self.deltas[-1].timestamp
        curr_t = first_t
        
        self.keyframes.clear()
        while curr_t <= last_t:
            self.create_keyframe(curr_t)
            curr_t += timedelta(days=self.keyframe_interval_days)

    def scrub_state(self, playhead_time: datetime, filter_rack: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        THE PLAYHEAD SCRUBBER:
        Reconstructs the 100% deterministic world state at timestamp T.
        Equation: State(T) = NearestKeyframe(T_last) + Sum(Deltas between T_last and T)
        """
        base_state: Dict[str, Dict[str, Any]] = {}
        last_kf_time = datetime.min

        # 1. Jump to nearest preceding Keyframe (O(1) hop)
        for kf in reversed(self.keyframes):
            if kf.timestamp <= playhead_time:
                base_state = json.loads(json.dumps(kf.state_snapshot))
                last_kf_time = kf.timestamp
                break

        # 2. Replay deltas up to playhead_time
        for delta in self.deltas:
            if last_kf_time < delta.timestamp <= playhead_time:
                if filter_rack and delta.topic_rack != filter_rack:
                    continue
                if delta.entity_id not in base_state:
                    base_state[delta.entity_id] = {}
                base_state[delta.entity_id][delta.attribute] = delta.new_value

        return base_state

    def dual_search(
        self,
        query_vector: np.ndarray,
        playhead_time: datetime,
        top_k: int = 3,
        filter_rack: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        DUAL-COORDINATE RETRIEVAL (S x T):
        1. Temporal Boundary (T): Prunes search space to timestamps <= playhead_time (0% future leak).
        2. Semantic Ranking (S): Computes cosine similarity of historical deltas.
        3. State Snapshot: Returns exact consolidated entity attributes.
        """
        # Temporal filtering
        valid_deltas = [
            d for d in self.deltas 
            if d.timestamp <= playhead_time and (filter_rack is None or d.topic_rack == filter_rack)
        ]

        scored_events = []
        for d in valid_deltas:
            if d.embedding is not None:
                sim = np.dot(query_vector, d.embedding) / (
                    np.linalg.norm(query_vector) * np.linalg.norm(d.embedding) + 1e-9
                )
                scored_events.append((float(sim), d))

        scored_events.sort(key=lambda x: x[0], reverse=True)
        top_events = scored_events[:top_k]

        return {
            "playhead_time": playhead_time.strftime("%Y-%m-%d %H:%M"),
            "exact_state": self.scrub_state(playhead_time, filter_rack=filter_rack),
            "relevant_events": [
                {
                    "similarity": round(score, 4),
                    "timestamp": d.timestamp.strftime("%Y-%m-%d %H:%M"),
                    "entity_id": d.entity_id,
                    "topic_rack": d.topic_rack,
                    "change": f"{d.attribute}: '{d.old_value}' ➔ '{d.new_value}'",
                    "reason": d.causal_reason,
                    "raw_text": d.raw_text
                }
                for score, d in top_events
            ]
        }

    def trace_entity(self, entity_id: str, up_to_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """TRACER: Extracts the complete chronological motion trajectory of an entity."""
        trajectory = []
        for d in self.deltas:
            if d.entity_id == entity_id:
                if up_to_time is None or d.timestamp <= up_to_time:
                    trajectory.append(d.to_dict())
        return trajectory
