import json
from datetime import datetime
from typing import Any, Dict, Optional
import numpy as np


class DeltaFrame:
    """
    Represents a P-Frame (Predicted Delta Frame) in video codec terminology.
    Captures a state mutation along with its causal motivation and semantic embedding.
    """
    def __init__(
        self,
        timestamp: datetime,
        entity_id: str,
        topic_rack: str,
        attribute: str,
        old_value: Any,
        new_value: Any,
        causal_reason: str,
        raw_text: str,
        embedding: Optional[np.ndarray] = None
    ):
        self.timestamp = timestamp
        self.entity_id = entity_id
        self.topic_rack = topic_rack
        self.attribute = attribute
        self.old_value = old_value
        self.new_value = new_value
        self.causal_reason = causal_reason
        self.raw_text = raw_text
        self.embedding = embedding

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M"),
            "entity_id": self.entity_id,
            "topic_rack": self.topic_rack,
            "attribute": self.attribute,
            "change": f"{self.attribute}: '{self.old_value}' ➔ '{self.new_value}'",
            "reason": self.causal_reason,
            "raw_text": self.raw_text
        }


class Keyframe:
    """
    Represents an I-Frame (Intra-coded Frame / Snapshot) in video codec terminology.
    Contains the full consolidated ground-truth state of the universe at time T.
    """
    def __init__(self, timestamp: datetime, state_snapshot: Dict[str, Dict[str, Any]]):
        self.timestamp = timestamp
        self.state_snapshot = json.loads(json.dumps(state_snapshot))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M"),
            "state_snapshot": self.state_snapshot
        }
