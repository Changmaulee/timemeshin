"""
TimeMeshin Next-Gen: Deterministic Spatio-Temporal (S x T) Memory Substrate.
Authored by Chandramouli (@Changmaulee).
"""

from .models import StateDelta, SemanticEvent, Keyframe, CausalEdge, Modality, BranchConflictError
from .extractor import ZeroETLExtractor
from .storage import TimeMeshinStorage, LightweightEmbedder
from .causality import CausalDAG, TopologyGraph
from .branching import EphemeralBranch
from .engine import SpatioTemporalEngine
from .client import TimeMeshinClient

__version__ = "0.2.1"
__all__ = [
    "TimeMeshinClient",
    "StateDelta",
    "SemanticEvent",
    "Keyframe",
    "CausalEdge",
    "Modality",
    "BranchConflictError",
    "TopologyGraph",
    "ZeroETLExtractor",
    "TimeMeshinStorage",
    "LightweightEmbedder",
    "CausalDAG",
    "EphemeralBranch",
    "SpatioTemporalEngine",
]
