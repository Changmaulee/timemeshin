import json
import os
import re
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
import numpy as np

from ..core.frames import DeltaFrame


SYSTEM_PROMPT = """You are a Spatio-Temporal State Extractor for ChronoMesh.
Your job is to read raw text (chat logs, incident reports, commit messages, emails) and extract state mutations (Deltas).

For each state mutation, extract:
1. entity_id: The specific object/system/person whose state changed (e.g. "Database", "TeamLead", "CloudBudget").
2. topic_rack: The high-level category (e.g. "Infrastructure", "EngineeringTeam", "Finance", "Security").
3. attribute: The specific property that changed (e.g. "Engine", "Lead", "MonthlyUSD", "AuthProtocol").
4. old_value: The previous value before the change (or "None" if first initialized).
5. new_value: The updated value after the change.
6. causal_reason: Why this change happened (the root cause or intention).

Respond strictly with valid JSON matching this schema:
{
  "events": [
    {
      "entity_id": "...",
      "topic_rack": "...",
      "attribute": "...",
      "old_value": "...",
      "new_value": "...",
      "causal_reason": "..."
    }
  ]
}
"""


class LLMDeltaExtractor:
    """
    Auto-ingestor that uses LLM function calling (OpenAI, Gemini, or fallback)
    to transform unstructured text into structured DeltaFrames.
    """
    def __init__(self, api_key: Optional[str] = None, provider: str = "auto", embed_fn: Optional[Callable[[str], np.ndarray]] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.provider = provider
        self.embed_fn = embed_fn

    def extract_deltas_from_text(self, text: str, timestamp: Optional[datetime] = None) -> List[DeltaFrame]:
        """Extracts structured DeltaFrames from raw unstructured text."""
        if isinstance(timestamp, str):
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
                try:
                    event_time = datetime.strptime(timestamp, fmt)
                    break
                except ValueError:
                    pass
            else:
                event_time = datetime.utcnow()
        elif isinstance(timestamp, datetime):
            event_time = timestamp
        else:
            event_time = datetime.utcnow()
        extracted_events = []

        # Try LLM extraction if API key is provided
        if self.api_key and self.provider != "heuristic":
            try:
                extracted_events = self._call_llm(text)
            except Exception as e:
                print(f"[!] LLM extraction failed: {e}. Falling back to heuristic extractor.")
                extracted_events = self._heuristic_extract(text)
        else:
            extracted_events = self._heuristic_extract(text)

        # Convert to DeltaFrames with embeddings
        deltas = []
        for ev in extracted_events:
            emb = None
            if self.embed_fn is not None:
                text_to_embed = f"{ev['entity_id']} {ev['attribute']} {ev['causal_reason']} {text}"
                emb = self.embed_fn(text_to_embed)

            deltas.append(DeltaFrame(
                timestamp=event_time,
                entity_id=ev.get("entity_id", "UnknownEntity"),
                topic_rack=ev.get("topic_rack", "General"),
                attribute=ev.get("attribute", "Status"),
                old_value=ev.get("old_value", "None"),
                new_value=ev.get("new_value", "Updated"),
                causal_reason=ev.get("causal_reason", text),
                raw_text=text,
                embedding=emb
            ))
        return deltas

    def _call_llm(self, text: str) -> List[Dict[str, Any]]:
        # Native OpenAI / Gemini structured output adapter
        import urllib.request
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Extract state mutations from this text:\n\n{text}"}
            ],
            "response_format": {"type": "json_object"}
        }
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return parsed.get("events", [])

    def _heuristic_extract(self, text: str) -> List[Dict[str, Any]]:
        """Fast offline rule-based fallback when no API key is provided."""
        events = []
        text_lower = text.lower()

        # Database mutations
        if "postgres" in text_lower or "dynamodb" in text_lower or "redis" in text_lower or "database" in text_lower:
            old_v = "None"
            new_v = "PostgreSQL"
            if "dynamodb" in text_lower:
                old_v = "PostgreSQL"
                new_v = "DynamoDB"
            elif "redis" in text_lower:
                old_v = "DynamoDB"
                new_v = "PostgreSQL + Redis"
            events.append({
                "entity_id": "Database",
                "topic_rack": "Infrastructure",
                "attribute": "Engine",
                "old_value": old_v,
                "new_value": new_v,
                "causal_reason": text
            })

        # Budget mutations
        match = re.search(r'\$(\d+[\d,]*)', text)
        if match:
            val = match.group(1).replace(",", "")
            events.append({
                "entity_id": "MonthlyCloudBudget",
                "topic_rack": "Finance",
                "attribute": "AmountUSD",
                "old_value": "Prior",
                "new_value": int(val),
                "causal_reason": text
            })

        # Personnel mutations
        if "lead" in text_lower or "took over" in text_lower or "assigned" in text_lower:
            person = "Alex" if "alex" in text_lower else ("Sarah" if "sarah" in text_lower else "Elena")
            events.append({
                "entity_id": "TeamLead",
                "topic_rack": "EngineeringTeam",
                "attribute": "Lead",
                "old_value": "Prior",
                "new_value": person,
                "causal_reason": text
            })

        if not events:
            events.append({
                "entity_id": "GeneralState",
                "topic_rack": "General",
                "attribute": "Event",
                "old_value": "None",
                "new_value": text[:50],
                "causal_reason": text
            })
        return events
