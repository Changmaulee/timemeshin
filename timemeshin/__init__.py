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

# Level 3: AST & ShowLLM Cartridge Foundry
from .code_lineage import ASTCodeAnalyzer
from .cartridge import CartridgeBuilder, CartridgeDecoder

# Level 4: OS Kernel & File I/O Tracing
from .kernel_tracer import FileSystemWatcher, ProcessCommandTracer

# Level 5: Multimodal Sensory Memory
from .multimodal_memory import VisualFrameMemory, AudioSensoryMemory

# Level 6: Counterfactual Causal Simulation
from .counterfactual_engine import CounterfactualEngine, CounterfactualBranch

# Licensing & Tier Entitlements (Free L1-2 vs Pro L3-6)
from .license import LicenseManager

# Backward compatibility
ChronoMeshClient = TimeMeshinClient

__version__ = "0.2.1"
__all__ = [
    "TimeMeshinClient",
    "ChronoMeshClient",
    "LicenseManager",
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
    "ASTCodeAnalyzer",
    "CartridgeBuilder",
    "CartridgeDecoder",
    "FileSystemWatcher",
    "ProcessCommandTracer",
    "VisualFrameMemory",
    "AudioSensoryMemory",
    "CounterfactualEngine",
    "CounterfactualBranch"
]
