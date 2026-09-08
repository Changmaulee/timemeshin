"""
TimeMeshin: Deterministic Spatio-Temporal (S x T) Video-Scrubber Context Engine for LLM Retrieval.
"""

from .core.frames import DeltaFrame, Keyframe
from .core.engine import ChronoMeshEngine as TimeMeshinEngine
from .core.causal_dag import TimelessPhase2Engine as TimeMeshinPhase2Engine, AdvancedDelta, StateModality, EntityAliasGraph
from .ingestion.extractor import StructuredDeltaExtractor
from .ingestion.llm_client import LLMDeltaExtractor
from .storage.sqlite_store import SQLiteStorage
from .client import ChronoMeshClient as TimeMeshinClient

__version__ = "0.1.0"
__all__ = [
    "DeltaFrame",
    "Keyframe",
    "TimeMeshinEngine",
    "TimeMeshinPhase2Engine",
    "AdvancedDelta",
    "StateModality",
    "EntityAliasGraph",
    "StructuredDeltaExtractor",
    "LLMDeltaExtractor",
    "SQLiteStorage",
    "TimeMeshinClient"
]
