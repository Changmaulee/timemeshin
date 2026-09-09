"""
Storage and Vector Indexing Substrate for TimeMeshin.
Handles SQLite relational persistence for Keyframes/Deltas and Dense Vector Space for Rationales.
"""

from __future__ import annotations
import sqlite3
import json
import math
import re
from typing import List, Dict, Any, Optional, Tuple, Callable
from .models import StateDelta, SemanticEvent, Keyframe, CausalEdge, Modality


class LightweightEmbedder:
    """
    Fast, zero-external-dependency sparse/dense semantic vectorizer.
    Can be replaced or augmented with any dense neural embedder (e.g. sentence-transformers or Gemini/OpenAI).
    """
    def __init__(self, dim: int = 128):
        self.dim = dim

    def embed(self, text: str) -> List[float]:
        """Produces a deterministic normalized unit vector for semantic similarity."""
        vec = [0.0] * self.dim
        if not text:
            return vec

        # Tokenize and compute character n-grams + word hash projections
        words = re.findall(r'\b\w+\b', text.lower())
        for i, word in enumerate(words):
            # Positional and semantic hash
            h1 = hash(word) % self.dim
            vec[h1] += 1.5
            # Word bigrams
            if i > 0:
                bigram = f"{words[i-1]}_{word}"
                h2 = hash(bigram) % self.dim
                vec[h2] += 2.0

        # Subword character n-grams (3-grams)
        for i in range(len(text) - 2):
            trigram = text[i:i+3].lower()
            h = hash(trigram) % self.dim
            vec[h] += 0.5

        # L2 Normalize
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 1e-9:
            vec = [x / norm for x in vec]
        return vec

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        return sum(a * b for a, b in zip(v1, v2))


class TimeMeshinStorage:
    """
    Persistent SQLite storage and spatio-temporal query manager.
    """

    def __init__(self, db_path: str = ":memory:", embedder: Optional[LightweightEmbedder] = None):
        self.db_path = db_path
        self.embedder = embedder or LightweightEmbedder()
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        with self.conn:
            # 1. Deltas Table (P-Frames)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS deltas (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    entity TEXT NOT NULL,
                    rack TEXT NOT NULL,
                    attribute TEXT NOT NULL,
                    v_old TEXT,
                    v_new TEXT NOT NULL,
                    causal_rationale TEXT,
                    modality TEXT NOT NULL,
                    parent_ids TEXT,
                    metadata TEXT,
                    embedding TEXT
                )
            """)
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_deltas_ts ON deltas(timestamp)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_deltas_entity ON deltas(entity)")

            # 2. Semantic Events Table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS semantic_events (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    raw_text TEXT NOT NULL,
                    rack TEXT NOT NULL,
                    topics TEXT,
                    impact_level TEXT,
                    metadata TEXT,
                    embedding TEXT
                )
            """)
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_events_ts ON semantic_events(timestamp)")

            # 3. Causal Edges Table (Transitive DAG)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS causal_edges (
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    evidence TEXT,
                    discovered_auto INTEGER NOT NULL,
                    PRIMARY KEY (source_id, target_id)
                )
            """)

            # 4. Precomputed Keyframes Table (I-Frames)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS keyframes (
                    timestamp TEXT PRIMARY KEY,
                    state_table TEXT NOT NULL,
                    source_delta_ids TEXT NOT NULL
                )
            """)

    def save_delta(self, delta: StateDelta) -> None:
        if not delta.embedding:
            # Embed the rationale + transition value
            embed_text = f"{delta.entity} {delta.attribute} {delta.v_old}->{delta.v_new} {delta.causal_rationale}"
            delta.embedding = self.embedder.embed(embed_text)

        with self.conn:
            self.conn.execute("""
                INSERT OR REPLACE INTO deltas (
                    id, timestamp, entity, rack, attribute, v_old, v_new, causal_rationale, modality, parent_ids, metadata, embedding
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                delta.id,
                delta.timestamp,
                delta.entity,
                delta.rack,
                delta.attribute,
                delta.v_old,
                delta.v_new,
                delta.causal_rationale,
                delta.modality.value,
                json.dumps(delta.parent_ids),
                json.dumps(delta.metadata),
                json.dumps(delta.embedding)
            ))

    def save_event(self, event: SemanticEvent) -> None:
        if not event.embedding:
            embed_text = f"{event.summary} {event.raw_text} {' '.join(event.topics)}"
            event.embedding = self.embedder.embed(embed_text)

        with self.conn:
            self.conn.execute("""
                INSERT OR REPLACE INTO semantic_events (
                    id, timestamp, summary, raw_text, rack, topics, impact_level, metadata, embedding
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.id,
                event.timestamp,
                event.summary,
                event.raw_text,
                event.rack,
                json.dumps(event.topics),
                event.impact_level,
                json.dumps(event.metadata),
                json.dumps(event.embedding)
            ))

    def save_causal_edge(self, edge: CausalEdge) -> None:
        with self.conn:
            self.conn.execute("""
                INSERT OR REPLACE INTO causal_edges (
                    source_id, target_id, confidence, evidence, discovered_auto
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                edge.source_id,
                edge.target_id,
                edge.confidence,
                edge.evidence,
                1 if edge.discovered_automatically else 0
            ))

    def get_deltas_up_to(self, playhead: str) -> List[StateDelta]:
        """
        Retrieves all deltas up to playhead (Coordinate T Temporal Fence: t <= playhead).
        """
        cur = self.conn.cursor()
        cur.execute("""
            SELECT id, timestamp, entity, rack, attribute, v_old, v_new, causal_rationale, modality, parent_ids, metadata, embedding
            FROM deltas
            WHERE timestamp <= ?
            ORDER BY timestamp ASC
        """, (playhead,))
        
        rows = cur.fetchall()
        deltas = []
        for r in rows:
            deltas.append(StateDelta(
                id=r[0],
                timestamp=r[1],
                entity=r[2],
                rack=r[3],
                attribute=r[4],
                v_old=r[5],
                v_new=r[6],
                causal_rationale=r[7],
                modality=Modality(r[8]),
                parent_ids=json.loads(r[9]) if r[9] else [],
                metadata=json.loads(r[10]) if r[10] else {},
                embedding=json.loads(r[11]) if r[11] else None
            ))
        return deltas

    def get_events_up_to(self, playhead: str) -> List[SemanticEvent]:
        """
        Retrieves all semantic events up to playhead (t <= playhead).
        """
        cur = self.conn.cursor()
        cur.execute("""
            SELECT id, timestamp, summary, raw_text, rack, topics, impact_level, metadata, embedding
            FROM semantic_events
            WHERE timestamp <= ?
            ORDER BY timestamp ASC
        """, (playhead,))
        
        rows = cur.fetchall()
        events = []
        for r in rows:
            events.append(SemanticEvent(
                id=r[0],
                timestamp=r[1],
                summary=r[2],
                raw_text=r[3],
                rack=r[4],
                topics=json.loads(r[5]) if r[5] else [],
                impact_level=r[6],
                metadata=json.loads(r[7]) if r[7] else {},
                embedding=json.loads(r[8]) if r[8] else None
            ))
        return events

    def get_causal_edges(self) -> List[CausalEdge]:
        cur = self.conn.cursor()
        cur.execute("SELECT source_id, target_id, confidence, evidence, discovered_auto FROM causal_edges")
        rows = cur.fetchall()
        return [
            CausalEdge(
                source_id=r[0],
                target_id=r[1],
                confidence=r[2],
                evidence=r[3],
                discovered_automatically=bool(r[4])
            )
            for r in rows
        ]

    def get_timeline_epoch(self, playhead: str) -> str:
        """
        Returns a deterministic epoch hash of all committed/active state deltas up to playhead.
        Used for Optimistic Concurrency Control (OCC) during branch merges.
        """
        cur = self.conn.cursor()
        cur.execute("""
            SELECT COUNT(*), MAX(timestamp), GROUP_CONCAT(id)
            FROM (
                SELECT id, timestamp FROM deltas WHERE timestamp <= ? ORDER BY timestamp ASC, id ASC
            )
        """, (playhead,))
        row = cur.fetchone()
        count = row[0] or 0
        max_ts = row[1] or "empty"
        ids = row[2] or ""
        import hashlib
        epoch_hash = hashlib.sha256(f"{count}:{max_ts}:{ids}".encode("utf-8")).hexdigest()[:16]
        return f"epoch_{count}_{epoch_hash}"

    def fold_keyframe(self, playhead: str) -> Keyframe:
        """
        Folds all P-Frames up to playhead into a single deterministic I-Frame state table.
        """
        deltas = self.get_deltas_up_to(playhead)
        state_table: Dict[str, Dict[str, Any]] = {}
        applied_ids = []

        for d in deltas:
            # We fold COMMITTED (and optionally EVALUATING) mutations
            if d.modality in [Modality.COMMITTED, Modality.EVALUATING, Modality.HYPOTHETICAL]:
                if d.entity not in state_table:
                    state_table[d.entity] = {
                        "_rack": d.rack,
                        "_last_updated": d.timestamp,
                        "_last_modality": d.modality.value
                    }
                state_table[d.entity][d.attribute] = d.v_new
                state_table[d.entity]["_last_updated"] = d.timestamp
                state_table[d.entity]["_last_modality"] = d.modality.value
                applied_ids.append(d.id)

        return Keyframe(
            timestamp=playhead,
            state_table=state_table,
            source_delta_ids=applied_ids
        )
