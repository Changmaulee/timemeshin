"""
Zero-ETL Semantic State Extractor.
Parses raw unstructured text (incident logs, Slack messages, Git diffs, PR reviews)
into structured StateDelta mutations or fallback SemanticEvents.
"""

from __future__ import annotations
import re
import uuid
import datetime
from typing import List, Union, Optional, Callable, Dict, Any
from .models import StateDelta, SemanticEvent, Modality


class ZeroETLExtractor:
    """
    Automated Semantic Extractor that transforms unstructured engineering prose into
    deterministic state deltas (P-Frames) and anchored semantic events.
    """

    def __init__(self, custom_llm_extractor: Optional[Callable[[str, str], List[Dict[str, Any]]]] = None):
        """
        :param custom_llm_extractor: Optional callable `(raw_text, timestamp) -> list of delta/event dicts`
        """
        self.custom_llm_extractor = custom_llm_extractor

    def extract(self, raw_text: str, timestamp: Optional[str] = None, rack: str = "General") -> List[Union[StateDelta, SemanticEvent]]:
        """
        Extracts StateDelta(s) or SemanticEvent(s) from unstructured text.
        """
        if timestamp is None:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. If a custom LLM / SLM extractor is supplied, use it
        if self.custom_llm_extractor:
            try:
                results = self.custom_llm_extractor(raw_text, timestamp)
                extracted_items = []
                for item in results:
                    if item.get("type") == "delta" or "entity" in item:
                        delta = StateDelta(
                            id=item.get("id", f"delta_{uuid.uuid4().hex[:8]}"),
                            timestamp=item.get("timestamp", timestamp),
                            entity=item.get("entity", "system"),
                            rack=item.get("rack", rack),
                            attribute=item.get("attribute", "state"),
                            v_old=item.get("v_old"),
                            v_new=str(item.get("v_new", "")),
                            causal_rationale=item.get("causal_rationale", raw_text),
                            modality=Modality(item.get("modality", Modality.COMMITTED.value)),
                            parent_ids=item.get("parent_ids", [])
                        )
                        extracted_items.append(delta)
                    else:
                        event = SemanticEvent(
                            id=item.get("id", f"event_{uuid.uuid4().hex[:8]}"),
                            timestamp=item.get("timestamp", timestamp),
                            summary=item.get("summary", raw_text[:100]),
                            raw_text=raw_text,
                            rack=item.get("rack", rack),
                            topics=item.get("topics", []),
                            impact_level=item.get("impact_level", "INFO")
                        )
                        extracted_items.append(event)
                if extracted_items:
                    return extracted_items
            except Exception as e:
                # Fallback to heuristic parser on failure
                pass

        # 2. Rule-based / Heuristic pattern extraction (Fast Zero-Dependency Engine)
        deltas = self._heuristic_extract_deltas(raw_text, timestamp, rack)
        if deltas:
            return deltas

        # 3. Fallback: Treat as timestamp-anchored SemanticEvent
        event_id = f"event_{uuid.uuid4().hex[:8]}"
        summary = self._generate_summary(raw_text)
        topics = self._extract_topics(raw_text)
        impact = "CRITICAL" if any(w in raw_text.lower() for w in ["outage", "down", "504", "crash", "corrupt", "failed", "breach"]) else "INFO"

        return [
            SemanticEvent(
                id=event_id,
                timestamp=timestamp,
                summary=summary,
                raw_text=raw_text,
                rack=rack,
                topics=topics,
                impact_level=impact
            )
        ]

    def _heuristic_extract_deltas(self, raw_text: str, timestamp: str, default_rack: str) -> List[StateDelta]:
        """
        Identifies state transition patterns like:
        - "Switched X from A to B"
        - "Updated X from 100 -> 20"
        - "Reduced database max_connections 100 -> 20"
        - "Changed primary database from Postgres to DynamoDB"
        - "Set rate_limit = 500"
        - "Merged PR #402: auth_service updated to v2.1"
        """
        deltas = []
        text = raw_text.strip()

        # Determine modality
        modality = Modality.COMMITTED
        lower = text.lower()
        if "propose" in lower or "rfc" in lower or "pr #" in lower and "open" in lower:
            modality = Modality.PROPOSED
        elif "evaluat" in lower or "testing" in lower or "benchmark" in lower or "canary" in lower:
            modality = Modality.EVALUATING

        # Pattern 1: Incident / Outage status change (e.g. "HTTP 504 Gateway Timeouts detected on API gateway")
        if re.search(r'\b(?:http\s*(?:504|502|500|503)|504\s*gateway|502\s*bad|gateway\s*timeout|outage|latency\s*spike)\b', text, re.IGNORECASE):
            entity = "api_gateway" if "gateway" in text.lower() else "system_health"
            deltas.append(StateDelta(
                id=f"delta_{uuid.uuid4().hex[:8]}",
                timestamp=timestamp,
                entity=entity,
                rack="Observability",
                attribute="status",
                v_old="HEALTHY",
                v_new="DEGRADED / 504_TIMEOUT",
                causal_rationale=text,
                modality=Modality.COMMITTED
            ))
            return deltas

        # Pattern 2: PR merged or version deployed (e.g., "PR #402 merged (auth_service updated to v2.0)")
        p_pr = re.search(r'PR\s*#?([0-9]+)\s+merged\s*\(([^)]+)\)', text, re.IGNORECASE)
        if p_pr:
            pr_num = p_pr.group(1)
            desc = p_pr.group(2)
            deltas.append(StateDelta(
                id=f"delta_{uuid.uuid4().hex[:8]}",
                timestamp=timestamp,
                entity="auth_service" if "auth" in desc.lower() else f"PR_{pr_num}",
                rack="Code",
                attribute="version" if "v" in desc.lower() else "status",
                v_old=None,
                v_new="merged",
                causal_rationale=f"PR #{pr_num} merged: {desc}",
                modality=Modality.COMMITTED
            ))
            return deltas

        # Pattern 3: Initial setup or set database engine
        p_init = re.search(r'(?:initial\s+setup:?\s*)?(?:primary\s+)?(database|db|redis|postgres|cache)\s+set\s+to\s+([A-Za-z0-9_\-]+)(?:\s*\(([^)]+)\))?', text, re.IGNORECASE)
        if p_init:
            entity = "database" if "db" in p_init.group(1).lower() or "database" in p_init.group(1).lower() else p_init.group(1).lower()
            engine_val = p_init.group(2).strip()
            extra_params = p_init.group(3)

            deltas.append(StateDelta(
                id=f"delta_{uuid.uuid4().hex[:8]}",
                timestamp=timestamp,
                entity=entity,
                rack="Infra",
                attribute="engine",
                v_old=None,
                v_new=engine_val,
                causal_rationale=text,
                modality=modality
            ))

            if extra_params:
                # Parse e.g. "max_connections=100" or "port=5432"
                for param in extra_params.split(","):
                    if "=" in param:
                        k, v = param.split("=", 1)
                        deltas.append(StateDelta(
                            id=f"delta_{uuid.uuid4().hex[:8]}",
                            timestamp=timestamp,
                            entity=entity,
                            rack="Infra",
                            attribute=k.strip(),
                            v_old=None,
                            v_new=v.strip(),
                            causal_rationale=text,
                            modality=modality
                        ))
            return deltas

        # Pattern 4: "Switched primary database from Postgres to DynamoDB due to write lock contention"
        p3 = re.search(r'switched\s+(?:primary\s+)?([A-Za-z0-9_\-]+)\s+from\s+([A-Za-z0-9_\-]+)\s+to\s+([A-Za-z0-9_\-]+)(?:\s+due to\s+(.*))?', text, re.IGNORECASE)
        if p3:
            entity = p3.group(1).strip()
            v_old = p3.group(2).strip()
            v_new = p3.group(3).strip()
            rationale = p3.group(4) if p3.group(4) else text
            rack = "Infra" if "db" in entity.lower() or "database" in entity.lower() else default_rack
            deltas.append(StateDelta(
                id=f"delta_{uuid.uuid4().hex[:8]}",
                timestamp=timestamp,
                entity=entity,
                rack=rack,
                attribute="engine" if entity.lower() in ["database", "db"] else "type",
                v_old=v_old,
                v_new=v_new,
                causal_rationale=rationale.strip(),
                modality=modality
            ))
            return deltas

        # Pattern 4: [Entity] [attribute] [changed/reduced/increased/updated] [from] X [to/->] Y
        p1 = re.search(r'(?:(?:updated|changed|switched|reduced|increased|set|migrated)\s+)?([A-Za-z0-9_\-\.]+)(?:\s+([A-Za-z0-9_\-\.]+))?\s+(?:from\s+)?([A-Za-z0-9_\-\.]+)\s+(?:to|->|=>)\s+([A-Za-z0-9_\-\.]+)', text, re.IGNORECASE)
        if p1:
            part1, part2, v_old, v_new = p1.group(1), p1.group(2), p1.group(3), p1.group(4)
            entity = part1
            attribute = part2 if part2 else "value"
            rack = default_rack
            if any(k in entity.lower() for k in ["db", "database", "redis", "postgres", "infra", "server", "pool"]):
                rack = "Infra"
            elif any(k in entity.lower() for k in ["service", "auth", "api", "pr", "commit", "code"]):
                rack = "Code"
            elif any(k in entity.lower() for k in ["rate_limit", "config", "flag", "env"]):
                rack = "Config"

            deltas.append(StateDelta(
                id=f"delta_{uuid.uuid4().hex[:8]}",
                timestamp=timestamp,
                entity=entity,
                rack=rack,
                attribute=attribute,
                v_old=v_old,
                v_new=v_new,
                causal_rationale=text,
                modality=modality
            ))
            return deltas

        return deltas

        return deltas

    def _generate_summary(self, text: str) -> str:
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if not lines:
            return ""
        first = lines[0]
        return first[:120] + ("..." if len(first) > 120 else "")

    def _extract_topics(self, text: str) -> List[str]:
        keywords = [
            "database", "postgres", "dynamodb", "aurora", "redis", "latency", 
            "timeout", "auth", "security", "infra", "config", "deploy", 
            "rollback", "policy", "migration", "sync", "release", "incident", "outage", "scale"
        ]
        found = []
        lower = text.lower()
        for kw in keywords:
            if kw in lower:
                found.append(kw)
        return found
