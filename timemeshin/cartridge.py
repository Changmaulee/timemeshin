"""
TimeMeshin ShowLLM Cartridge Foundry & Temporal Decoder
Builds and decodes portable Movie-Codec JSON cartridges for sovereign AI runtimes.
"""

import json
import difflib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

class CartridgeBuilder:
    """Foundry for compiling TimeMeshin temporal data into swappable ShowLLM Movie-Codec JSON cartridges."""

    @staticmethod
    def build_cartridge(
        name: str,
        i_frames: List[Dict[str, Any]],
        p_frames: List[Dict[str, Any]],
        b_frames: Optional[List[Dict[str, Any]]] = None,
        author: str = "Chandramouli (@Changmaulee)",
        topics: Optional[List[str]] = None,
        description: str = ""
    ) -> Dict[str, Any]:
        """Assembles the standardized Movie-Codec Knowledge Cartridge dictionary."""
        timestamps = [f.get("timestamp", "") for f in (i_frames + p_frames) if f.get("timestamp")]
        start_t = min(timestamps) if timestamps else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        end_t = max(timestamps) if timestamps else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cartridge = {
            "": "https://timemeshin.ai/schemas/movie-codec-cartridge-v1.json",
            "cartridge_name": name,
            "version": "1.0.0",
            "engine": "TimeMeshin Movie-Codec (S x T)",
            "author": author,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "description": description or f"Sovereign Movie-Codec Knowledge Cartridge for {name}",
            "temporal_bounds": {
                "start_time": start_t,
                "end_time": end_t,
                "total_keyframes": len(i_frames),
                "total_deltas": len(p_frames)
            },
            "i_frames": i_frames,
            "p_frames": p_frames,
            "b_frames": b_frames or [],
            "semantic_index": {
                "topics": topics or ["Sovereign AI", "TimeMeshin", "Temporal Memory"],
                "extracted_entities": list(set([p.get("entity", "") for p in p_frames if p.get("entity")]))
            }
        }
        return cartridge

    @staticmethod
    def export_to_file(cartridge_dict: Dict[str, Any], filepath: str) -> str:
        """Saves cartridge as a standalone JSON file."""
        p = Path(filepath)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(cartridge_dict, f, indent=2)
        return str(p.absolute())


class CartridgeDecoder:
    """
    The ShowLLM Runtime Decoder.
    Decodes multi-dimensional Movie-Codec JSON cartridges, scrubs playheads, and reconstructs state.
    """

    def __init__(self, cartridge_data: Dict[str, Any]):
        self.data = cartridge_data
        self.name = cartridge_data.get("cartridge_name", "Untitled Cartridge")
        self.i_frames = sorted(cartridge_data.get("i_frames", []), key=lambda x: x.get("timestamp", ""))
        self.p_frames = sorted(cartridge_data.get("p_frames", []), key=lambda x: x.get("timestamp", ""))
        self.b_frames = cartridge_data.get("b_frames", [])

    @classmethod
    def from_file(cls, filepath: str) -> "CartridgeDecoder":
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(data)

    def scrub(self, playhead: Optional[str] = None) -> Dict[str, Any]:
        """
        Reconstructs the consolidated ground truth state table at or before playhead t (t <= T).
        """
        if playhead is None:
            playhead = self.data.get("temporal_bounds", {}).get("end_time", "9999-12-31")

        # 1. Find the latest I-Frame <= playhead
        active_iframe = None
        for iframe in self.i_frames:
            if iframe.get("timestamp", "") <= playhead:
                active_iframe = iframe
            else:
                break

        state_table = {}
        if active_iframe:
            state_table = dict(active_iframe.get("state_snapshot", {}))

        # 2. Roll forward all P-Frames between active_iframe and playhead
        iframe_ts = active_iframe.get("timestamp", "") if active_iframe else ""
        applied_deltas = []

        for delta in self.p_frames:
            ts = delta.get("timestamp", "")
            if ts > iframe_ts and ts <= playhead:
                entity = delta.get("entity")
                val = delta.get("v_new") or delta.get("value")
                if entity and val is not None:
                    state_table[entity] = val
                applied_deltas.append(delta)

        return {
            "playhead": playhead,
            "anchor_iframe": active_iframe.get("frame_id") if active_iframe else None,
            "state": state_table,
            "applied_deltas_count": len(applied_deltas),
            "recent_deltas": applied_deltas[-5:]
        }

    def compile_context_for_llm(self, query: str = "", playhead: Optional[str] = None) -> str:
        """
        Compiles clean, deterministic, zero-hallucination context ready to feed into any LLM.
        """
        reconstructed = self.scrub(playhead=playhead)
        state = reconstructed["state"]
        
        lines = [
            f"=== MOVIE-CODEC CARTRIDGE: [{self.name}] ===",
            f"Ground Truth Playhead Anchor: {reconstructed['playhead']}",
            f"Reconstructed State Variables ({len(state)} active):"
        ]
        for k, v in state.items():
            lines.append(f"  • {k} = {v}")
            
        lines.append("\nRecent Causal Lineage Mutations:")
        for delta in reconstructed.get("recent_deltas", []):
            ts = delta.get("timestamp", "")
            summary = delta.get("summary") or delta.get("details") or delta.get("v_new") or ""
            lines.append(f"  [{ts}] {delta.get('entity', 'State')}: {summary}")
            
        return "\n".join(lines)
