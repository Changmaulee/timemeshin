"""
Folder Watcher & Spatio-Temporal Chat Aligner for TimeMeshin
Monitors a dropzone folder, ingests chats (.html, .pdf, .md, .txt, .json),
filters out-of-context noise, and aligns events horizontally across timeline (T)
and vertically across topic swimlanes (S).
"""

import os
import sys
import time
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

from .document_loader import DocumentLoader
from ..client import TimeMeshinClient
from ..core.frames import DeltaFrame

# Noise filtering patterns: Out-of-context banter, greetings, weather, non-mutating chit-chat
NOISE_PATTERNS = [
    r"^(hi|hello|hey|good morning|good evening|howdy|sup)[\s\.,!]*$",
    r"how are you",
    r"what('s| is) the weather",
    r"tell me a joke",
    r"thanks?(\s+you)?[\s\.,!]*$",
    r"you('re| are) welcome",
    r"who are you",
    r"can you hear me",
    r"testing 1 2 3",
    r"^ok[\s\.,!]*$",
    r"^cool[\s\.,!]*$"
]

DEFAULT_TOPIC_KEYWORDS = {
    "Database & Storage": ["database", "postgres", "dynamodb", "redis", "mongodb", "mysql", "sqlite", "table", "schema", "query", "migration"],
    "Auth & Security": ["auth", "oauth", "jwt", "token", "login", "sso", "permission", "rbac", "password", "security", "encryption"],
    "Architecture & Core": ["architecture", "refactor", "service", "microservice", "api", "pipeline", "engine", "protocol", "codec", "design"],
    "Infrastructure & Cloud": ["cloud", "aws", "docker", "kubernetes", "deploy", "server", "cluster", "latency", "hosting", "container"],
    "Budget & Operations": ["budget", "cost", "dollar", "$", "usd", "spend", "hiring", "team", "assign", "contract", "billing"],
    "UI & Frontend": ["ui", "frontend", "dashboard", "css", "html", "react", "vue", "tailwind", "button", "slider", "widget", "theme"]
}


class FolderWatcher:
    """
    Watches an inbox directory, processes incoming chat documents,
    filters irrelevant noise, and organizes events into an (S x T) Spatio-Temporal Matrix.
    """
    def __init__(
        self,
        watch_dir: str = "dropzone",
        db_path: Optional[str] = None,
        matrix_output_path: Optional[str] = None
    ):
        self.watch_dir = Path(watch_dir).resolve()
        self.watch_dir.mkdir(parents=True, exist_ok=True)
        
        # Default database and output JSON directly inside the watched folder
        self.db_path = db_path or str(self.watch_dir / "timeline_memory.db")
        if matrix_output_path:
            self.matrix_output_path = Path(matrix_output_path).resolve()
        else:
            self.matrix_output_path = self.watch_dir / "matrix_data.json"

        self.matrix_js_path = self.watch_dir / "matrix_data.js"

        self.loader = DocumentLoader()
        self.client = TimeMeshinClient(db_path=self.db_path)
        self.processed_files = set()
        self._load_processed_history()

    def _load_processed_history(self):
        """Loads record of previously processed files to prevent duplicate ingestion."""
        history_file = self.watch_dir / ".processed_files.json"
        if history_file.exists():
            try:
                self.processed_files = set(json.loads(history_file.read_text(encoding="utf-8")))
            except Exception:
                self.processed_files = set()

    def _save_processed_history(self):
        history_file = self.watch_dir / ".processed_files.json"
        history_file.write_text(json.dumps(list(self.processed_files)), encoding="utf-8")

    def is_noise_or_out_of_context(self, text: str) -> bool:
        """Determines if a message is out-of-context noise with no state significance."""
        cleaned = text.strip().lower()
        if len(cleaned) < 4:
            return True
        for pat in NOISE_PATTERNS:
            if re.search(pat, cleaned, re.IGNORECASE):
                return True
        return False

    def classify_topic_rack(self, text: str, entity_name: str = "") -> str:
        """Classifies an event or chat into its vertical topic swimlane (S-axis)."""
        combined = f"{entity_name} {text}".lower()
        for topic, keywords in DEFAULT_TOPIC_KEYWORDS.items():
            for kw in keywords:
                if kw in combined:
                    return topic
        return "General & Discussion"

    def process_file(self, file_path: Path) -> int:
        """Parses a single file, filters noise, extracts deltas, and updates the timeline."""
        print(f"[*] Processing incoming document: {file_path.name}")
        try:
            docs = self.loader.load_file(str(file_path))
            if isinstance(docs, dict):
                docs = [docs]
            elif isinstance(docs, str):
                docs = [{"content": docs}]

            ingested_count = 0
            filtered_noise_count = 0
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)

            turn_idx = 0
            for doc_item in docs:
                turn_idx += 1
                if isinstance(doc_item, dict):
                    content = (doc_item.get("text") or doc_item.get("content") or "").strip()
                    item_time = doc_item.get("timestamp")
                else:
                    content = str(doc_item).strip()
                    item_time = None

                if not content:
                    continue

                # 1. Noise / Out-of-context Filter Gating
                if self.is_noise_or_out_of_context(content):
                    filtered_noise_count += 1
                    continue

                # 2. Extract or approximate timestamp from content if present
                turn_time = None
                ts_match = re.search(r"\[?(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}(?::\d{2})?)\]?", content)
                if ts_match:
                    try:
                        turn_time = datetime.strptime(ts_match.group(1), "%Y-%m-%d %H:%M:%S" if len(ts_match.group(1)) > 16 else "%Y-%m-%d %H:%M")
                    except ValueError:
                        pass

                if not turn_time and item_time:
                    try:
                        turn_time = datetime.strptime(item_time, "%Y-%m-%d %H:%M:%S" if len(item_time) > 16 else "%Y-%m-%d %H:%M")
                    except ValueError:
                        pass

                turn_time = turn_time or file_mtime

                # 3. Ingest into TimeMeshin engine
                deltas = self.client.ingest(content, timestamp=turn_time)
                if deltas:
                    ingested_count += len(deltas)
                else:
                    topic = self.classify_topic_rack(content)
                    self.client.ingest_event(
                        timestamp=turn_time,
                        rack=topic,
                        entity=f"Action_{turn_idx}",
                        value=content[:80],
                        reason=content,
                        attribute="note"
                    )
                    ingested_count += 1
                continue
            if False:
                for turn in []:

                    # 1. Noise / Out-of-context Filter Gating
                    if self.is_noise_or_out_of_context(content):
                        filtered_noise_count += 1
                        continue

                    # 2. Extract or approximate timestamp from content if present
                    turn_time = None
                    if isinstance(turn, dict) and turn.get("timestamp"):
                        turn_time = turn.get("timestamp")
                    else:
                        ts_match = re.search(r"\[?(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}(?::\d{2})?)\]?", content)
                        if ts_match:
                            try:
                                turn_time = datetime.strptime(ts_match.group(1), "%Y-%m-%d %H:%M:%S" if len(ts_match.group(1)) > 16 else "%Y-%m-%d %H:%M")
                            except ValueError:
                                pass
                    turn_time = turn_time or file_mtime

                    # 3. Ingest into TimeMeshin engine
                    deltas = self.client.ingest(content, timestamp=turn_time)
                    if deltas:
                        ingested_count += len(deltas)
                    else:
                        topic = self.classify_topic_rack(content)
                        self.client.ingest_event(
                            timestamp=turn_time,
                            rack=topic,
                            entity=f"Event_{turn_idx}",
                            value=content[:80],
                            reason=content,
                            attribute="action"
                        )
                        ingested_count += 1

            self.processed_files.add(file_path.name)
            self._save_processed_history()
            print(f"  [OK] Ingested {ingested_count} state events (Filtered {filtered_noise_count} out-of-context turns).")
            
            # Export updated S x T Matrix for UI visualization
            self.export_spatio_temporal_matrix()
            return ingested_count

        except Exception as e:
            print(f"  [!] Error processing {file_path.name}: {e}")
            import traceback
            traceback.print_exc()
            return 0

    def scan_once(self) -> int:
        """Scans dropzone directory for any new files."""
        total_ingested = 0
        supported_exts = {".html", ".htm", ".pdf", ".md", ".txt", ".json", ".csv"}
        ignored_names = {"matrix_data.json", "matrix_data.js", "spatio_temporal_matrix.html", ".processed_files.json", "cloud_matrix.json", "timeline_memory.db"}
        for item in self.watch_dir.iterdir():
            if item.is_file() and item.suffix.lower() in supported_exts and item.name not in self.processed_files and item.name not in ignored_names:
                total_ingested += self.process_file(item)
        return total_ingested

    def watch_continuous(self, interval_sec: float = 2.0):
        """Continuously watches dropzone folder in real-time."""
        print(f"==========================================================================")
        print(f"   TimeMeshin Dropzone Watcher Active                                     ")
        print(f"   Folder: {self.watch_dir}                                               ")
        print(f"   Supported: .html, .pdf, .md, .txt, .json, .csv                         ")
        print(f"   S x T Matrix Output: {self.matrix_output_path}                          ")
        print(f"==========================================================================")
        print("Waiting for chat documents... (Press Ctrl+C to stop)\n")
        try:
            while True:
                self.scan_once()
                time.sleep(interval_sec)
        except KeyboardInterrupt:
            print("\nStopped watcher daemon.")

    def export_spatio_temporal_matrix(self) -> Dict[str, Any]:
        """
        Generates structured (S x T) Matrix data:
          - Horizontal Axis (T): Chronological timeline intervals / timestamps
          - Vertical Axis (S): Topic swimlanes (Database, Auth, UI, Budget, etc.)
          - Cells: Formatted chat events and active state deltas with noise excluded
        """
        deltas = self.client.storage.load_all_deltas()
        
        # Sort chronologically (T-axis)
        deltas.sort(key=lambda d: d.timestamp)

        # Build unique topic racks (S-axis)
        topics = list(DEFAULT_TOPIC_KEYWORDS.keys()) + ["General & Discussion"]
        
        matrix_events = []
        timestamps = []

        for d in deltas:
            ts_str = d.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            if ts_str not in timestamps:
                timestamps.append(ts_str)

            topic = d.topic_rack
            if topic not in topics:
                topics.append(topic)

            matrix_events.append({
                "id": f"{d.entity_id}_{ts_str}",
                "timestamp": ts_str,
                "topic": topic,
                "entity": d.entity_id,
                "attribute": d.attribute,
                "old_value": str(d.old_value),
                "new_value": str(d.new_value),
                "causal_reason": d.causal_reason,
                "raw_text": d.raw_text,
                "modality": getattr(d, "modality", "COMMITTED")
            })

        matrix_data = {
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "total_events": len(matrix_events),
            "topics": topics,
            "timeline": timestamps,
            "events": matrix_events
        }

        self.matrix_output_path.parent.mkdir(parents=True, exist_ok=True)
        json_str = json.dumps(matrix_data, indent=2)
        self.matrix_output_path.write_text(json_str, encoding="utf-8")
        
        # Also write matrix_data.js for instant zero-CORS browser double-click loading
        js_content = f"window.TIMEMESHIN_LIVE_DATA = {json_str};\n"
        if hasattr(self, "matrix_js_path"):
            self.matrix_js_path.write_text(js_content, encoding="utf-8")
            
        return matrix_data