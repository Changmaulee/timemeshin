# -*- coding: utf-8 -*-
"""
TimeMesh Cloud Service (System One Decision & Causal Memory Gateway)
High-performance async API server built for Cloud Deployment (Cloud Run, AWS ECS, K8s).
"""

import time
import re
from enum import Enum
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
import uvicorn

# ==========================================
# 1. PYDANTIC SCHEMAS (Type-Safe Contracts)
# ==========================================

class TicketCategory(str, Enum):
    BILLING = "billing"
    AUTH_FAILURE = "auth_failure"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    SECURITY_ALERT = "security_alert"
    GENERAL_INQUIRY = "general_inquiry"

class DecisionRequest(BaseModel):
    ticket_id: Optional[str] = Field(default=None, description="Unique ticket/request identifier")
    payload: str = Field(..., description="Unstructured prose or incident description")
    caller_id: Optional[str] = Field(default="system", description="Service or agent identifier")
    persist_to_timeline: bool = Field(default=False, description="If True, promotes decision to P-Frame DAG in background")
    timestamp: Optional[str] = Field(default=None, description="Playhead timestamp (defaults to current time)")

class DecisionResponse(BaseModel):
    op: str = "EVAL_BFRAME_OCC"
    ticket_id: Optional[str]
    category: TicketCategory
    priority: int
    confidence: float
    target_queue: str
    auto_escalate: bool
    server_compute_time_us: float
    persisted: bool

# ==========================================
# 2. CORE DECISION ENGINE
# ==========================================

QUEUES = {
    TicketCategory.BILLING: "finance_triage",
    TicketCategory.AUTH_FAILURE: "secops_l2",
    TicketCategory.PERFORMANCE_DEGRADATION: "infra_sre",
    TicketCategory.SECURITY_ALERT: "incident_commander",
    TicketCategory.GENERAL_INQUIRY: "tier1_support"
}

def evaluate_system_one_decision(text: str) -> Dict[str, Any]:
    """Fast in-memory token scanning & schema evaluation."""
    lower = text.lower()
    if any(k in lower for k in ("sql injection", "breach", "attack", "exploit", "unauthorized access")):
        cat = TicketCategory.SECURITY_ALERT
        priority = 100
        conf = 0.99
        escalate = True
    elif any(k in lower for k in ("latency", "timeout", "504", "502", "slow", "down", "outage")):
        cat = TicketCategory.PERFORMANCE_DEGRADATION
        priority = 85
        conf = 0.96
        escalate = True
    elif any(k in lower for k in ("invoice", "charge", "refund", "credit card", "payment", "billing")):
        cat = TicketCategory.BILLING
        priority = 70
        conf = 0.95
        escalate = False
    elif any(k in lower for k in ("login", "2fa", "password", "jwt", "session", "sso", "auth")):
        cat = TicketCategory.AUTH_FAILURE
        priority = 80
        conf = 0.94
        escalate = False
    else:
        cat = TicketCategory.GENERAL_INQUIRY
        priority = 30
        conf = 0.90
        escalate = False

    return {
        "category": cat,
        "priority": priority,
        "confidence": conf,
        "target_queue": QUEUES[cat],
        "auto_escalate": escalate
    }

# ==========================================
# 3. FASTAPI APP
# ==========================================

app = FastAPI(
    title="TimeMesh Cloud Decision & Causal Gateway",
    version="1.0.0",
    description="High-Throughput Type-Safe Decision Engine with Optional Temporal Causal Persistence."
)

timeline_storage: List[Dict[str, Any]] = []

def async_persist_pframe(data: Dict[str, Any]):
    """Background task to commit state to timeline without blocking decision response."""
    timeline_storage.append(data)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "TimeMesh Cloud", "version": "1.0.0"}

@app.post("/v1/decide", response_model=DecisionResponse)
async def decide(req: DecisionRequest, bg: BackgroundTasks):
    t_start = time.perf_counter_ns()
    
    # 1. Evaluate B-Frame OCC Decision (System One)
    decision = evaluate_system_one_decision(req.payload)
    
    t_end = time.perf_counter_ns()
    compute_us = (t_end - t_start) / 1000.0

    # 2. Optional Non-Blocking Background Causal Commit
    if req.persist_to_timeline:
        bg.add_task(async_persist_pframe, {
            "ticket_id": req.ticket_id,
            "timestamp": req.timestamp or time.strftime("%Y-%m-%d %H:%M:%S"),
            "decision": decision
        })

    return DecisionResponse(
        op="EVAL_BFRAME_OCC",
        ticket_id=req.ticket_id,
        category=decision["category"],
        priority=decision["priority"],
        confidence=decision["confidence"],
        target_queue=decision["target_queue"],
        auto_escalate=decision["auto_escalate"],
        server_compute_time_us=compute_us,
        persisted=req.persist_to_timeline
    )

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
