"""
Case Orchestrator - Coordinates the full escalation lifecycle.

This module ties all agents together and exposes endpoints that
UiPath API Workflows can call to drive the case through stages.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import uuid

from agents.triage.agent import triage_ticket
from agents.context.agent import enrich_case
from agents.resolution.agent import resolve_case
from agents.satisfaction.agent import SatisfactionAgent

app = FastAPI(title="Case Orchestrator", version="1.0.0")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "orchestrator"}

# In-memory case store (in production, Maestro Case handles this)
CASES: dict = {}


class IncomingTicket(BaseModel):
    ticket_id: str
    customer_id: str
    source: str
    subject: str
    body: str
    customer_tier: str = "standard"


class HumanDecision(BaseModel):
    case_id: str
    approved: bool
    modified_response: str | None = None
    notes: str | None = None


@app.post("/cases/intake")
async def intake_case(ticket: IncomingTicket):
    """Stage 1: Intake - Create a new case from an incoming ticket."""
    case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
    case = {
        "case_id": case_id,
        "stage": "intake",
        "status": "open",
        "created_at": datetime.now().isoformat(),
        "ticket": ticket.model_dump(),
        "audit_trail": [
            {"timestamp": datetime.now().isoformat(), "actor": "rpa_intake_bot", "actor_type": "rpa", "action": "case_created"}
        ],
    }
    CASES[case_id] = case
    return {"case_id": case_id, "stage": "intake", "message": "Case created. Ready for triage."}


@app.post("/cases/{case_id}/triage")
async def triage_case(case_id: str):
    """Stage 2: Triage - AI agent classifies and scores the case."""
    if case_id not in CASES:
        raise HTTPException(status_code=404, detail="Case not found")

    case = CASES[case_id]
    ticket = case["ticket"]

    triage_result = triage_ticket(ticket, customer_tier=ticket.get("customer_tier", "standard"))

    case["stage"] = "triage"
    case["triage"] = triage_result
    case["audit_trail"].append({
        "timestamp": datetime.now().isoformat(),
        "actor": "triage_agent",
        "actor_type": "agent",
        "action": "triage_completed",
        "details": triage_result,
    })

    return {"case_id": case_id, "stage": "triage", "triage": triage_result}


@app.post("/cases/{case_id}/enrich")
async def enrich_case_endpoint(case_id: str):
    """Stage 3: Context Enrichment - Pull customer data and history."""
    if case_id not in CASES:
        raise HTTPException(status_code=404, detail="Case not found")

    case = CASES[case_id]
    ticket = case["ticket"]
    triage = case.get("triage", {})

    enrichment_input = {
        "customer_id": ticket["customer_id"],
        "subject": ticket["subject"],
        "body": ticket["body"],
        "category": triage.get("category", "general"),
        "urgency_score": triage.get("urgency_score", 0.5),
    }

    context_brief = enrich_case(enrichment_input)

    case["stage"] = "routing"
    case["context_brief"] = context_brief
    case["audit_trail"].append({
        "timestamp": datetime.now().isoformat(),
        "actor": "context_agent",
        "actor_type": "agent",
        "action": "context_enriched",
    })

    return {"case_id": case_id, "stage": "routing", "context_brief": context_brief}


@app.post("/cases/{case_id}/resolve")
async def resolve_case_endpoint(case_id: str):
    """Stage 4: Resolution - Draft response and recommend actions."""
    if case_id not in CASES:
        raise HTTPException(status_code=404, detail="Case not found")

    case = CASES[case_id]
    ticket = case["ticket"]
    triage = case.get("triage", {})
    context_brief = case.get("context_brief", "No context available.")

    resolution_input = {
        "subject": ticket["subject"],
        "body": ticket["body"],
        "category": triage.get("category", "general"),
        "urgency_score": triage.get("urgency_score", 0.5),
        "sentiment_score": triage.get("sentiment_score", 0.0),
        "intent": triage.get("intent", "unknown"),
        "flags": triage.get("flags", []),
        "customer_tier": ticket.get("customer_tier", "standard"),
    }

    resolution = resolve_case(resolution_input, context_brief)

    case["stage"] = "resolution"
    case["status"] = "awaiting_human" if resolution.get("requires_human_approval") else "resolved"
    case["resolution"] = resolution
    case["audit_trail"].append({
        "timestamp": datetime.now().isoformat(),
        "actor": "resolution_agent",
        "actor_type": "agent",
        "action": "resolution_drafted",
        "details": {"requires_approval": resolution.get("requires_human_approval")},
    })

    return {"case_id": case_id, "stage": "resolution", "status": case["status"], "resolution": resolution}


@app.post("/cases/{case_id}/human-decision")
async def human_decision(case_id: str, decision: HumanDecision):
    """Stage 4b: Human approves or modifies the resolution."""
    if case_id not in CASES:
        raise HTTPException(status_code=404, detail="Case not found")

    case = CASES[case_id]

    if decision.approved:
        if decision.modified_response:
            case["resolution"]["draft_response"] = decision.modified_response
        case["status"] = "resolved"
        case["audit_trail"].append({
            "timestamp": datetime.now().isoformat(),
            "actor": "human_reviewer",
            "actor_type": "human",
            "action": "resolution_approved",
            "details": {"notes": decision.notes},
        })
    else:
        case["status"] = "in_progress"
        case["stage"] = "routing"
        case["audit_trail"].append({
            "timestamp": datetime.now().isoformat(),
            "actor": "human_reviewer",
            "actor_type": "human",
            "action": "resolution_rejected",
            "details": {"notes": decision.notes},
        })

    return {"case_id": case_id, "status": case["status"], "approved": decision.approved}


@app.post("/cases/{case_id}/satisfaction")
async def check_satisfaction(case_id: str):
    """Stage 5: Post-resolution satisfaction analysis."""
    if case_id not in CASES:
        raise HTTPException(status_code=404, detail="Case not found")

    case = CASES[case_id]
    ticket = case["ticket"]
    triage = case.get("triage", {})
    resolution = case.get("resolution", {})

    satisfaction_input = {
        "subject": ticket["subject"],
        "customer_tier": ticket.get("customer_tier", "standard"),
        "urgency_score": triage.get("urgency_score", 0.5),
        "sentiment_score": triage.get("sentiment_score", 0.0),
        "flags": triage.get("flags", []),
    }

    sat_agent = SatisfactionAgent()
    satisfaction_result = await sat_agent.analyze_satisfaction({"case": satisfaction_input, "resolution": resolution})

    case["stage"] = "satisfaction"
    case["satisfaction"] = satisfaction_result
    case["audit_trail"].append({
        "timestamp": datetime.now().isoformat(),
        "actor": "satisfaction_agent",
        "actor_type": "agent",
        "action": "satisfaction_analyzed",
    })

    return {"case_id": case_id, "stage": "satisfaction", "analysis": satisfaction_result}


@app.post("/cases/{case_id}/close")
async def close_case(case_id: str):
    """Close the case."""
    if case_id not in CASES:
        raise HTTPException(status_code=404, detail="Case not found")

    case = CASES[case_id]
    case["stage"] = "closed"
    case["status"] = "closed"
    case["closed_at"] = datetime.now().isoformat()
    case["audit_trail"].append({
        "timestamp": datetime.now().isoformat(),
        "actor": "system",
        "actor_type": "system",
        "action": "case_closed",
    })

    return {"case_id": case_id, "stage": "closed", "status": "closed"}


@app.get("/cases/{case_id}")
async def get_case(case_id: str):
    """Get full case details."""
    if case_id not in CASES:
        raise HTTPException(status_code=404, detail="Case not found")
    return CASES[case_id]


@app.get("/cases")
async def list_cases():
    """List all cases."""
    return list(CASES.values())
