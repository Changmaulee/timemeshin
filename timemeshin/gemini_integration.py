"""
Gemini Integration for TimeMeshin
Provides first-class episodic memory and video-scrubber time travel for Google Gemini models.
"""

import os
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from .client import TimeMeshinClient


# 1. Native Gemini Function / Tool Definitions
GEMINI_TIMEMESHIN_TOOLS = [
    {
        "name": "scrub_playhead",
        "description": "Scrub the memory playhead to an exact point in time to inspect ground-truth state with 0% future leakage.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "playhead_timestamp": {
                    "type": "STRING",
                    "description": "The ISO timestamp or date (e.g. '2026-09-08 14:00') to scrub the playhead to."
                }
            },
            "required": ["playhead_timestamp"]
        }
    },
    {
        "name": "trace_causal_history",
        "description": "Trace the causal lineage and historical evolution of a specific entity or decision over time.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "entity_name": {
                    "type": "STRING",
                    "description": "The name of the entity, component, or decision (e.g. 'Database', 'AuthService', 'Budget')."
                }
            },
            "required": ["entity_name"]
        }
    },
    {
        "name": "query_temporal_ground_truth",
        "description": "Perform a dual-coordinate (Semantics x Timeline) query bounded strictly to t <= playhead_timestamp.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": "The natural language question or topic to search for."
                },
                "playhead_timestamp": {
                    "type": "STRING",
                    "description": "The temporal boundary timestamp (e.g. '2026-09-08 14:00')."
                }
            },
            "required": ["query", "playhead_timestamp"]
        }
    }
]


class GeminiTimeMeshinChat:
    """
    Drop-in Gemini Chat session supercharged with TimeMeshin Deterministic Episodic Memory.
    
    Features:
      - Automatic P-Frame delta extraction from ongoing conversations.
      - 0% Future Leakage point-in-time playhead questions (`ask_at`).
      - Autonomous Gemini Tool Calling (Function Calling).
      - Persistent disk storage via SQLite.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.0-flash",
        db_path: str = "gemini_timemeshin_memory.db",
        system_instruction: Optional[str] = None
    ):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.model_name = model_name
        self.db_path = db_path
        self.memory = TimeMeshinClient(db_path=db_path)
        
        self.system_instruction = system_instruction or (
            "You are Gemini powered by TimeMeshin Spatio-Temporal Episodic Memory. "
            "You maintain an exact, deterministic understanding of how facts, systems, and "
            "decisions mutate over time. When answering questions about historical states, "
            "always evaluate strictly against the specified playhead timestamp without future data leakage."
        )
        self._init_gemini_client()

    def _init_gemini_client(self):
        """Initializes the Google GenAI or GenerativeAI client."""
        self._client = None
        try:
            import google.generativeai as genai
            if self.api_key:
                genai.configure(api_key=self.api_key)
            self._genai = genai
            self._model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=self.system_instruction
            )
            self._chat_session = self._model.start_chat(history=[])
        except ImportError:
            # Graceful fallback mode for offline/dry-run execution
            self._genai = None
            self._model = None
            self._chat_session = None

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Executes TimeMeshin tools called by Gemini."""
        if tool_name == "scrub_playhead":
            timestamp = args.get("playhead_timestamp")
            state = self.memory.scrub(playhead=timestamp)
            return {"status": "success", "playhead": timestamp, "ground_truth_state": state}
            
        elif tool_name == "trace_causal_history":
            entity = args.get("entity_name")
            history = self.memory.trace(entity)
            return {"status": "success", "entity": entity, "history": history}
            
        elif tool_name == "query_temporal_ground_truth":
            q = args.get("query")
            ts = args.get("playhead_timestamp")
            res = self.memory.query_at(timestamp=ts, query=q)
            return {"status": "success", "query": q, "playhead": ts, "result": res}
            
        return {"status": "error", "message": f"Unknown tool: {tool_name}"}

    def send_message(self, message: str, timestamp: Optional[Any] = None) -> str:
        """
        Sends a message in the conversation, automatically ingesting state deltas into TimeMeshin memory.
        """
        event_time = timestamp or datetime.utcnow()
        
        # 1. Ingest state deltas into persistent memory
        self.memory.ingest(message, timestamp=event_time)
        
        # 2. Get active ground truth state at current time
        current_state = self.memory.scrub(playhead=event_time)
        
        context_prompt = (
            f"[TimeMeshin Active Ground Truth State @ {event_time}]:\n"
            f"{json.dumps(current_state, default=str)}\n\n"
            f"User: {message}"
        )
        
        # 3. Call Gemini if available
        if self._chat_session:
            response = self._chat_session.send_message(context_prompt)
            return response.text
        else:
            return f"[Offline Gemini Simulator] Ingested message into TimeMeshin memory. Current State: {current_state}"

    def ask_at(self, playhead: Any, question: str) -> str:
        """
        Asks Gemini a question evaluated strictly at a specific point in time (t <= playhead),
        guaranteeing zero future data leakage.
        """
        # 1. Query TimeMeshin at the exact playhead
        temporal_context = self.memory.query_at(timestamp=playhead, query=question)
        state = temporal_context.get("state", {})
        deltas = temporal_context.get("relevant_deltas", [])
        
        scrub_prompt = (
            f"--- TIMEMESHIN TEMPORAL FENCE ACTIVE ---\n"
            f"PLAYHEAD TIMESTAMP: {playhead}\n"
            f"TEMPORAL RULE: You must answer strictly based on the facts known at t <= {playhead}. "
            f"Do NOT reference or assume any events occurring after this timestamp.\n\n"
            f"GROUND-TRUTH STATE AS OF {playhead}:\n"
            f"{json.dumps(state, indent=2, default=str)}\n\n"
            f"RELEVANT CAUSAL HISTORY LEADING TO PLAYHEAD:\n"
            f"{json.dumps(deltas, indent=2, default=str)}\n"
            f"-----------------------------------------\n\n"
            f"Question: {question}"
        )
        
        if self._model:
            response = self._model.generate_content(scrub_prompt)
            return response.text
        else:
            return (
                f"[TimeMeshin Ground Truth @ {playhead}]\n"
                f"State: {state}\n"
                f"Causal History: {deltas}"
            )