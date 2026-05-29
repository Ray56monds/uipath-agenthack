from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import uuid
import random

app = FastAPI(title="Mock Ticket Service", version="1.0.0")

# Simulated ticket queue
TICKETS = [
    {
        "ticket_id": "TKT-1001",
        "customer_id": "CUST-001",
        "source": "email",
        "subject": "API response times unacceptable",
        "body": "Our integration has been experiencing 5-10 second response times since last Tuesday. This is impacting our production systems and we need this resolved immediately. We pay for premium support and expect better.",
        "created_at": "2025-05-18T09:30:00Z",
        "status": "new",
    },
    {
        "ticket_id": "TKT-1002",
        "customer_id": "CUST-005",
        "source": "chat",
        "subject": "Billing charge I never authorized",
        "body": "I was charged $499 for a service I never signed up for. I want an immediate refund or I will be contacting my lawyer and filing a dispute with my bank. This is fraud.",
        "created_at": "2025-05-18T10:15:00Z",
        "status": "new",
    },
    {
        "ticket_id": "TKT-1003",
        "customer_id": "CUST-003",
        "source": "portal",
        "subject": "Custom integration failing after your update",
        "body": "After your platform update on May 16th, our custom integration pipeline is throwing 500 errors. This is blocking our entire data team. We need a rollback or fix within the hour.",
        "created_at": "2025-05-18T11:00:00Z",
        "status": "new",
    },
    {
        "ticket_id": "TKT-1004",
        "customer_id": "CUST-004",
        "source": "email",
        "subject": "Question about upgrading to Enterprise",
        "body": "Hi, I'd like to understand the differences between Professional and Enterprise plans. Can someone walk me through the migration process? No rush, just planning for next quarter.",
        "created_at": "2025-05-18T11:30:00Z",
        "status": "new",
    },
    {
        "ticket_id": "TKT-1005",
        "customer_id": "CUST-002",
        "source": "social_media",
        "subject": "@YourCompany your service has been down 3 times this week",
        "body": "@YourCompany I've had enough. Your service has gone down 3 times this week and your support team takes days to respond. Switching to CompetitorX unless someone fixes this TODAY. #frustrated #badservice",
        "created_at": "2025-05-18T12:00:00Z",
        "status": "new",
    },
]


class TicketCreate(BaseModel):
    customer_id: str
    source: str
    subject: str
    body: str


class TicketUpdate(BaseModel):
    status: str | None = None
    assigned_to: str | None = None
    notes: str | None = None


@app.get("/")
def root():
    return {"service": "Mock Ticket Service", "status": "running", "pending_tickets": len([t for t in TICKETS if t["status"] == "new"])}


@app.get("/health")
def health():
    return {"status": "healthy", "service": "mock_tickets"}


@app.get("/tickets/pending")
def get_pending_tickets():
    return [t for t in TICKETS if t["status"] == "new"]


@app.get("/tickets")
def list_tickets(status: str | None = None):
    if status:
        return [t for t in TICKETS if t["status"] == status]
    return TICKETS


@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: str):
    for ticket in TICKETS:
        if ticket["ticket_id"] == ticket_id:
            return ticket
    raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")


@app.get("/tickets/next")
def get_next_ticket():
    new_tickets = [t for t in TICKETS if t["status"] == "new"]
    if not new_tickets:
        raise HTTPException(status_code=404, detail="No new tickets in queue")
    return new_tickets[0]


@app.post("/tickets")
def create_ticket(ticket: TicketCreate):
    new_ticket = {
        "ticket_id": f"TKT-{random.randint(2000, 9999)}",
        "customer_id": ticket.customer_id,
        "source": ticket.source,
        "subject": ticket.subject,
        "body": ticket.body,
        "created_at": datetime.now().isoformat(),
        "status": "new",
    }
    TICKETS.append(new_ticket)
    return new_ticket


@app.patch("/tickets/{ticket_id}")
def update_ticket(ticket_id: str, update: TicketUpdate):
    for ticket in TICKETS:
        if ticket["ticket_id"] == ticket_id:
            if update.status:
                ticket["status"] = update.status
            if update.assigned_to:
                ticket["assigned_to"] = update.assigned_to
            if update.notes:
                ticket["notes"] = update.notes
            return ticket
    raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
