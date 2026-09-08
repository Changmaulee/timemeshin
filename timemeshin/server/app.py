from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from ..client import ChronoMeshClient as TimeMeshinClient

app = FastAPI(
    title="TimeMeshin REST API",
    description="Deterministic Spatio-Temporal (Semantics x Timeline) Video-Scrubber Context Engine for AI Retrieval",
    version="0.1.0"
)

# Global persistent client
client = TimeMeshinClient(db_path="timemeshin_server.db")


class IngestRequest(BaseModel):
    text: str = Field(..., description="Raw text, chat message, or log entry to ingest")
    timestamp: Optional[str] = Field(None, description="ISO timestamp (e.g. 2026-09-02T14:30:00). Defaults to UTC now.")


class QueryRequest(BaseModel):
    question: str = Field(..., description="Natural language question")
    playhead_time: str = Field(..., description="ISO timestamp to lock playhead to (e.g. 2026-09-02T16:00:00)")
    top_k: int = Field(3, description="Number of causal events to return")
    filter_rack: Optional[str] = Field(None, description="Optional topic rack filter")


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "total_deltas": len(client.engine.deltas),
        "total_keyframes": len(client.engine.keyframes),
        "racks": list(client.engine.racks)
    }


@app.post("/api/v1/ingest")
def ingest_text(req: IngestRequest):
    t = None
    if req.timestamp:
        try:
            t = datetime.fromisoformat(req.timestamp.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid ISO timestamp format.")
    
    recorded_deltas = client.ingest(req.text, timestamp=t)
    return {
        "status": "success",
        "recorded_deltas_count": len(recorded_deltas),
        "deltas": recorded_deltas
    }


@app.get("/api/v1/scrub")
def scrub_playhead(
    playhead_time: str = Query(..., description="ISO timestamp to reconstruct state at"),
    rack: Optional[str] = Query(None, description="Optional topic rack filter")
):
    try:
        t = datetime.fromisoformat(playhead_time.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ISO timestamp format.")

    state = client.scrub(playhead=t, filter_rack=rack)
    return {
        "playhead_time": t.isoformat(),
        "state": state
    }


@app.post("/api/v1/query")
def dual_coordinate_query(req: QueryRequest):
    try:
        t = datetime.fromisoformat(req.playhead_time.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ISO timestamp format.")

    res = client.query(
        question=req.question,
        playhead=t,
        top_k=req.top_k,
        filter_rack=req.filter_rack
    )
    return res


@app.get("/api/v1/trace/{entity_id}")
def trace_entity_trajectory(
    entity_id: str,
    up_to_time: Optional[str] = Query(None, description="Optional upper time bound")
):
    t = None
    if up_to_time:
        try:
            t = datetime.fromisoformat(up_to_time.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid ISO timestamp format.")

    trajectory = client.trace(entity_id=entity_id, up_to_time=t)
    return {
        "entity_id": entity_id,
        "trajectory_steps": len(trajectory),
        "trajectory": trajectory
    }
