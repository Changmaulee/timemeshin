from datetime import datetime
import json
from typing import Any, Dict, List, Optional
import numpy as np

from .core.engine import ChronoMeshEngine
from .core.frames import DeltaFrame
from .ingestion.llm_client import LLMDeltaExtractor
from .storage.sqlite_store import SQLiteStorage


def default_embed_fn(text: str) -> np.ndarray:
    """Default lightweight local embedding or fallback."""
    try:
        from sentence_transformers import SentenceTransformer
        if not hasattr(default_embed_fn, "_model"):
            default_embed_fn._model = SentenceTransformer('all-MiniLM-L6-v2')
        return default_embed_fn._model.encode(text)
    except Exception:
        # Fallback deterministic pseudo-vector if sentence-transformers not installed
        rng = np.random.RandomState(abs(hash(text)) % (2**32))
        v = rng.randn(384)
        return v / np.linalg.norm(v)


class TimeMeshinClient:
    """
    Plug-and-Play Client for TimeMeshin.
    
    Usage:
        client = TimeMeshinClient(db_path="my_memory.db")
        client.ingest_event(timestamp="2026-09-01 09:00", rack="Infrastructure", entity="Database", value="DynamoDB", reason="Write lock contention")
        result = client.query_at(timestamp="2026-09-01 12:00", query="database")
        print(result["state"])
    """
    def __init__(
        self,
        db_path: str = "timemeshin.db",
        api_key: Optional[str] = None,
        keyframe_interval_days: int = 5,
        embed_fn=None
    ):
        self.db_path = db_path
        self.storage = SQLiteStorage(db_path=db_path)
        self.engine = ChronoMeshEngine(keyframe_interval_days=keyframe_interval_days)
        self.embed_fn = embed_fn or default_embed_fn
        self.extractor = LLMDeltaExtractor(api_key=api_key, embed_fn=self.embed_fn)
        
        # Hydrate from SQLite database on startup
        self._load_from_storage()

    def _load_from_storage(self) -> None:
        saved_deltas = self.storage.load_all_deltas()
        for d in saved_deltas:
            self.engine.record_delta(d)
        
        saved_keyframes = self.storage.load_all_keyframes()
        self.engine.keyframes = saved_keyframes
        if not self.engine.keyframes and self.engine.deltas:
            self.engine.build_periodic_keyframes()

    def ingest_event(
        self,
        timestamp: Any,
        rack: str = "General",
        entity: str = "Item",
        value: Any = None,
        reason: str = "",
        old_value: Any = None,
        attribute: str = "state",
        confidence: float = 1.0,
        modality: str = "COMMITTED"
    ) -> Dict[str, Any]:
        """
        Directly ingests a structured state delta (P-Frame) into the timeline.
        """
        event_time = self._parse_time(timestamp)
        semantic_summary = f"[{rack}] {entity} changed to {value} (reason: {reason})"
        embedding = self.embed_fn(semantic_summary)
        
        delta = DeltaFrame(
            timestamp=event_time,
            entity_id=entity,
            topic_rack=rack,
            attribute=attribute,
            old_value=old_value,
            new_value=value,
            causal_reason=reason,
            raw_text=semantic_summary,
            embedding=embedding
        )
        
        self.engine.record_delta(delta)
        self.storage.save_delta(delta)
        
        if len(self.engine.deltas) % 5 == 0:
            self.engine.build_periodic_keyframes()
            for kf in self.engine.keyframes:
                self.storage.save_keyframe(kf)
                
        return delta.to_dict()

    def ingest(self, text: str, timestamp: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Ingests unstructured text into the spatio-temporal memory.
        Automatically extracts deltas, generates embeddings, updates engine, and writes to SQLite.
        """
        event_time = timestamp or datetime.utcnow()
        deltas = self.extractor.extract_deltas_from_text(text, timestamp=event_time)
        
        recorded = []
        for d in deltas:
            self.engine.record_delta(d)
            self.storage.save_delta(d)
            recorded.append(d.to_dict())

        # Update keyframes periodically
        self.engine.build_periodic_keyframes()
        for kf in self.engine.keyframes:
            self.storage.save_keyframe(kf)

        return recorded

    def _parse_time(self, t: Any) -> datetime:
        if isinstance(t, datetime):
            return t
        if isinstance(t, str):
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
                try:
                    return datetime.strptime(t, fmt)
                except ValueError:
                    pass
            try:
                return datetime.fromisoformat(t.replace("Z", "+00:00"))
            except ValueError:
                pass
        return datetime.utcnow()

    def scrub(self, playhead: Any, filter_rack: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Reconstructs the exact, 100% deterministic ground-truth state at any point in time.
        Accepts datetime or string (e.g. '2026-09-02 14:00').
        """
        playhead_dt = self._parse_time(playhead)
        return self.engine.scrub_state(playhead_dt, filter_rack=filter_rack)

    def query_at(
        self,
        timestamp: Any,
        query: str = "",
        top_k: int = 5,
        filter_rack: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Convenient playhead time-travel query returning state snapshot, events, and causal summary.
        """
        playhead_dt = self._parse_time(timestamp)
        raw_state = self.engine.scrub_state(playhead_dt, filter_rack=filter_rack)
        
        # Flatten state: if entity has single 'state' or 'value' attribute, extract directly
        flat_state = {}
        for entity, attrs in raw_state.items():
            if isinstance(attrs, dict):
                if len(attrs) == 1 and ("state" in attrs or "value" in attrs):
                    flat_state[entity] = list(attrs.values())[0]
                else:
                    flat_state[entity] = attrs
            else:
                flat_state[entity] = attrs
                
        # Retrieve causal history leading up to this time
        if hasattr(self.engine, 'get_deltas_up_to'):
            deltas_up_to = self.engine.get_deltas_up_to(playhead_dt, filter_rack=filter_rack)
        else:
            all_deltas = getattr(self.engine, 'deltas', getattr(self.engine, 'delta_log', []))
            deltas_up_to = [
                d for d in all_deltas
                if getattr(d, 'timestamp', datetime.min) <= playhead_dt and (filter_rack is None or getattr(d, 'topic_rack', None) == filter_rack)
            ]
        
        causal_steps = []
        for d in deltas_up_to[-6:]:
            ent = getattr(d, 'entity_id', getattr(d, 'entity', 'Item'))
            val = getattr(d, 'new_value', getattr(d, 'value', ''))
            reason = getattr(d, 'causal_reason', getattr(d, 'reason', 'Delta'))
            ts_str = d.timestamp.strftime('%Y-%m-%d %H:%M') if hasattr(d, 'timestamp') and isinstance(d.timestamp, datetime) else str(getattr(d, 'timestamp', ''))
            causal_steps.append(f"[{ts_str}] {ent} ➔ {val} ({reason or 'Delta'})")
            
        causal_summary = " ➔\n".join(causal_steps) if causal_steps else "Initial State Established"
        
        return {
            "timestamp": playhead_dt,
            "state": flat_state,
            "raw_state": raw_state,
            "causal_summary": causal_summary,
            "events_count": len(deltas_up_to)
        }

    def query(
        self,
        question: str,
        playhead: Any,
        top_k: int = 3,
        filter_rack: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Dual-Coordinate S x T Query:
        Returns the exact state snapshot + top ranked causal events leading up to playhead.
        """
        playhead_dt = self._parse_time(playhead)
        q_vec = self.embed_fn(question)
        return self.engine.dual_search(
            query_vector=q_vec,
            playhead_time=playhead_dt,
            top_k=top_k,
            filter_rack=filter_rack
        )

    def generate_context_prompt(
        self,
        question: str,
        playhead: Any = None,
        filter_rack: Optional[str] = None
    ) -> str:
        """
        Synthesizes a pristine LLM Context Prompt that fences temporal boundaries strictly.
        Can be plugged directly into OpenAI, Anthropic, Gemini, or local models.
        """
        playhead_dt = self._parse_time(playhead) if playhead else (self.engine.deltas[-1].timestamp if self.engine.deltas else datetime.utcnow())
        res = self.query_at(playhead_dt, filter_rack=filter_rack)
        
        state_lines = [f"- {k}: {v}" for k, v in res["state"].items()]
        state_text = "\n".join(state_lines) if state_lines else "No variables recorded."
        
        prompt = f"""=== GROUND-TRUTH WORLD STATE (AT PLAYHEAD: {playhead_dt.strftime('%Y-%m-%d %H:%M')}) ===
Strict Temporal Rule: Do NOT reference any events occurring after this timestamp.

Active State Snapshot:
{state_text}

Causal Trajectory Leading Up to this Moment:
{res['causal_summary']}
========================================================================

User Question: {question}

Answer based ONLY on the ground-truth state and causal trajectory up to {playhead_dt.strftime('%Y-%m-%d %H:%M')}:"""
        return prompt

    def chat(
        self,
        user_message: str,
        playhead: Any = None,
        model_name: Optional[str] = None
    ) -> str:
        """
        Conversational AI Assistant with temporal ground-truth memory.
        Answers naturally based strictly on the world state at the playhead.
        """
        playhead_dt = self._parse_time(playhead) if playhead else (self.engine.deltas[-1].timestamp if self.engine.deltas else datetime.utcnow())
        res = self.query_at(playhead_dt, query=user_message)
        time_str = playhead_dt.strftime("%Y-%m-%d %H:%M")
        
        # 1. Check for Gemini / OpenAI API keys for direct LLM generation
        openai_key = os.environ.get("OPENAI_API_KEY")
        gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        
        prompt = self.generate_context_prompt(user_message, playhead=playhead_dt)
        
        if gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)
                if response and response.text:
                    return response.text
            except Exception:
                pass

        if openai_key:
            try:
                import openai
                client_ai = openai.OpenAI(api_key=openai_key)
                resp = client_ai.chat.completions.create(
                    model=model_name or "gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a helpful, clear, and precise engineering assistant. Strictly adhere to the ground-truth state provided without leaking future information."},
                        {"role": "user", "content": prompt}
                    ]
                )
                return resp.choices[0].message.content
            except Exception:
                pass

        # 2. Built-in Conversational Intent Resolver (Zero-key offline assistant)
        q_clean = user_message.lower().strip()
        all_deltas = getattr(self.engine, 'deltas', getattr(self.engine, 'delta_log', []))
        past_deltas = [d for d in all_deltas if getattr(d, 'timestamp', datetime.min) <= playhead_dt]
        
        # Intent A: "Why" / "Reason" / "Cause" / "Purpose"
        if any(w in q_clean for w in ["why", "reason", "cause", "purpose", "how come"]):
            recent_reasons = []
            for d in past_deltas[-5:]:
                ent = getattr(d, 'entity_id', 'Item')
                val = str(getattr(d, 'new_value', ''))
                reason = getattr(d, 'causal_reason', '')
                if reason and reason != 'Delta':
                    recent_reasons.append(f"• **{ent}**: {reason} (Result: {val[:60]})")
                else:
                    recent_reasons.append(f"• **{ent}**: Updated to {val[:60]}")
            
            reasons_text = "\n".join(recent_reasons) if recent_reasons else "• Operations proceeded according to the scheduled architecture roadmap."
            return f"### 💡 Causal Context & Motivations (as of {time_str}):\n\nThe recent changes were initiated for the following reasons:\n\n{reasons_text}\n\n*(🛡️ Strictly fenced at {time_str} with 0% future leakage)*"

        # Intent B: "Who" / "Author" / "Team" / "Lead"
        if any(w in q_clean for w in ["who", "author", "lead", "team", "person", "contributor"]):
            authors = set()
            for d in past_deltas[-10:]:
                val = str(getattr(d, 'new_value', ''))
                if ":" in val:
                    authors.add(val.split(":")[0].strip())
            authors_list = ", ".join([f"**{a}**" for a in list(authors)[:6]]) if authors else "Core Engineering Team"
            return f"### 👥 Active Contributors & Personnel (as of {time_str}):\n\nThe active contributors/leads responsible for state modifications up to this point include: {authors_list}."

        # Intent C: General / Specific Entity Question
        matched_items = []
        for k, v in res["state"].items():
            if any(term in k.lower() or term in str(v).lower() for term in q_clean.split() if len(term) > 2):
                matched_items.append((k, str(v)))
                
        if matched_items:
            bullets = "\n".join([f"• **{k}**: {v[:75]}" for k, v in matched_items[:6]])
            return f"### 📋 System Status & Active Configuration (as of {time_str}):\n\n{bullets}\n\n**Recent Trajectory:**\n{res['causal_summary']}"
        else:
            # Clean overview of the latest 5 state items
            latest_items = list(res["state"].items())[:5]
            bullets = "\n".join([f"• **{k}**: {str(v)[:75]}" for k, v in latest_items])
            return f"### 🌐 System Overview (as of {time_str}):\n\nCurrently, there are **{len(res['state'])} active state entities** tracked in memory:\n\n{bullets}\n\n**Latest Timeline Progression:**\n{res['causal_summary']}"

    def ask(self, question: str, playhead: Any = None) -> str:
        """Convenient alias for chat."""
        return self.chat(user_message=question, playhead=playhead)



# Backward compatibility alias

ChronoMeshClient = TimeMeshinClient


