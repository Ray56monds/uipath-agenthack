from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import random

app = FastAPI(title="Mock CRM Service", version="1.0.0")

# Simulated customer database
CUSTOMERS = {
    "CUST-001": {
        "customer_id": "CUST-001",
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "tier": "vip",
        "lifetime_value": 125000,
        "account_age_months": 48,
        "open_cases_count": 0,
        "products": ["Enterprise Suite", "Premium Support"],
        "last_interaction": "2025-05-01",
        "sentiment_history": [0.8, 0.6, 0.3],
        "notes": "Key account. Renewed contract last quarter. Recent complaints about API latency."
    },
    "CUST-002": {
        "customer_id": "CUST-002",
        "name": "Bob Martinez",
        "email": "bob@example.com",
        "tier": "standard",
        "lifetime_value": 8500,
        "account_age_months": 12,
        "open_cases_count": 2,
        "products": ["Starter Plan"],
        "last_interaction": "2025-05-10",
        "sentiment_history": [0.5, 0.4, 0.2],
        "notes": "Has escalated twice in the past month. Considering cancellation."
    },
    "CUST-003": {
        "customer_id": "CUST-003",
        "name": "Carol Chen",
        "email": "carol@example.com",
        "tier": "enterprise",
        "lifetime_value": 450000,
        "account_age_months": 72,
        "open_cases_count": 1,
        "products": ["Enterprise Suite", "Custom Integration", "Dedicated Support"],
        "last_interaction": "2025-05-15",
        "sentiment_history": [0.9, 0.9, 0.7],
        "notes": "Strategic partner. Any issue must be handled with highest priority."
    },
    "CUST-004": {
        "customer_id": "CUST-004",
        "name": "David Park",
        "email": "david@example.com",
        "tier": "premium",
        "lifetime_value": 35000,
        "account_age_months": 24,
        "open_cases_count": 0,
        "products": ["Professional Plan", "Add-on Analytics"],
        "last_interaction": "2025-04-28",
        "sentiment_history": [0.7, 0.8, 0.8],
        "notes": "Happy customer. Potential upsell candidate."
    },
    "CUST-005": {
        "customer_id": "CUST-005",
        "name": "Eva Thompson",
        "email": "eva@example.com",
        "tier": "standard",
        "lifetime_value": 5200,
        "account_age_months": 6,
        "open_cases_count": 3,
        "products": ["Starter Plan"],
        "last_interaction": "2025-05-18",
        "sentiment_history": [0.3, 0.1, -0.2],
        "notes": "High churn risk. Mentioned competitor products in last call. Threatened legal action over billing dispute."
    },
}


class InteractionLog(BaseModel):
    customer_id: str
    interaction_type: str
    summary: str
    timestamp: str | None = None


@app.get("/")
def root():
    return {"service": "Mock CRM", "status": "running", "customers": len(CUSTOMERS)}


@app.get("/health")
def health():
    return {"status": "healthy", "service": "mock_crm"}


@app.get("/customers/{customer_id}")
def get_customer(customer_id: str):
    if customer_id not in CUSTOMERS:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
    return CUSTOMERS[customer_id]


@app.get("/customers/{customer_id}/history")
def get_customer_history(customer_id: str):
    if customer_id not in CUSTOMERS:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    # Generate mock interaction history
    interactions = [
        {
            "date": "2025-05-15",
            "type": "support_call",
            "summary": "Called about billing discrepancy. Issue resolved.",
            "sentiment": 0.6,
        },
        {
            "date": "2025-05-10",
            "type": "email",
            "summary": "Complained about service downtime on May 9th.",
            "sentiment": 0.2,
        },
        {
            "date": "2025-04-28",
            "type": "chat",
            "summary": "Asked about upgrading plan. Interested in premium features.",
            "sentiment": 0.8,
        },
    ]
    return {"customer_id": customer_id, "interactions": interactions}


@app.get("/customers/lookup/email/{email}")
def lookup_by_email(email: str):
    for cust in CUSTOMERS.values():
        if cust["email"] == email:
            return cust
    raise HTTPException(status_code=404, detail=f"No customer found with email {email}")


@app.post("/customers/{customer_id}/interactions")
def log_interaction(customer_id: str, interaction: InteractionLog):
    if customer_id not in CUSTOMERS:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
    return {
        "status": "logged",
        "customer_id": customer_id,
        "interaction_type": interaction.interaction_type,
        "timestamp": interaction.timestamp or datetime.now().isoformat(),
    }
