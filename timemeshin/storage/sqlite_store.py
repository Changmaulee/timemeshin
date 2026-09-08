import io
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np

from ..core.frames import DeltaFrame, Keyframe


class SQLiteStorage:
    """
    Zero-config persistent storage for ChronoMesh.
    Stores I-Frames (Keyframes), P-Frames (Deltas), and vector embeddings in SQLite.
    """
    def __init__(self, db_path: str = "chronomesh.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Deltas table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS deltas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    topic_rack TEXT NOT NULL,
                    attribute TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    causal_reason TEXT,
                    raw_text TEXT,
                    embedding BLOB
                );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_deltas_time ON deltas(timestamp);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_deltas_entity ON deltas(entity_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_deltas_rack ON deltas(topic_rack);")

            # Keyframes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS keyframes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL UNIQUE,
                    state_snapshot TEXT NOT NULL
                );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_keyframes_time ON keyframes(timestamp);")
            conn.commit()

    @staticmethod
    def _adapt_array(arr: Optional[np.ndarray]) -> Optional[bytes]:
        if arr is None:
            return None
        out = io.BytesIO()
        np.save(out, arr)
        out.seek(0)
        return out.read()

    @staticmethod
    def _convert_array(blob: Optional[bytes]) -> Optional[np.ndarray]:
        if blob is None:
            return None
        out = io.BytesIO(blob)
        out.seek(0)
        return np.load(out)

    def save_delta(self, delta: DeltaFrame) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO deltas (
                    timestamp, entity_id, topic_rack, attribute, 
                    old_value, new_value, causal_reason, raw_text, embedding
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                delta.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                delta.entity_id,
                delta.topic_rack,
                delta.attribute,
                json.dumps(delta.old_value),
                json.dumps(delta.new_value),
                delta.causal_reason,
                delta.raw_text,
                self._adapt_array(delta.embedding)
            ))
            conn.commit()

    def save_keyframe(self, keyframe: Keyframe) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO keyframes (timestamp, state_snapshot)
                VALUES (?, ?)
            """, (
                keyframe.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                json.dumps(keyframe.state_snapshot)
            ))
            conn.commit()

    def load_all_deltas(self) -> List[DeltaFrame]:
        deltas = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT timestamp, entity_id, topic_rack, attribute, 
                       old_value, new_value, causal_reason, raw_text, embedding
                FROM deltas ORDER BY timestamp ASC
            """)
            for row in cursor.fetchall():
                t = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
                old_val = json.loads(row[4]) if row[4] else None
                new_val = json.loads(row[5]) if row[5] else None
                emb = self._convert_array(row[8])
                deltas.append(DeltaFrame(
                    timestamp=t,
                    entity_id=row[1],
                    topic_rack=row[2],
                    attribute=row[3],
                    old_value=old_val,
                    new_value=new_val,
                    causal_reason=row[6],
                    raw_text=row[7],
                    embedding=emb
                ))
        return deltas

    def load_all_keyframes(self) -> List[Keyframe]:
        keyframes = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp, state_snapshot FROM keyframes ORDER BY timestamp ASC")
            for row in cursor.fetchall():
                t = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
                state = json.loads(row[1])
                keyframes.append(Keyframe(t, state))
        return keyframes
