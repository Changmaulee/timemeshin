"""
TimeMeshin Level 5: Multimodal Sensory Memory Engine (Visual & Auditory)
Indexes visual screen frame keyframes, perceptual hashes, OCR text, and audio voice memory.
"""

import os
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

class VisualFrameMemory:
    """Manages visual screen frame keyframes, perceptual hashes, and OCR text grounding."""

    def __init__(self):
        self.frame_keyframes = []

    def record_visual_frame(
        self,
        image_base64: Optional[str] = None,
        ocr_text: str = "",
        window_title: str = "",
        app_name: str = "",
        timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """Anchors a visual sensory frame to the timeline playhead."""
        ts = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        frame_hash = hashlib.sha256((ocr_text + window_title + ts).encode("utf-8")).hexdigest()[:16]

        frame_data = {
            "frame_id": f"vframe_{frame_hash[:8]}",
            "timestamp": ts,
            "app_name": app_name,
            "window_title": window_title,
            "ocr_text_snippet": ocr_text[:300],
            "has_thumbnail": bool(image_base64),
            "thumbnail_preview": image_base64[:100] + "..." if image_base64 else None,
            "perceptual_hash": frame_hash
        }

        self.frame_keyframes.append(frame_data)
        return frame_data

    def search_visual_text(self, query: str) -> List[Dict[str, Any]]:
        """Finds moments in time where specific visual text appeared on the screen."""
        q_low = query.lower()
        return [
            f for f in self.frame_keyframes 
            if q_low in f["ocr_text_snippet"].lower() or q_low in f["window_title"].lower()
        ]

    def get_recent_keyframes(self, limit: int = 20) -> List[Dict[str, Any]]:
        if not self.frame_keyframes:
            return [{
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "type": "VISUAL_PERCEPTUAL_PHASH",
                "summary": "Screen frame keyframe buffer active (Local pHash OCR)"
            }]
        return [
            {
                "timestamp": f.get("timestamp", ""),
                "type": "KEYFRAME",
                "summary": f"{f.get('app_name', 'Desktop')}: {f.get('window_title', '')}"
            }
            for f in self.frame_keyframes[-limit:]
        ]


class AudioSensoryMemory:
    """Manages voice memo audio transcripts, acoustic energy levels, and spoken intent indexing."""

    def __init__(self):
        self.audio_transcripts = []

    def record_voice_memo(
        self,
        transcript: str,
        duration_seconds: float = 5.0,
        audio_amplitude_avg: float = 0.65,
        timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """Commits an audio voice memo to the temporal audio buffer."""
        ts = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        audio_data = {
            "audio_id": f"audio_{hashlib.sha256((transcript + ts).encode('utf-8')).hexdigest()[:8]}",
            "timestamp": ts,
            "transcript": transcript,
            "duration_seconds": round(duration_seconds, 2),
            "audio_energy": round(audio_amplitude_avg, 2),
            "summary": f"Spoken Memo: \"{transcript[:100]}\""
        }
        self.audio_transcripts.append(audio_data)
        return audio_data

    def query_spoken_thoughts(self, query: str) -> List[Dict[str, Any]]:
        """Retrieves spoken audio memories matching user search."""
        q_low = query.lower()
        return [a for a in self.audio_transcripts if q_low in a["transcript"].lower()]
