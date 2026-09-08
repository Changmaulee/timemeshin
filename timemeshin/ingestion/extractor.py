import re
from datetime import datetime
from typing import Any, Dict, List, Optional
import numpy as np

from ..core.frames import DeltaFrame


class StructuredDeltaExtractor:
    """
    Standardized Ingestion Extractor.
    Transforms raw streaming documents or LLM function-call payloads into DeltaFrames.
    """
    
    # JSON Schema definition for LLM Function Calling (OpenAI / Gemini / Anthropic)
    JSON_SCHEMA = {
        "name": "record_state_mutations",
        "description": "Extracts entity state changes, causal reasons, and topic partitions from text.",
        "parameters": {
            "type": "object",
            "properties": {
                "events": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "timestamp": {"type": "string", "description": "ISO timestamp (YYYY-MM-DD HH:MM)"},
                            "entity_id": {"type": "string", "description": "Subject entity mutating (e.g., Database, Auth, LeadEngineer)"},
                            "topic_rack": {"type": "string", "description": "Thematic rack (e.g., Infrastructure, Security, Finance)"},
                            "attribute": {"type": "string", "description": "Specific attribute changing (e.g., Engine, Budget, Status)"},
                            "old_value": {"type": "string", "description": "Previous value before mutation"},
                            "new_value": {"type": "string", "description": "New value after mutation"},
                            "causal_reason": {"type": "string", "description": "Why this change occurred (causality)"}
                        },
                        "required": ["timestamp", "entity_id", "topic_rack", "attribute", "old_value", "new_value", "causal_reason"]
                    }
                }
            },
            "required": ["events"]
        }
    }

    def __init__(self, embed_fn=None):
        self.embed_fn = embed_fn

    def parse_payload(self, event_dict: Dict[str, Any], raw_text: str) -> DeltaFrame:
        """Constructs a DeltaFrame from a validated dictionary."""
        t = datetime.strptime(event_dict["timestamp"], "%Y-%m-%d %H:%M")
        
        emb = None
        if self.embed_fn is not None:
            text_to_embed = f"{event_dict['entity_id']} {event_dict['attribute']} {event_dict['causal_reason']} {raw_text}"
            emb = self.embed_fn(text_to_embed)

        return DeltaFrame(
            timestamp=t,
            entity_id=event_dict["entity_id"],
            topic_rack=event_dict["topic_rack"],
            attribute=event_dict["attribute"],
            old_value=event_dict["old_value"],
            new_value=event_dict["new_value"],
            causal_reason=event_dict["causal_reason"],
            raw_text=raw_text,
            embedding=emb
        )
