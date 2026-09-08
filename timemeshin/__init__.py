"""
TimeMeshin: Deterministic Spatio-Temporal (S x T) Video-Scrubber Context Engine for LLM Retrieval.
"""

from .core.frames import DeltaFrame, Keyframe
from .core.engine import ChronoMeshEngine as TimeMeshinEngine
from .core.causal_dag import TimelessPhase2Engine as TimeMeshinPhase2Engine, AdvancedDelta, StateModality, EntityAliasGraph
from .ingestion.extractor import StructuredDeltaExtractor
from .ingestion.llm_client import LLMDeltaExtractor
from .ingestion.document_loader import DocumentLoader
from .ingestion.folder_watcher import FolderWatcher
from .storage.sqlite_store import SQLiteStorage
from .client import ChronoMeshClient as TimeMeshinClient
from .gemini_integration import GeminiTimeMeshinChat, GEMINI_TIMEMESHIN_TOOLS

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
    "DocumentLoader",
    "FolderWatcher",
    "SQLiteStorage",
    "TimeMeshinClient",
    "GeminiTimeMeshinChat",
    "GEMINI_TIMEMESHIN_TOOLS"
]